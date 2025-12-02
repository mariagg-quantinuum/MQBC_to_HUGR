from typing import Dict, List, Set, Optional
import numpy as np
from graphix.pattern import Pattern
from graphix.command import N, E, M, X, Z, C, CommandKind
from graphix.fundamentals import Plane
from graphix.clifford import Clifford

# Guppy imports for code generation
try:
    from guppy import guppy
    from guppy.module import GuppyModule
    GUPPY_AVAILABLE = True
except ImportError:
    GUPPY_AVAILABLE = False
    # Fallback: generate code as strings without executing


class GraphixToGuppyConverter:
    """
    Converts a Graphix MBQC pattern to Guppy quantum code.
    
    This converter translates measurement-based quantum computation (MBQC)
    patterns into imperative Guppy quantum programs. It can generate either:
    1. String code representation (always available)
    2. Actual Guppy module with compiled function (if guppy is installed)
    """
    
    def __init__(self, use_guppy_module: bool = False):
        self.qubit_vars: Dict[int, str] = {}  # Maps node indices to qubit variable names
        self.classical_vars: Dict[int, str] = {}  # Maps measurement results to classical vars
        self.node_order: List[int] = []  # Track order of qubit preparation
        self.code_lines: List[str] = []  # Generated Guppy code
        self.indent_level: int = 1  # Current indentation level
        self.var_counter: int = 0  # Counter for generating unique variable names
        self.use_guppy_module: bool = use_guppy_module and GUPPY_AVAILABLE
        self.guppy_module: Optional['GuppyModule'] = None
        
        if self.use_guppy_module:
            self.guppy_module = GuppyModule("quantum_circuit")
            # Import quantum operations
            self.guppy_module.load_all()
        
    def convert(self, pattern: Pattern, compile_module: bool = False):
        """
        Convert a Graphix Pattern to Guppy quantum code.
        
        Args:
            pattern: The Graphix MBQC pattern to convert
            compile_module: If True and Guppy is available, compile and return GuppyModule
            
        Returns:
            If compile_module is True and Guppy is available: GuppyModule
            Otherwise: A string containing the Guppy function definition
        """
        # Determine input and output qubits
        input_nodes = sorted(pattern.input_nodes)
        output_nodes = sorted(pattern.output_nodes)
        measured_nodes = self._get_measured_nodes(pattern)
        
        # Calculate how many qubits we need
        n_inputs = len(input_nodes)
        n_outputs = len(output_nodes)
        n_classical_outputs = len(measured_nodes)
        
        # Start building the Guppy function
        self._start_function(n_inputs, n_outputs, n_classical_outputs)
        
        # Initialize input qubits - map pattern input nodes to function parameters
        for i, node_idx in enumerate(input_nodes):
            var_name = f"q_in_{i}"
            self.qubit_vars[node_idx] = var_name
            
        # Process pattern commands in order
        for cmd in pattern:
            self._process_command(cmd)
            
        # Build return statement
        self._build_return_statement(output_nodes, measured_nodes)
        
        # Close the function
        self._end_function()
        
        code_str = "\n".join(self.code_lines)
        
        # If compiling to Guppy module, execute the code
        if compile_module and GUPPY_AVAILABLE:
            try:
                # Create a new module and execute the generated code
                module = GuppyModule("quantum_circuit")
                exec(code_str, {"guppy": guppy, "GuppyModule": GuppyModule, 
                                "qubit": None, "measure": None, "h": None, 
                                "x": None, "y": None, "z": None, 
                                "s": None, "sdg": None, "rx": None, 
                                "ry": None, "rz": None, "cz": None})
                module.compile()
                return module
            except Exception as e:
                print(f"Warning: Could not compile Guppy module: {e}")
                return code_str
        
        return code_str
    
    def _get_measured_nodes(self, pattern: Pattern) -> List[int]:
        """Extract nodes that are measured (not output nodes)."""
        measured = []
        for cmd in pattern:
            if cmd.kind == CommandKind.M:
                if cmd.node not in pattern.output_nodes:
                    measured.append(cmd.node)
        return sorted(set(measured))
    
    def _start_function(self, n_inputs: int, n_outputs: int, n_classical: int):
        """Generate the Guppy function signature with proper imports."""
        # Add Guppy imports at the top of the generated code
        if not self.code_lines:  # Only add imports once
            self.code_lines.append("from guppy import guppy")
            self.code_lines.append("from guppy.prelude.quantum import qubit, measure, h, x, y, z, s, sdg, rx, ry, rz, cz")
            self.code_lines.append("")
        
        self.code_lines.append("@guppy")
        
        # Build parameter list
        params = [f"q_in_{i}: qubit" for i in range(n_inputs)]
        param_str = ", ".join(params) if params else ""
        
        # Build return type
        return_types = ["qubit"] * n_outputs + ["bool"] * n_classical
        if len(return_types) == 0:
            return_type = "None"
        elif len(return_types) == 1:
            return_type = return_types[0]
        else:
            return_type = f"tuple[{', '.join(return_types)}]"
        
        self.code_lines.append(f"def quantum_circuit({param_str}) -> {return_type}:")

    
    def _end_function(self):
        """Close the function definition."""
        if not any(line.strip().startswith("return") for line in self.code_lines):
            self._add_line("return None")
    
    def _add_line(self, line: str):
        """Add a line of code with proper indentation."""
        indent = "    " * self.indent_level
        self.code_lines.append(f"{indent}{line}")
    
    def _get_unique_var(self, prefix: str = "v") -> str:
        """Generate a unique variable name."""
        var_name = f"{prefix}_{self.var_counter}"
        self.var_counter += 1
        return var_name
    
    def _process_command(self, cmd):
        """
        Process a single Graphix command and generate corresponding Guppy code.
        
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
        # In Guppy: allocate qubit in |0⟩, then apply H to get |+⟩
        var_name = self._get_unique_var("q")
        
        self._add_line(f"{var_name} = qubit()  # Allocate qubit in |0⟩")
        self._add_line(f"{var_name} = h({var_name})  # Prepare |+⟩ state")
        
        self.qubit_vars[node] = var_name
        self.node_order.append(node)
    
    def _process_entangle(self, cmd: E):
        """
        Process an entanglement command (E).
        Applies a CZ gate between two qubits.
        """
        node1, node2 = cmd.nodes
        
        if node1 not in self.qubit_vars or node2 not in self.qubit_vars:
            # Nodes not yet available - skip (they'll be prepared later)
            return
            
        # Get the qubit variable names
        q1 = self.qubit_vars[node1]
        q2 = self.qubit_vars[node2]
        
        # Apply CZ gate
        self._add_line(f"{q1}, {q2} = cz({q1}, {q2})")
    
    def _process_measure(self, cmd: M):
        """
        Process a measurement command (M).
        Measures a qubit in the specified plane and angle.
        """
        node = cmd.node
        
        if node not in self.qubit_vars:
            return
            
        qubit_var = self.qubit_vars[node]
        
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
                self._add_line(f"{qubit_var} = rz({qubit_var}, {-angle})")
            self._add_line(f"{qubit_var} = h({qubit_var})")
            
        elif plane == Plane.YZ:
            # YZ plane measurement
            if abs(angle) > 1e-10:
                self._add_line(f"{qubit_var} = rx({qubit_var}, {-angle})")
            
        elif plane == Plane.XZ:
            # XZ plane measurement  
            if abs(angle) > 1e-10:
                self._add_line(f"{qubit_var} = ry({qubit_var}, {angle})")
        
        # Perform measurement
        result_var = self._get_unique_var("m")
        self._add_line(f"{result_var} = measure({qubit_var})")
        
        # Store classical result
        self.classical_vars[node] = result_var
        
        # Remove from qubit variables as it's been measured
        del self.qubit_vars[node]
    
    def _process_pauli_x(self, cmd: X):
        """
        Process a Pauli X correction command.
        May be conditional on measurement outcomes.
        """
        node = cmd.node
        
        if node not in self.qubit_vars:
            return
            
        qubit_var = self.qubit_vars[node]
        
        # Check if there's a domain (conditional correction)
        if hasattr(cmd, 'domain') and cmd.domain:
            # Conditional X based on measurement outcomes
            condition_expr = self._build_condition_expression(cmd.domain)
            self._add_line(f"if {condition_expr}:")
            self.indent_level += 1
            self._add_line(f"{qubit_var} = x({qubit_var})")
            self.indent_level -= 1
        else:
            # Unconditional X gate
            self._add_line(f"{qubit_var} = x({qubit_var})")
    
    def _process_pauli_z(self, cmd: Z):
        """
        Process a Pauli Z correction command.
        May be conditional on measurement outcomes.
        """
        node = cmd.node
        
        if node not in self.qubit_vars:
            return
            
        qubit_var = self.qubit_vars[node]
        
        # Check if there's a domain (conditional correction)
        if hasattr(cmd, 'domain') and cmd.domain:
            # Conditional Z based on measurement outcomes
            condition_expr = self._build_condition_expression(cmd.domain)
            self._add_line(f"if {condition_expr}:")
            self.indent_level += 1
            self._add_line(f"{qubit_var} = z({qubit_var})")
            self.indent_level -= 1
        else:
            # Unconditional Z gate
            self._add_line(f"{qubit_var} = z({qubit_var})")
    
    def _process_clifford(self, cmd: C):
        """
        Process a Clifford operation command.
        Decomposes Clifford into sequence of H, S, and Pauli gates.
        """
        node = cmd.node
        
        if node not in self.qubit_vars:
            return
            
        qubit_var = self.qubit_vars[node]
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
                    self._add_line(f"{qubit_var} = h({qubit_var})")
                elif gate_name in ['s', 'phase']:
                    self._add_line(f"{qubit_var} = s({qubit_var})")
                elif gate_name in ['sdg', 's_dag', 'sdagger']:
                    self._add_line(f"{qubit_var} = sdg({qubit_var})")
                elif gate_name in ['x', 'pauli_x']:
                    self._add_line(f"{qubit_var} = x({qubit_var})")
                elif gate_name in ['y', 'pauli_y']:
                    self._add_line(f"{qubit_var} = y({qubit_var})")
                elif gate_name in ['z', 'pauli_z']:
                    self._add_line(f"{qubit_var} = z({qubit_var})")
                    
        except Exception as e:
            self._add_line(f"# Warning: Could not decompose Clifford {clifford_index}")
    
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
    
    def _build_condition_expression(self, domain: Set[int]) -> str:
        """
        Build a boolean expression for conditional corrections.
        
        In MBQC, corrections depend on the parity (XOR) of measurement
        outcomes. This method creates the classical logic expression.
        
        Args:
            domain: Set of node indices whose measurements to XOR
            
        Returns:
            String containing the boolean expression
        """
        if not domain:
            return "False"
        
        domain_list = sorted(domain)
        
        # Get measurement variable names
        meas_vars = []
        for node_idx in domain_list:
            if node_idx in self.classical_vars:
                meas_vars.append(self.classical_vars[node_idx])
        
        if not meas_vars:
            return "False"
        
        if len(meas_vars) == 1:
            return meas_vars[0]
        
        # Build XOR expression: a ^ b ^ c ...
        return " ^ ".join(meas_vars)
    
    def _build_return_statement(self, output_nodes: List[int], 
                                measured_nodes: List[int]):
        """Generate the return statement for the function."""
        return_values = []
        
        # Add output qubits
        for node_idx in output_nodes:
            if node_idx in self.qubit_vars:
                return_values.append(self.qubit_vars[node_idx])
            else:
                # This shouldn't happen, but handle gracefully
                self._add_line(f"# Warning: Output node {node_idx} not found")
                
        # Add classical measurement results
        for node_idx in measured_nodes:
            if node_idx in self.classical_vars:
                return_values.append(self.classical_vars[node_idx])
            else:
                return_values.append("False")
        
        if not return_values:
            self._add_line("return None")
        elif len(return_values) == 1:
            self._add_line(f"return {return_values[0]}")
        else:
            return_str = ", ".join(return_values)
            self._add_line(f"return {return_str}")


def convert_graphix_pattern_to_guppy(pattern: Pattern, compile_module: bool = False):
    """
    Convert a Graphix MBQC pattern to Guppy quantum code.
    
    Args:
        pattern: The Graphix pattern to convert
        compile_module: If True, attempt to compile to GuppyModule (requires guppy installed)
        
    Returns:
        If compile_module is True and Guppy is available: GuppyModule
        Otherwise: String containing the Guppy function definition
    """
    converter = GraphixToGuppyConverter()
    return converter.convert(pattern, compile_module=compile_module)


if __name__ == "__main__":
    print("Graphix to Guppy Converter")
    print("=" * 50)
    
    from graphix import Circuit
    
    # Test with simple Hadamard gate
    print("\nTest 1: Circuit with Hadamard gate")
    circuit = Circuit(1)
    circuit.h(0)
    pattern = circuit.transpile().pattern
    
    guppy_code = convert_graphix_pattern_to_guppy(pattern)
    print(guppy_code)
    print()
    
    # Test with S gate (Clifford)
    print("\nTest 2: Circuit with S gate (Clifford)")
    circuit2 = Circuit(1)
    circuit2.s(0)
    pattern2 = circuit2.transpile().pattern
    
    guppy_code2 = convert_graphix_pattern_to_guppy(pattern2)
    print(guppy_code2)
    print()
    
    # Test with rotation
    print("\nTest 3: Circuit with Rz rotation")
    circuit3 = Circuit(1)
    circuit3.rz(0, np.pi/4)
    pattern3 = circuit3.transpile().pattern
    
    guppy_code3 = convert_graphix_pattern_to_guppy(pattern3)
    print(guppy_code3)
    print()
    
    # Test with two-qubit gate
    print("\nTest 4: Circuit with CNOT gate")
    circuit4 = Circuit(2)
    circuit4.cnot(0, 1)
    pattern4 = circuit4.transpile().pattern
    
    guppy_code4 = convert_graphix_pattern_to_guppy(pattern4)
    print(guppy_code4)
    
    print("\n" + "=" * 50)
    print("All tests completed!")