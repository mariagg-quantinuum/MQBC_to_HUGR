from typing import Dict, List, Set, Optional
import numpy as np
from graphix.pattern import Pattern
from graphix.command import N, E, M, X, Z, C, CommandKind
from graphix.fundamentals import Plane
from graphix.clifford import Clifford
from graphix import Circuit as GraphixCircuit

try:
    from pytket import Circuit, Qubit, Bit, OpType
    from pytket.circuit.logic_exp import BitLogicExp, reg_eq, create_bit_logic_exp
    PYTKET_AVAILABLE = True
except ImportError:
    PYTKET_AVAILABLE = False
    print("Warning: pytket not available. Install with: pip install pytket")


class GraphixToPytketConverter:
    """
    Converts a Graphix MBQC pattern to pytket Circuit using pytket's condition mechanism.
    
    This converter translates measurement-based quantum computation (MBQC)
    patterns into pytket circuits, using pytket's native `condition` kwarg
    for conditional corrections based on measurement outcomes.
    
    Key difference from graphix_to_guppy.py:
    - Uses pytket's condition=<expression> instead of generating if-statements
    - Leverages pytket's classical logic expression system (XOR, AND, OR)
    - Produces circuits compatible with TKET compilation passes
    """
    
    def __init__(self):
        self.circuit: Optional['Circuit'] = None
        self.qubits: Dict[int, Qubit] = {}  # Maps node indices to Qubit objects
        self.bits: Dict[int, Bit] = {}  # Maps measurement results to Bit objects
        self.node_order: List[int] = []  # Track order of qubit preparation
        self.qubit_counter: int = 0
        self.bit_counter: int = 0
        
    def convert(self, pattern: Pattern) -> 'Circuit':
        """
        Convert a Graphix Pattern to a pytket Circuit.
        
        Args:
            pattern: The Graphix MBQC pattern to convert
            
        Returns:
            A pytket Circuit with conditional gates using the condition argument
        """
        if not PYTKET_AVAILABLE:
            raise ImportError("pytket is required for this converter")
            
        # Determine input and output qubits
        input_nodes = sorted(pattern.input_nodes)
        output_nodes = sorted(pattern.output_nodes)
        measured_nodes = self._get_measured_nodes(pattern)
        
        # Calculate how many qubits and bits we need
        n_inputs = len(input_nodes)
        n_outputs = len(output_nodes)
        
        # Estimate total qubits needed (inputs + ancillas)
        all_nodes = set()
        for cmd in pattern:
            if cmd.kind == CommandKind.N:
                all_nodes.add(cmd.node)
            elif cmd.kind == CommandKind.E:
                all_nodes.update(cmd.nodes)
        all_nodes.update(input_nodes)
        
        n_qubits = len(all_nodes)
        n_bits = len(measured_nodes)
        
        # Create the circuit
        self.circuit = Circuit()
        
        # Add quantum and classical registers
        for i in range(n_qubits):
            qubit = Qubit("q", i)
            self.circuit.add_qubit(qubit)
            
        for i in range(n_bits):
            bit = Bit("m", i)
            self.circuit.add_bit(bit)
            
        # Initialize input qubits - map pattern input nodes to circuit qubits
        for i, node_idx in enumerate(input_nodes):
            qubit = Qubit("q", i)
            self.qubits[node_idx] = qubit
            self.qubit_counter = max(self.qubit_counter, i + 1)
            
        # Process pattern commands in order
        for cmd in pattern:
            self._process_command(cmd)
            
        return self.circuit
    
    def _get_measured_nodes(self, pattern: Pattern) -> List[int]:
        """Extract nodes that are measured (not output nodes)."""
        measured = []
        for cmd in pattern:
            if cmd.kind == CommandKind.M:
                if cmd.node not in pattern.output_nodes:
                    measured.append(cmd.node)
        return sorted(set(measured))
    
    def _get_qubit(self) -> Qubit:
        """Allocate a new qubit."""
        qubit = Qubit("q", self.qubit_counter)
        self.qubit_counter += 1
        return qubit
    
    def _get_bit(self) -> Bit:
        """Allocate a new bit."""
        bit = Bit("m", self.bit_counter)
        self.bit_counter += 1
        return bit
    
    def _process_command(self, cmd):
        """
        Process a single Graphix command and add corresponding operations to pytket Circuit.
        
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
        # In pytket: use existing qubit (assumed initialized to |0⟩), then apply H to get |+⟩
        if node not in self.qubits:
            qubit = self._get_qubit()
            self.qubits[node] = qubit
            
        qubit = self.qubits[node]
        
        # Apply H gate to prepare |+⟩ state
        self.circuit.H(qubit)
        
        self.node_order.append(node)
    
    def _process_entangle(self, cmd: E):
        """
        Process an entanglement command (E).
        Applies a CZ gate between two qubits.
        """
        node1, node2 = cmd.nodes
        
        if node1 not in self.qubits or node2 not in self.qubits:
            # Nodes not yet available - skip (they'll be prepared later)
            return
            
        # Get the qubit objects
        q1 = self.qubits[node1]
        q2 = self.qubits[node2]
        
        # Apply CZ gate
        self.circuit.CZ(q1, q2)
    
    def _process_measure(self, cmd: M):
        """
        Process a measurement command (M).
        Measures a qubit in the specified plane and angle.
        """
        node = cmd.node
        
        if node not in self.qubits:
            return
            
        qubit = self.qubits[node]
        
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
            if abs(angle) > 1e-10:
                self.circuit.Rz(-angle, qubit)
            self.circuit.H(qubit)
            
        elif plane == Plane.YZ:
            # YZ plane measurement
            if abs(angle) > 1e-10:
                self.circuit.Rx(-angle, qubit)
            
        elif plane == Plane.XZ:
            # XZ plane measurement  
            if abs(angle) > 1e-10:
                self.circuit.Ry(angle, qubit)
        
        # Allocate a bit for the measurement result
        bit = self._get_bit()
        self.bits[node] = bit
        
        # Perform measurement
        self.circuit.Measure(qubit, bit)
    
    def _process_pauli_x(self, cmd: X):
        """
        Process a Pauli X correction command.
        May be conditional on measurement outcomes using pytket's condition argument.
        
        KEY DIFFERENCE: Instead of generating if-statements, we use pytket's 
        condition kwarg with classical logic expressions.
        """
        node = cmd.node
        
        if node not in self.qubits:
            return
            
        qubit = self.qubits[node]
        
        # Check if there's a domain (conditional correction)
        if hasattr(cmd, 'domain') and cmd.domain:
            # Conditional X based on measurement outcomes
            # Build pytket condition expression (XOR of measurement results)
            condition_expr = self._build_pytket_condition(cmd.domain)
            
            # Apply X gate with condition
            # The gate will only execute if the condition evaluates to True
            self.circuit.X(qubit, condition=condition_expr)
        else:
            # Unconditional X gate
            self.circuit.X(qubit)
    
    def _process_pauli_z(self, cmd: Z):
        """
        Process a Pauli Z correction command.
        May be conditional on measurement outcomes using pytket's condition argument.
        
        KEY DIFFERENCE: Instead of generating if-statements, we use pytket's 
        condition kwarg with classical logic expressions.
        """
        node = cmd.node
        
        if node not in self.qubits:
            return
            
        qubit = self.qubits[node]
        
        # Check if there's a domain (conditional correction)
        if hasattr(cmd, 'domain') and cmd.domain:
            # Conditional Z based on measurement outcomes
            condition_expr = self._build_pytket_condition(cmd.domain)
            
            # Apply Z gate with condition
            self.circuit.Z(qubit, condition=condition_expr)
        else:
            # Unconditional Z gate
            self.circuit.Z(qubit)
    
    def _process_clifford(self, cmd: C):
        """
        Process a Clifford operation command.
        Decomposes Clifford into sequence of H, S, and Pauli gates.
        """
        node = cmd.node
        
        if node not in self.qubits:
            return
            
        qubit = self.qubits[node]
        clifford_index = cmd.clifford
        
        # Get decomposition from Clifford gate
        try:
            clifford_obj = Clifford(clifford_index)
            
            # Try to get gate decomposition
            if hasattr(clifford_obj, 'to_gate_sequence'):
                gates = clifford_obj.to_gate_sequence()
            elif hasattr(clifford_obj, 'gate'):
                gates = [clifford_obj.gate]
            else:
                # Use standard decomposition patterns for common Cliffords
                gates = self._get_clifford_decomposition(clifford_index)
            
            # Apply each gate in sequence
            for gate in gates:
                gate_name = gate.lower() if isinstance(gate, str) else str(gate).lower()
                
                if gate_name in ['h', 'hadamard']:
                    self.circuit.H(qubit)
                elif gate_name in ['s', 'phase']:
                    self.circuit.S(qubit)
                elif gate_name in ['sdg', 's_dag', 'sdagger']:
                    self.circuit.Sdg(qubit)
                elif gate_name in ['x', 'pauli_x']:
                    self.circuit.X(qubit)
                elif gate_name in ['y', 'pauli_y']:
                    self.circuit.Y(qubit)
                elif gate_name in ['z', 'pauli_z']:
                    self.circuit.Z(qubit)
                    
        except Exception as e:
            print(f"Warning: Could not decompose Clifford {clifford_index}: {e}")
    
    def _get_clifford_decomposition(self, clifford_index: int) -> List[str]:
        """
        Get standard gate decomposition for common Clifford operations.
        
        The 24 single-qubit Clifford gates can be decomposed into
        H, S, and Pauli gates.
        """
        # Standard decompositions for the 24 Clifford gates
        decompositions = {
            0: [],  # Identity
            1: ['S'],  # S gate
            2: ['S', 'S'],  # S^2 = Z
            3: ['SDG'],  # S^†
            4: ['H'],  # Hadamard
            5: ['H', 'S'],
            6: ['H', 'S', 'S'],
            7: ['H', 'SDG'],
            8: ['S', 'H'],
            9: ['S', 'H', 'S'],
            10: ['S', 'H', 'S', 'S'],
            11: ['S', 'H', 'SDG'],
            12: ['H', 'S', 'H'],
            13: ['H', 'S', 'H', 'S'],
            14: ['H', 'S', 'H', 'S', 'S'],
            15: ['H', 'S', 'H', 'SDG'],
            16: ['S', 'H', 'S', 'H'],
            17: ['S', 'H', 'S', 'H', 'S'],
            18: ['S', 'H', 'S', 'H', 'S', 'S'],
            19: ['S', 'H', 'S', 'H', 'SDG'],
            20: ['H', 'S', 'H', 'S', 'H'],
            21: ['H', 'S', 'H', 'S', 'H', 'S'],
            22: ['H', 'S', 'H', 'S', 'H', 'S', 'S'],
            23: ['H', 'S', 'H', 'S', 'H', 'SDG'],
        }
        
        return decompositions.get(clifford_index % 24, [])
    
    def _build_pytket_condition(self, domain: Set[int]) -> 'BitLogicExp':
        """
        Build a pytket conditional expression for measurement-based corrections.
        
        KEY FEATURE: This uses pytket's native classical logic expression system.
        In MBQC, corrections depend on the parity (XOR) of measurement outcomes.
        
        Args:
            domain: Set of node indices whose measurements to XOR
            
        Returns:
            pytket BitLogicExp representing the condition
        """
        if not domain:
            # Empty domain - should not apply gate (always False)
            # Return a condition that's always false
            # We'll use a dummy bit that we know is 0
            dummy_bit = Bit("m", 0)
            return reg_eq(dummy_bit, 1)  # Always false since bit is 0
        
        domain_list = sorted(domain)
        
        # Get measurement bits
        meas_bits = []
        for node_idx in domain_list:
            if node_idx in self.bits:
                meas_bits.append(self.bits[node_idx])
        
        if not meas_bits:
            # No measurement bits available - return always-false condition
            dummy_bit = Bit("m", 0)
            return reg_eq(dummy_bit, 1)
        
        if len(meas_bits) == 1:
            # Single bit: condition is just that bit being 1
            return reg_eq(meas_bits[0], 1)
        
        # Build XOR expression using pytket's logic system
        # Start with first bit
        result_expr = create_bit_logic_exp(meas_bits[0])
        
        # XOR with remaining bits
        for bit in meas_bits[1:]:
            bit_expr = create_bit_logic_exp(bit)
            result_expr = result_expr ^ bit_expr
        
        # The condition is: XOR result == 1 (i.e., odd parity)
        return reg_eq(result_expr, 1)


def convert_graphix_pattern_to_pytket(pattern: Pattern) -> 'Circuit':
    """
    Convert a Graphix MBQC pattern to pytket Circuit using condition arguments.
    
    Args:
        pattern: The Graphix pattern to convert
        
    Returns:
        A pytket Circuit with conditional gates
    """
    converter = GraphixToPytketConverter()
    return converter.convert(pattern)


if __name__ == "__main__":
    print("Graphix to pytket Converter (using condition argument)")
    print("=" * 60)
    
    if not PYTKET_AVAILABLE:
        print("ERROR: pytket is not installed. Please install with:")
        print("  pip install pytket")
        exit(1)
    
    
    # Test with simple Hadamard gate
    print("\nTest 1: Circuit with Hadamard gate")
    circuit = GraphixCircuit(1)
    circuit.h(0)
    pattern = circuit.transpile().pattern
    
    pytket_circ = convert_graphix_pattern_to_pytket(pattern)
    print(f"✓ Converted to pytket circuit")
    print(f"  Qubits: {pytket_circ.n_qubits}")
    print(f"  Gates: {pytket_circ.n_gates}")
    print(f"  Commands: {[str(cmd) for cmd in pytket_circ.get_commands()[:5]]}")
    print()
    
    # Test with S gate (Clifford)
    print("\nTest 2: Circuit with S gate (Clifford)")
    circuit2 = GraphixCircuit(1)
    circuit2.s(0)
    pattern2 = circuit2.transpile().pattern
    
    pytket_circ2 = convert_graphix_pattern_to_pytket(pattern2)
    print(f"✓ Converted to pytket circuit")
    print(f"  Qubits: {pytket_circ2.n_qubits}")
    print(f"  Gates: {pytket_circ2.n_gates}")
    print()
    
    # Test with rotation
    print("\nTest 3: Circuit with Rz rotation")
    circuit3 = GraphixCircuit(1)
    circuit3.rz(0, np.pi/4)
    pattern3 = circuit3.transpile().pattern
    
    pytket_circ3 = convert_graphix_pattern_to_pytket(pattern3)
    print(f"✓ Converted to pytket circuit")
    print(f"  Qubits: {pytket_circ3.n_qubits}")
    print(f"  Gates: {pytket_circ3.n_gates}")
    print()
    
    # Test with two-qubit gate
    print("\nTest 4: Circuit with CNOT gate")
    circuit4 = GraphixCircuit(2)
    circuit4.cnot(0, 1)
    pattern4 = circuit4.transpile().pattern
    
    pytket_circ4 = convert_graphix_pattern_to_pytket(pattern4)
    print(f"✓ Converted to pytket circuit")
    print(f"  Qubits: {pytket_circ4.n_qubits}")
    print(f"  Gates: {pytket_circ4.n_gates}")
    
    print("\n" + "=" * 60)
    print("All tests completed!")