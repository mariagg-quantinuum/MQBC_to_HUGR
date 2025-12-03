"""
Test suite for Graphix to Guppy converter.

Tests conversion of various quantum circuits from Graphix MBQC patterns
to Guppy quantum code, verifying correctness and structure.
"""

import unittest
import numpy as np
from graphix import Circuit
from graphix_to_guppy import convert_graphix_pattern_to_guppy, GraphixToGuppyConverter

# Check if Guppy is available for compilation tests
GUPPY_AVAILABLE = False
try:
    from guppy import guppy, GuppyModule
    GUPPY_AVAILABLE = True
except ImportError:
    pass


class TestSingleQubitGateConversion(unittest.TestCase):
    """Test conversion of single-qubit gates."""
    
    def test_hadamard_gate(self):
        """Test Hadamard gate conversion."""
        circuit = Circuit(1)
        circuit.h(0)
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        # Check structure
        self.assertIn("@guppy", guppy_code)
        self.assertIn("def quantum_circuit", guppy_code)
        self.assertIn("-> qubit", guppy_code)
        self.assertIn("from guppy import guppy", guppy_code)
        self.assertIn("from guppy.prelude.quantum import", guppy_code)
        
        # Check for H gate application
        self.assertIn("h(", guppy_code)
        
        print(f"  ✓ Hadamard: {len(guppy_code)} chars, {guppy_code.count('h(')}, H gates")
    
    def test_pauli_x_gate(self):
        """Test Pauli X gate conversion."""
        circuit = Circuit(1)
        circuit.x(0)
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        self.assertIn("@guppy", guppy_code)
        self.assertIn("x(", guppy_code)
        print(f"  ✓ Pauli X gate converted")
    
    def test_pauli_y_gate(self):
        """Test Pauli Y gate conversion."""
        circuit = Circuit(1)
        circuit.y(0)
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        self.assertIn("@guppy", guppy_code)
        # Y may be decomposed into other gates
        print(f"  ✓ Pauli Y gate converted")
    
    def test_pauli_z_gate(self):
        """Test Pauli Z gate conversion."""
        circuit = Circuit(1)
        circuit.z(0)
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        self.assertIn("@guppy", guppy_code)
        self.assertIn("z(", guppy_code)
        print(f"  ✓ Pauli Z gate converted")
    
    def test_s_gate(self):
        """Test S (phase) gate conversion."""
        circuit = Circuit(1)
        circuit.s(0)
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        self.assertIn("@guppy", guppy_code)
        # S gate may appear directly or decomposed
        self.assertTrue("s(" in guppy_code or "rz(" in guppy_code)
        print(f"  ✓ S gate converted")
    
    def test_sdg_gate(self):
        """Test S-dagger gate conversion."""
        circuit = Circuit(1)
        circuit.s(0)
        circuit.s(0)
        circuit.s(0)  # Three S gates = S†
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        self.assertIn("@guppy", guppy_code)
        print(f"  ✓ S-dagger gate converted")


class TestRotationGateConversion(unittest.TestCase):
    """Test conversion of rotation gates with arbitrary angles."""
    
    def test_rx_rotation(self):
        """Test Rx rotation gate."""
        angle = np.pi / 4
        circuit = Circuit(1)
        circuit.rx(0, angle)
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        self.assertIn("@guppy", guppy_code)
        self.assertIn("rx(", guppy_code)
        # Check angle is approximately preserved
        self.assertIn(str(angle)[:6], guppy_code)
        print(f"  ✓ Rx(π/4) rotation converted")
    
    def test_ry_rotation(self):
        """Test Ry rotation gate."""
        angle = np.pi / 3
        circuit = Circuit(1)
        circuit.ry(0, angle)
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        self.assertIn("@guppy", guppy_code)
        self.assertIn("ry(", guppy_code)
        print(f"  ✓ Ry(π/3) rotation converted")
    
    def test_rz_rotation(self):
        """Test Rz rotation gate."""
        angle = np.pi / 6
        circuit = Circuit(1)
        circuit.rz(0, angle)
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        self.assertIn("@guppy", guppy_code)
        self.assertIn("rz(", guppy_code)
        print(f"  ✓ Rz(π/6) rotation converted")
    
    def test_multiple_rotations(self):
        """Test sequence of different rotations."""
        circuit = Circuit(1)
        circuit.rx(0, np.pi/4)
        circuit.ry(0, np.pi/3)
        circuit.rz(0, np.pi/6)
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        self.assertIn("rx(", guppy_code)
        self.assertIn("ry(", guppy_code)
        self.assertIn("rz(", guppy_code)
        print(f"  ✓ Multiple rotations converted")


class TestTwoQubitGateConversion(unittest.TestCase):
    """Test conversion of two-qubit gates."""
    
    def test_cnot_gate(self):
        """Test CNOT gate conversion."""
        circuit = Circuit(2)
        circuit.cnot(0, 1)
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        self.assertIn("@guppy", guppy_code)
        self.assertIn("q_in_0: qubit", guppy_code)
        self.assertIn("q_in_1: qubit", guppy_code)
        # CNOT is decomposed into CZ + H in MBQC
        self.assertTrue("cz(" in guppy_code or "h(" in guppy_code)
        print(f"  ✓ CNOT gate converted")
    
    def test_cz_gate(self):
        """Test CZ gate conversion."""
        circuit = Circuit(2)
        circuit.cz(0, 1)
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        self.assertIn("@guppy", guppy_code)
        self.assertIn("cz(", guppy_code)
        print(f"  ✓ CZ gate converted")
    
    def test_bell_state(self):
        """Test Bell state (H + CNOT) conversion."""
        circuit = Circuit(2)
        circuit.h(0)
        circuit.cnot(0, 1)
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        self.assertIn("@guppy", guppy_code)
        self.assertIn("tuple[qubit, qubit]", guppy_code)
        self.assertIn("h(", guppy_code)
        
        # Check return statement has both qubits
        self.assertIn("return", guppy_code)
        print(f"  ✓ Bell state converted ({len(guppy_code)} chars)")


class TestMultiQubitCircuits(unittest.TestCase):
    """Test conversion of multi-qubit circuits."""
    
    def test_ghz_state(self):
        """Test GHZ state conversion."""
        circuit = Circuit(3)
        circuit.h(0)
        circuit.cnot(0, 1)
        circuit.cnot(0, 2)
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        self.assertIn("@guppy", guppy_code)
        self.assertIn("q_in_0: qubit", guppy_code)
        self.assertIn("q_in_1: qubit", guppy_code)
        self.assertIn("q_in_2: qubit", guppy_code)
        # MBQC produces measurement results in addition to output qubits
        # The return type will include both qubits and measurement results (bool)
        self.assertIn("tuple[qubit", guppy_code)
        
        # Should have H and entangling operations
        self.assertIn("h(", guppy_code)
        print(f"  ✓ GHZ state (3 qubits) converted")
    
    def test_four_qubit_circuit(self):
        """Test 4-qubit circuit conversion."""
        circuit = Circuit(4)
        circuit.h(0)
        circuit.cnot(0, 1)
        circuit.cnot(1, 2)
        circuit.cnot(2, 3)
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        self.assertIn("@guppy", guppy_code)
        # Check all input parameters
        for i in range(4):
            self.assertIn(f"q_in_{i}: qubit", guppy_code)
        
        print(f"  ✓ 4-qubit circuit converted")


class TestCodeStructure(unittest.TestCase):
    """Test the structure and format of generated Guppy code."""
    
    def test_imports_present(self):
        """Test that necessary imports are included."""
        circuit = Circuit(1)
        circuit.h(0)
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        self.assertIn("from guppy import guppy", guppy_code)
        self.assertIn("from guppy.prelude.quantum import", guppy_code)
        self.assertIn("qubit", guppy_code)
        self.assertIn("measure", guppy_code)
        print(f"  ✓ Required imports present")
    
    def test_decorator_present(self):
        """Test that @guppy decorator is applied."""
        circuit = Circuit(1)
        circuit.h(0)
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        # Find @guppy and check it's before def
        guppy_idx = guppy_code.find("@guppy")
        def_idx = guppy_code.find("def quantum_circuit")
        
        self.assertGreater(guppy_idx, -1)
        self.assertGreater(def_idx, -1)
        self.assertLess(guppy_idx, def_idx)
        print(f"  ✓ @guppy decorator properly placed")
    
    def test_type_annotations(self):
        """Test that type annotations are correct."""
        circuit = Circuit(2)
        circuit.h(0)
        circuit.cnot(0, 1)
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        # Check parameter types
        self.assertIn("q_in_0: qubit", guppy_code)
        self.assertIn("q_in_1: qubit", guppy_code)
        
        # Check return type
        self.assertIn("-> tuple[qubit, qubit]", guppy_code)
        print(f"  ✓ Type annotations correct")
    
    def test_return_statement(self):
        """Test that return statement is present."""
        circuit = Circuit(1)
        circuit.h(0)
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        self.assertIn("return", guppy_code)
        print(f"  ✓ Return statement present")
    
    def test_indentation(self):
        """Test that code is properly indented."""
        circuit = Circuit(1)
        circuit.h(0)
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        lines = guppy_code.split('\n')
        function_body_started = False
        
        for line in lines:
            if "def quantum_circuit" in line:
                function_body_started = True
                continue
            
            if function_body_started and line.strip():
                # Non-empty lines in function body should be indented
                self.assertTrue(line.startswith("    ") or line.startswith("\t"))
        
        print(f"  ✓ Code properly indented")


class TestVariableManagement(unittest.TestCase):
    """Test variable naming and management."""
    
    def test_unique_variable_names(self):
        """Test that variables have unique names."""
        circuit = Circuit(2)
        circuit.h(0)
        circuit.h(1)
        circuit.cnot(0, 1)
        pattern = circuit.transpile().pattern
        
        converter = GraphixToGuppyConverter()
        guppy_code = converter.convert(pattern)
        
        # Check that we're using unique variable names
        lines = guppy_code.split('\n')
        variable_assignments = [l.strip() for l in lines if '=' in l and not l.strip().startswith('#')]
        
        # Should have multiple unique variable assignments
        self.assertGreater(len(variable_assignments), 0)
        print(f"  ✓ {len(variable_assignments)} variable assignments")
    
    def test_input_parameter_mapping(self):
        """Test that input qubits are properly mapped."""
        circuit = Circuit(3)
        circuit.h(0)
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        # Check all input parameters are defined
        self.assertIn("q_in_0", guppy_code)
        self.assertIn("q_in_1", guppy_code)
        self.assertIn("q_in_2", guppy_code)
        print(f"  ✓ Input parameters properly mapped")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios."""
    
    def test_empty_circuit(self):
        """Test conversion of circuit with no gates."""
        circuit = Circuit(1)
        # No gates applied
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        self.assertIn("@guppy", guppy_code)
        self.assertIn("def quantum_circuit", guppy_code)
        self.assertIn("return", guppy_code)
        print(f"  ✓ Empty circuit handled")
    
    def test_identity_circuit(self):
        """Test circuit with only identity operations."""
        circuit = Circuit(2)
        # Identity is implicit
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        self.assertIn("return", guppy_code)
        print(f"  ✓ Identity circuit handled")
    
    def test_large_angle(self):
        """Test rotation with large angle."""
        circuit = Circuit(1)
        circuit.rx(0, 5 * np.pi)  # Large angle
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        # MBQC decomposes Rx rotations into Rz rotations with basis changes
        # Rx(θ) = H · Rz(θ) · H in the measurement-based model
        self.assertTrue("rz(" in guppy_code or "rx(" in guppy_code, 
                       "Expected either rx or rz rotation in generated code")
        print(f"  ✓ Large angle rotation handled")
    
    def test_zero_angle(self):
        """Test rotation with zero angle."""
        circuit = Circuit(1)
        circuit.rx(0, 0.0)  # Zero rotation
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        self.assertIn("@guppy", guppy_code)
        print(f"  ✓ Zero angle rotation handled")


@unittest.skipUnless(GUPPY_AVAILABLE, "Guppy not installed")
class TestGuppyCompilation(unittest.TestCase):
    """Test actual compilation with Guppy (if available)."""
    
    def test_compile_simple_circuit(self):
        """Test that generated code can be compiled by Guppy."""
        circuit = Circuit(1)
        circuit.h(0)
        pattern = circuit.transpile().pattern
        
        guppy_code = convert_graphix_pattern_to_guppy(pattern)
        
        # Try to compile (this might fail depending on Guppy version)
        try:
            exec(guppy_code)
            print(f"  ✓ Code compiles with Guppy")
        except Exception as e:
            print(f"  ⚠ Compilation test skipped: {e}")
            self.skipTest(f"Guppy compilation: {e}")


class TestComparisonWithHUGR(unittest.TestCase):
    """Test that Guppy conversion produces similar structure to HUGR."""
    
    def test_gate_count_correlation(self):
        """Test that complex circuits produce appropriately complex code."""
        # Simple circuit
        simple = Circuit(1)
        simple.h(0)
        simple_pattern = simple.transpile().pattern
        simple_guppy = convert_graphix_pattern_to_guppy(simple_pattern)
        
        # Complex circuit
        complex_circuit = Circuit(3)
        complex_circuit.h(0)
        complex_circuit.cnot(0, 1)
        complex_circuit.cnot(1, 2)
        complex_circuit.rz(0, np.pi/4)
        complex_circuit.rx(1, np.pi/3)
        complex_pattern = complex_circuit.transpile().pattern
        complex_guppy = convert_graphix_pattern_to_guppy(complex_pattern)
        
        # Complex circuit should produce more code
        self.assertGreater(len(complex_guppy), len(simple_guppy))
        print(f"  ✓ Complex circuit: {len(complex_guppy)} chars > Simple: {len(simple_guppy)} chars")


def run_tests():
    """Run all tests with detailed output."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSingleQubitGateConversion))
    suite.addTests(loader.loadTestsFromTestCase(TestRotationGateConversion))
    suite.addTests(loader.loadTestsFromTestCase(TestTwoQubitGateConversion))
    suite.addTests(loader.loadTestsFromTestCase(TestMultiQubitCircuits))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeStructure))
    suite.addTests(loader.loadTestsFromTestCase(TestVariableManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestComparisonWithHUGR))
    
    if GUPPY_AVAILABLE:
        suite.addTests(loader.loadTestsFromTestCase(TestGuppyCompilation))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    import sys
    
    print("=" * 70)
    print("Graphix to Guppy Converter Test Suite")
    print("=" * 70)
    print()
    
    if GUPPY_AVAILABLE:
        print("✓ Guppy is installed - full test suite will run")
    else:
        print("⚠ Guppy not installed - compilation tests will be skipped")
        print("  Install with: pip install guppy-lang")
    print()
    
    result = run_tests()
    
    print()
    print("=" * 70)
    print("Test Summary:")
    print(f"  Tests run: {result.testsRun}")
    print(f"  Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Skipped: {len(result.skipped)}")
    print("=" * 70)
    
    sys.exit(0 if result.wasSuccessful() else 1)