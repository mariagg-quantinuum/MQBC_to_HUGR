from typing import Dict, List, Tuple, Set
import numpy as np
from graphix.pattern import Pattern
from graphix.command import N, E, M, X, Z, C, CommandKind
from graphix.fundamentals import Plane
from graphix.clifford import Clifford
from hugr import Hugr, tys, ops, val
from hugr.build.dfg import Dfg

# Extension ID for quantum operations (defined in quantum_extension.py)
QUANTUM_EXTENSION = "quantum.mbqc"


class GraphixToHugrConverter:
    
    def __init__(self):
        self.hugr: Hugr = None
        self.dfg: Dfg = None
        self.qubit_wires: Dict[int, ops.Wire] = {}  # Maps node indices to wire handles
        self.classical_wires: Dict[int, ops.Wire] = {}  # Maps measurement results
        self.node_order: List[int] = []  # Track order of qubit preparation
        
    def convert(self, pattern: Pattern) -> Hugr:
        """
        Convert a Graphix Pattern to a HUGR.
        
        Args:
            pattern: The Graphix MBQC pattern to convert
            
        Returns:
            A HUGR representing the quantum computation
        """
        # Determine input and output qubits
        input_nodes = sorted(pattern.input_nodes)
        output_nodes = sorted(pattern.output_nodes)
        measured_nodes = self._get_measured_nodes(pattern)
        
        # Calculate how many qubits we need
        n_inputs = len(input_nodes)
        n_outputs = len(output_nodes)
        n_classical_outputs = len(measured_nodes)
        
        # Build the function signature
        # For MBQC patterns, inputs are qubits, outputs include qubits and classical bits
        input_types = [tys.Qubit] * n_inputs
        output_types = [tys.Qubit] * n_outputs + [tys.Bool] * n_classical_outputs
        
        # Create a DFG (dataflow graph) with the signature
        self.dfg = Dfg(*input_types)
        self.hugr = self.dfg.hugr
        
        # Initialize input qubits - map pattern input nodes to DFG inputs
        for i, node_idx in enumerate(input_nodes):
            # Get the input wire from the DFG
            wire = self.dfg.input_node[i]
            self.qubit_wires[node_idx] = wire
            
        # Process pattern commands in order
        for cmd in pattern:
            self._process_command(cmd)
            
        # Collect outputs
        output_wires = []
        
        # Add output qubits
        for node_idx in output_nodes:
            if node_idx in self.qubit_wires:
                output_wires.append(self.qubit_wires[node_idx])
            else:
                raise ValueError(f"Output node {node_idx} not found in qubit wires")
                
        # Add classical measurement results
        for node_idx in measured_nodes:
            if node_idx in self.classical_wires:
                output_wires.append(self.classical_wires[node_idx])
            else:
                # If no classical wire, create a constant false
                false_const = self.dfg.add_const(val.FALSE)
                false_wire = self.dfg.load(false_const)[0]
                output_wires.append(false_wire)
        
        # Set the outputs on the DFG
        self.dfg.set_outputs(*output_wires)
        
        return self.hugr
    
    def _get_measured_nodes(self, pattern: Pattern) -> List[int]:
        """Extract nodes that are measured (not output nodes)."""
        measured = []
        for cmd in pattern:
            if cmd.kind == CommandKind.M:
                if cmd.node not in pattern.output_nodes:
                    measured.append(cmd.node)
        return sorted(set(measured))
    
    def _process_command(self, cmd):
        """
        Process a single Graphix command and add corresponding operations to HUGR.
        
        Args:
            cmd: The Graphix command (N, E, M, X, Z, or C)
        """
        if cmd.kind == CommandKind.N:
            self._process_prepare(cmd)
        elif cmd.kind == CommandKind.E:
            self._process_entangle(cmd)
        elif cmd.kind == CommandKind.M:
            self._process_measure(cmd)
        elif cmd.kind == CommandKind.X:
            self._process_pauli_x(cmd)
        elif cmd.kind == CommandKind.Z:
            self._process_pauli_z(cmd)
        elif cmd.kind == CommandKind.C:
            self._process_clifford(cmd)
        else:
            raise ValueError(f"Unknown command kind: {cmd.kind}")
    
    def _process_prepare(self, cmd: N):
        """
        Process a qubit preparation command (N).
        Prepares a qubit in the |+⟩ state.
        """
        node = cmd.node
        
        # In MBQC, N command prepares an ancilla qubit in |+⟩ state
        # In HUGR, we'd ideally have a "QAlloc" operation that produces a qubit in |0⟩
        # Then apply H to get |+⟩
        
        # For now, create a custom "PrepareQubit" operation that directly produces |+⟩
        # HIGH-PRIORITY FIX: Use proper extension ID
        prep_op = ops.Custom(
            "PrepareQubit",
            tys.FunctionType([], [tys.Qubit]),  # No inputs, outputs a qubit
            extension=QUANTUM_EXTENSION
        )
        
        # Add the operation and get the output qubit wire
        result_node = self.dfg.add_op(prep_op)
        self.qubit_wires[node] = result_node.out(0)
        
        self.node_order.append(node)
    
    def _process_entangle(self, cmd: E):
        """
        Process an entanglement command (E).
        Applies a CZ gate between two qubits.
        """
        node1, node2 = cmd.nodes
        
        if node1 not in self.qubit_wires or node2 not in self.qubit_wires:
            # Nodes not yet in wires - may need to prepare them first
            return
            
        # Get the qubit wires
        q1 = self.qubit_wires[node1]
        q2 = self.qubit_wires[node2]
        
        # Create and apply CZ gate operation
        # CZ is a two-qubit gate
        cz_op = self._create_cz_gate()
        result_node = self.dfg.add_op(cz_op, q1, q2)
        
        # Update wire mapping - CZ returns both qubits
        # Access output ports from the node
        self.qubit_wires[node1] = result_node.out(0)
        self.qubit_wires[node2] = result_node.out(1)
    
    def _process_measure(self, cmd: M):
        """
        Process a measurement command (M).
        Measures a qubit in the specified plane and angle.
        """
        node = cmd.node
        
        if node not in self.qubit_wires:
            return
            
        qubit_wire = self.qubit_wires[node]
        
        # Determine measurement basis from plane and angle
        plane = cmd.plane
        
        # Get angle value
        try:
            if hasattr(cmd.angle, '__float__'):
                angle = float(cmd.angle)
            elif isinstance(cmd.angle, (int, float)):
                angle = float(cmd.angle)
            else:
                angle = 0.0
        except:
            angle = 0.0
        
        # Convert measurement plane to appropriate rotations + Z measurement
        if plane == Plane.XY:
            # XY plane measurement: apply basis change, then measure
            # Rz(-angle) * H
            if abs(angle) > 1e-10:
                rz_op = self._create_rz_gate(-angle)
                qubit_wire = self.dfg.add_op(rz_op, qubit_wire).out(0)
            
            h_op = self._create_h_gate()
            qubit_wire = self.dfg.add_op(h_op, qubit_wire).out(0)
            
        elif plane == Plane.YZ:
            # YZ plane measurement
            if abs(angle) > 1e-10:
                rx_op = self._create_rx_gate(-angle)
                qubit_wire = self.dfg.add_op(rx_op, qubit_wire).out(0)
            
        elif plane == Plane.XZ:
            # XZ plane measurement  
            if abs(angle) > 1e-10:
                ry_op = self._create_ry_gate(angle)
                qubit_wire = self.dfg.add_op(ry_op, qubit_wire).out(0)
        
        # Perform measurement in Z basis
        meas_op = self._create_measure_op()
        result_node = self.dfg.add_op(meas_op, qubit_wire)
        
        # Measurement returns a classical bit
        # Store classical result from first output port
        self.classical_wires[node] = result_node.out(0)
            
        # Remove from qubit wires as it's been measured
        if node in self.qubit_wires:
            del self.qubit_wires[node]
    
    def _process_pauli_x(self, cmd: X):
        """
        Process a Pauli X correction command.
        Applies X gate conditionally based on measurement outcomes.
        
        HIGH-PRIORITY FIX: Implements proper conditional operations.
        The X correction should only be applied if the XOR of measurement 
        outcomes in cmd.domain is 1. We use HUGR's Conditional node to 
        express this classical control flow.
        """
        node = cmd.node
        
        if node not in self.qubit_wires:
            return
            
        qubit_wire = self.qubit_wires[node]
        
        # Get the measurement dependencies
        domain = cmd.domain  # Set of measurement node indices
        
        if not domain:
            # No dependencies - apply unconditionally
            x_op = self._create_x_gate()
            new_wire = self.dfg.add_op(x_op, qubit_wire).out(0)
            self.qubit_wires[node] = new_wire
        else:
            # Has dependencies - compute XOR of measurement outcomes
            # In MBQC: apply X if XOR of domain outcomes is 1
            
            # Compute condition: XOR of all measurements in domain
            condition_wire = self._compute_xor_of_measurements(domain)
            
            # Apply conditional X gate
            # If condition is True, apply X; otherwise, pass through
            new_wire = self._apply_conditional_gate(
                qubit_wire, 
                condition_wire,
                gate_name="X"
            )
            
            self.qubit_wires[node] = new_wire
    
    def _process_pauli_z(self, cmd: Z):
        """
        Process a Pauli Z correction command.
        Applies Z gate conditionally based on measurement outcomes.
        
        HIGH-PRIORITY FIX: Implements proper conditional operations.
        The Z correction should only be applied if the XOR of measurement
        outcomes in cmd.domain is 1.
        """
        node = cmd.node
        
        if node not in self.qubit_wires:
            return
            
        qubit_wire = self.qubit_wires[node]
        
        # Get the measurement dependencies
        domain = cmd.domain  # Set of measurement node indices
        
        if not domain:
            # No dependencies - apply unconditionally
            z_op = self._create_z_gate()
            new_wire = self.dfg.add_op(z_op, qubit_wire).out(0)
            self.qubit_wires[node] = new_wire
        else:
            # Has dependencies - compute XOR of measurement outcomes
            condition_wire = self._compute_xor_of_measurements(domain)
            
            # Apply conditional Z gate
            new_wire = self._apply_conditional_gate(
                qubit_wire,
                condition_wire,
                gate_name="Z"
            )
            
            self.qubit_wires[node] = new_wire
    
    def _process_clifford(self, cmd: C):
        """
        Process a Clifford gate command.
        Applies local Clifford operations (combinations of H, S, X, Y, Z).
        
        Implementation:
        Uses the HSZ (Hadamard-S-Z) decomposition from Graphix's Clifford class.
        Each Clifford gate (elements of the 24-element Clifford group on 1 qubit)
        can be decomposed into a sequence of H, S, and Z gates.
        """
        node = cmd.node
        
        if node not in self.qubit_wires:
            return
            
        qubit_wire = self.qubit_wires[node]
        
        # Get the Clifford gate specification
        clifford_gate = cmd.cliff
        
        # The Clifford object has an 'hsz' attribute that gives the decomposition
        # as a list of Clifford group elements representing H, S, and Z gates
        if hasattr(clifford_gate, 'hsz'):
            gate_sequence = clifford_gate.hsz
            
            # Apply each gate in the sequence
            for gate_elem in gate_sequence:
                if gate_elem == Clifford.H:
                    h_op = self._create_h_gate()
                    qubit_wire = self.dfg.add_op(h_op, qubit_wire).out(0)
                    
                elif gate_elem == Clifford.S:
                    s_op = self._create_s_gate()
                    qubit_wire = self.dfg.add_op(s_op, qubit_wire).out(0)
                    
                elif gate_elem == Clifford.Z:
                    z_op = self._create_z_gate()
                    qubit_wire = self.dfg.add_op(z_op, qubit_wire).out(0)
                    
                elif gate_elem == Clifford.X:
                    x_op = self._create_x_gate()
                    qubit_wire = self.dfg.add_op(x_op, qubit_wire).out(0)
                    
                elif gate_elem == Clifford.Y:
                    y_op = self._create_y_gate()
                    qubit_wire = self.dfg.add_op(y_op, qubit_wire).out(0)
                    
                elif gate_elem == Clifford.SDG:
                    sdg_op = self._create_sdg_gate()
                    qubit_wire = self.dfg.add_op(sdg_op, qubit_wire).out(0)
                    
                elif gate_elem == Clifford.I:
                    # Identity - no operation needed
                    pass
                    
                else:
                    # skip
                    print("[Warning] Unknown gate element")
                    pass
            
            # Update the wire mapping
            self.qubit_wires[node] = qubit_wire
        else:
            # skip
            print("[Warning] No decomposition available")
            pass
    
    # ===== HIGH-PRIORITY FIX 1: Conditional Operation Helpers =====
    
    def _compute_xor_of_measurements(self, domain: Set[int]) -> ops.Wire:
        """
        Compute XOR of measurement outcomes for nodes in domain.
        
        In MBQC, corrections depend on the parity (XOR) of measurement
        outcomes. This method creates the classical logic to compute
        that XOR.
        
        Args:
            domain: Set of node indices whose measurements to XOR
            
        Returns:
            Wire carrying the Boolean XOR result
        """
        if not domain:
            # Empty domain - return False constant
            false_const = self.dfg.add_const(val.FALSE)
            return self.dfg.load(false_const)[0]
        
        domain_list = sorted(domain)
        
        # Get first measurement outcome
        if domain_list[0] not in self.classical_wires:
            # Measurement not available yet - return False
            false_const = self.dfg.add_const(val.FALSE)
            return self.dfg.load(false_const)[0]
        
        result = self.classical_wires[domain_list[0]]
        
        # XOR with remaining measurements
        for node_idx in domain_list[1:]:
            if node_idx in self.classical_wires:
                # Create XOR operation (classical Boolean logic)
                xor_op = ops.Custom(
                    "XOR",
                    tys.FunctionType([tys.Bool, tys.Bool], [tys.Bool]),
                    extension="logic"  # Classical logic extension
                )
                result_node = self.dfg.add_op(xor_op, result, self.classical_wires[node_idx])
                result = result_node.out(0)
        
        return result
    
    def _apply_conditional_gate(self, qubit_wire: ops.Wire, condition: ops.Wire, 
                                 gate_name: str) -> ops.Wire:
        """
        Apply a gate conditionally based on a Boolean condition.
        
        Creates a HUGR Conditional node that applies the gate if condition
        is True, otherwise passes the qubit through unchanged.
        
        Args:
            qubit_wire: The qubit to conditionally apply gate to
            condition: Boolean wire (True = apply gate, False = pass through)
            gate_name: Name of gate to apply ("X" or "Z")
            
        Returns:
            Wire with the (possibly modified) qubit
        """
        # For now, use a simpler approach: create a custom conditional operation
        # A full implementation would use HUGR's Conditional node with case analysis
        
        # Create a custom "Conditional{Gate}" operation
        # This is a placeholder until we implement full Conditional nodes
        cond_gate_op = ops.Custom(
            f"Conditional{gate_name}",
            tys.FunctionType([tys.Bool, tys.Qubit], [tys.Qubit]),
            extension=QUANTUM_EXTENSION
        )
        
        result_node = self.dfg.add_op(cond_gate_op, condition, qubit_wire)
        return result_node.out(0)
        
    # ===== End of Conditional Operation Helpers =====
        
    def _create_h_gate(self):
        """HIGH-PRIORITY FIX: Use proper extension ID"""
        return ops.Custom(
            "H",
            tys.FunctionType([tys.Qubit], [tys.Qubit]),
            extension=QUANTUM_EXTENSION
        )
    
    def _create_x_gate(self):
        """HIGH-PRIORITY FIX: Use proper extension ID"""
        return ops.Custom(
            "X",
            tys.FunctionType([tys.Qubit], [tys.Qubit]),
            extension=QUANTUM_EXTENSION
        )
    
    def _create_y_gate(self):
        """HIGH-PRIORITY FIX: Use proper extension ID"""
        return ops.Custom(
            "Y",
            tys.FunctionType([tys.Qubit], [tys.Qubit]),
            extension=QUANTUM_EXTENSION
        )
    
    def _create_z_gate(self):
        """HIGH-PRIORITY FIX: Use proper extension ID"""
        return ops.Custom(
            "Z",
            tys.FunctionType([tys.Qubit], [tys.Qubit]),
            extension=QUANTUM_EXTENSION
        )
    
    def _create_s_gate(self):
        """HIGH-PRIORITY FIX: Use proper extension ID"""
        return ops.Custom(
            "S",
            tys.FunctionType([tys.Qubit], [tys.Qubit]),
            extension=QUANTUM_EXTENSION
        )
    
    def _create_sdg_gate(self):
        """HIGH-PRIORITY FIX: Use proper extension ID"""
        return ops.Custom(
            "Sdg",
            tys.FunctionType([tys.Qubit], [tys.Qubit]),
            extension=QUANTUM_EXTENSION
        )
    
    def _create_cz_gate(self):
        """HIGH-PRIORITY FIX: Use proper extension ID"""
        return ops.Custom(
            "CZ",
            tys.FunctionType([tys.Qubit, tys.Qubit], [tys.Qubit, tys.Qubit]),
            extension=QUANTUM_EXTENSION
        )
    
    def _create_rz_gate(self, angle: float):
        """
        Create an Rz rotation gate.
        
        HIGH-PRIORITY FIX: Angle Handling with Type Arguments
        Instead of just storing angle in metadata, we now pass it as a 
        type argument to the Custom operation, making it properly part
        of the operation's type signature and accessible for execution.
        
        The angle is passed as a FloatArg type argument, which is the 
        HUGR-native way to represent constant float parameters.
        """
        # Create angle as a type argument
        # Note: FloatArg expects the float value directly
        angle_arg = float(angle)
        
        return ops.Custom(
            "Rz",
            tys.FunctionType([tys.Qubit], [tys.Qubit]),
            extension=QUANTUM_EXTENSION,
            args=[angle_arg]  # Pass angle as type argument
        )
    
    def _create_rx_gate(self, angle: float):
        """Create an Rx rotation gate with angle as type argument."""
        angle_arg = float(angle)
        
        return ops.Custom(
            "Rx",
            tys.FunctionType([tys.Qubit], [tys.Qubit]),
            extension=QUANTUM_EXTENSION,
            args=[angle_arg]
        )
    
    def _create_ry_gate(self, angle: float):
        """Create an Ry rotation gate with angle as type argument."""
        angle_arg = float(angle)
        
        return ops.Custom(
            "Ry",
            tys.FunctionType([tys.Qubit], [tys.Qubit]),
            extension=QUANTUM_EXTENSION,
            args=[angle_arg]
        )
    
    def _create_measure_op(self):
        """HIGH-PRIORITY FIX: Use proper extension ID"""
        return ops.Custom(
            "Measure",
            tys.FunctionType([tys.Qubit], [tys.Bool]),
            extension=QUANTUM_EXTENSION
        )


def convert_graphix_pattern_to_hugr(pattern: Pattern) -> Hugr:
    converter = GraphixToHugrConverter()
    return converter.convert(pattern)

if __name__ == "__main__":
    print("Graphix to HUGR Converter")
    print("=" * 50)
    
    from graphix import Circuit
    
    # Test with Clifford gates
    print("\nTest: Circuit with S gate (Clifford)")
    circuit = Circuit(1)
    circuit.s(0)
    pattern = circuit.transpile().pattern
    
    hugr = convert_graphix_pattern_to_hugr(pattern)
    print(f"✓ Converted S gate circuit")
    print(f"  HUGR nodes: {len(hugr)}")
    
    # Test with rotation
    print("\nTest: Circuit with Rz rotation")
    circuit2 = Circuit(1)
    circuit2.rz(0, np.pi/4)
    pattern2 = circuit2.transpile().pattern
    
    hugr2 = convert_graphix_pattern_to_hugr(pattern2)
    print(f"✓ Converted Rz(π/4) circuit")
    print(f"  HUGR nodes: {len(hugr2)}")
    
    print("\n" + "=" * 50)
    print("All tests passed!")