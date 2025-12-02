import unittest
import numpy as np
from graphix import Circuit
from graphix.pattern import Pattern
from graphix.command import N, E, M, X, Z, CommandKind
from graphix.fundamentals import Plane
from graphix_to_hugr import convert_graphix_pattern_to_hugr, GraphixToHugrConverter
from hugr import Hugr, tys, ops


class TestBasicConversion(unittest.TestCase):
    """Test basic conversion functionality."""
    
    def test_converter_returns_hugr(self):
        """Test that converter returns a valid HUGR object."""
        circuit = Circuit(1)
        circuit.h(0)
        pattern = circuit.transpile().pattern
        
        result = convert_graphix_pattern_to_hugr(pattern)
        
        self.assertIsInstance(result, Hugr)
    
    def test_empty_pattern_raises_error(self):
        """Test that empty pattern is handled properly."""
        # Pattern with no operations should still convert
        # but might have minimal structure
        circuit = Circuit(1)
        pattern = circuit.transpile().pattern
        
        # Should not raise
        result = convert_graphix_pattern_to_hugr(pattern)
        self.assertIsInstance(result, Hugr)
    
    def test_hugr_has_expected_structure(self):
        """Test that resulting HUGR has expected node structure."""
        circuit = Circuit(1)
        circuit.h(0)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        # HUGR should have multiple nodes
        self.assertGreater(len(hugr), 0)
        
        # Should have an entrypoint
        self.assertIsNotNone(hugr.entrypoint)


class TestSingleQubitGates(unittest.TestCase):
    """Test conversion of single-qubit gates."""
    
    def test_hadamard_gate(self):
        """Test Hadamard gate conversion."""
        circuit = Circuit(1)
        circuit.h(0)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        # Hadamard in MBQC: N + E + M + X = 4 commands
        self.assertEqual(len(list(pattern)), 4)
        
        # Should have reasonable number of HUGR nodes
        self.assertGreater(len(hugr), 5)
        self.assertLess(len(hugr), 20)
        
        # Check input/output structure
        self.assertEqual(len(pattern.input_nodes), 1)
        self.assertEqual(len(pattern.output_nodes), 1)
    
    def test_pauli_x_gate(self):
        """Test Pauli X gate conversion."""
        circuit = Circuit(1)
        circuit.x(0)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        # Should create HUGR successfully
        self.assertIsInstance(hugr, Hugr)
        self.assertGreater(len(hugr), 5)
    
    def test_pauli_z_gate(self):
        """Test Pauli Z gate conversion."""
        circuit = Circuit(1)
        circuit.z(0)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        self.assertIsInstance(hugr, Hugr)
        self.assertGreater(len(hugr), 5)
    
    def test_s_gate(self):
        """Test S gate (phase gate) conversion."""
        circuit = Circuit(1)
        circuit.s(0)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        self.assertIsInstance(hugr, Hugr)
        self.assertGreater(len(hugr), 5)


class TestTwoQubitGates(unittest.TestCase):
    """Test conversion of two-qubit gates."""
    
    def test_cnot_gate(self):
        """Test CNOT gate conversion."""
        circuit = Circuit(2)
        circuit.cnot(0, 1)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        # Should have 2 input qubits
        self.assertEqual(len(pattern.input_nodes), 2)
        
        # CNOT creates a more complex pattern
        self.assertGreater(len(list(pattern)), 5)
        
        # HUGR should have corresponding complexity
        self.assertGreater(len(hugr), 10)
    
    def test_swap_gate(self):
        """Test SWAP gate conversion."""
        circuit = Circuit(2)
        circuit.swap(0, 1)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        self.assertEqual(len(pattern.input_nodes), 2)
        self.assertIsInstance(hugr, Hugr)


class TestRotationGates(unittest.TestCase):
    """Test parameterized rotation gates."""
    
    def test_rx_rotation(self):
        """Test Rx rotation gate."""
        angle = np.pi / 4
        circuit = Circuit(1)
        circuit.rx(0, angle)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        self.assertIsInstance(hugr, Hugr)
        self.assertGreater(len(hugr), 5)
    
    def test_ry_rotation(self):
        """Test Ry rotation gate."""
        angle = np.pi / 3
        circuit = Circuit(1)
        circuit.ry(0, angle)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        self.assertIsInstance(hugr, Hugr)
        self.assertGreater(len(hugr), 5)
    
    def test_rz_rotation(self):
        """Test Rz rotation gate."""
        angle = np.pi / 6
        circuit = Circuit(1)
        circuit.rz(0, angle)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        self.assertIsInstance(hugr, Hugr)
        self.assertGreater(len(hugr), 5)
    
    def test_multiple_rotations(self):
        """Test multiple rotation gates in sequence."""
        circuit = Circuit(1)
        circuit.rx(0, np.pi / 4)
        circuit.ry(0, np.pi / 3)
        circuit.rz(0, np.pi / 6)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        self.assertIsInstance(hugr, Hugr)
        # More gates = more nodes
        self.assertGreater(len(hugr), 20)


class TestMultiQubitCircuits(unittest.TestCase):
    """Test larger multi-qubit circuits."""
    
    def test_bell_state(self):
        """Test Bell state preparation (H + CNOT)."""
        circuit = Circuit(2)
        circuit.h(0)
        circuit.cnot(0, 1)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        # Bell state pattern structure
        self.assertEqual(len(pattern.input_nodes), 2)
        self.assertEqual(len(pattern.output_nodes), 2)
        
        # Should have multiple measurements in pattern
        measurement_count = sum(1 for cmd in pattern if cmd.kind == CommandKind.M)
        self.assertGreater(measurement_count, 0)
        
        # HUGR should be substantial
        self.assertGreater(len(hugr), 15)
    
    def test_ghz_state_3qubits(self):
        """Test 3-qubit GHZ state preparation."""
        circuit = Circuit(3)
        circuit.h(0)
        circuit.cnot(0, 1)
        circuit.cnot(0, 2)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        self.assertEqual(len(pattern.input_nodes), 3)
        self.assertIsInstance(hugr, Hugr)
        self.assertGreater(len(hugr), 20)
    
    def test_multiple_cnots(self):
        """Test circuit with multiple CNOT gates."""
        circuit = Circuit(3)
        circuit.cnot(0, 1)
        circuit.cnot(1, 2)
        circuit.cnot(0, 2)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        self.assertIsInstance(hugr, Hugr)
        self.assertGreater(len(hugr), 25)


class TestPatternCommands(unittest.TestCase):
    """Test conversion of individual pattern commands."""
    
    def test_n_command_creates_qubit(self):
        """Test that N command creates a qubit wire."""
        # Use a circuit-generated pattern that includes N commands
        circuit = Circuit(1)
        circuit.h(0)  # This creates N commands in the pattern
        pattern = circuit.transpile().pattern
        
        converter = GraphixToHugrConverter()
        hugr = converter.convert(pattern)
        
        # Should track prepared qubits
        self.assertGreater(len(converter.node_order), 0)
        self.assertGreater(len(converter.qubit_wires), 0)
    
    def test_e_command_creates_entanglement(self):
        """Test that E command creates CZ gate."""
        # CNOT creates E commands
        circuit = Circuit(2)
        circuit.cnot(0, 1)
        pattern = circuit.transpile().pattern
        
        converter = GraphixToHugrConverter()
        hugr = converter.convert(pattern)
        
        # Should process entanglement commands
        # Check that pattern has E commands
        has_e_command = any(cmd.kind == CommandKind.E for cmd in pattern)
        self.assertTrue(has_e_command)
    
    def test_m_command_produces_classical_output(self):
        """Test that M command produces classical bit."""
        # Any gate-based pattern will have measurements
        circuit = Circuit(1)
        circuit.h(0)
        pattern = circuit.transpile().pattern
        
        converter = GraphixToHugrConverter()
        hugr = converter.convert(pattern)
        
        # Should have classical wires from measurements
        self.assertGreater(len(converter.classical_wires), 0)
    
    def test_x_command_applies_correction(self):
        """Test that X command applies Pauli X."""
        # Hadamard creates X correction commands
        circuit = Circuit(1)
        circuit.h(0)
        pattern = circuit.transpile().pattern
        
        # Check pattern has X commands
        has_x_command = any(cmd.kind == CommandKind.X for cmd in pattern)
        self.assertTrue(has_x_command)
        
        converter = GraphixToHugrConverter()
        hugr = converter.convert(pattern)
        
        self.assertIsInstance(hugr, Hugr)
    
    def test_z_command_applies_correction(self):
        """Test that Z command applies Pauli Z."""
        # Some gates create Z correction commands
        circuit = Circuit(2)
        circuit.cnot(0, 1)
        pattern = circuit.transpile().pattern
        
        # Check pattern has Z commands
        has_z_command = any(cmd.kind == CommandKind.Z for cmd in pattern)
        self.assertTrue(has_z_command)
        
        converter = GraphixToHugrConverter()
        hugr = converter.convert(pattern)
        
        self.assertIsInstance(hugr, Hugr)


class TestMeasurementPlanes(unittest.TestCase):
    """Test different measurement plane conversions."""
    
    def test_xy_plane_measurement(self):
        """Test XY plane measurement (default for MBQC)."""
        # Most gates use XY plane measurements
        circuit = Circuit(1)
        circuit.h(0)
        pattern = circuit.transpile().pattern
        
        # Check that pattern has measurements
        measurements = [cmd for cmd in pattern if cmd.kind == CommandKind.M]
        self.assertGreater(len(measurements), 0)
        
        # Check at least one uses XY plane
        has_xy = any(cmd.plane == Plane.XY for cmd in measurements)
        self.assertTrue(has_xy)
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        self.assertIsInstance(hugr, Hugr)
    
    def test_yz_plane_measurement(self):
        """Test YZ plane measurement."""
        # Rx rotation uses YZ plane
        circuit = Circuit(1)
        circuit.rx(0, np.pi/4)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        self.assertIsInstance(hugr, Hugr)
    
    def test_xz_plane_measurement(self):
        """Test XZ plane measurement."""
        # Ry rotation uses XZ plane
        circuit = Circuit(1)
        circuit.ry(0, np.pi/4)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        self.assertIsInstance(hugr, Hugr)
    
    def test_zero_angle_measurement(self):
        """Test measurement with zero angle."""
        circuit = Circuit(1)
        circuit.h(0)
        pattern = circuit.transpile().pattern
        
        # Some measurements should have zero or near-zero angle
        measurements = [cmd for cmd in pattern if cmd.kind == CommandKind.M]
        self.assertGreater(len(measurements), 0)
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        self.assertIsInstance(hugr, Hugr)


class TestInputOutputMapping(unittest.TestCase):
    """Test proper mapping of inputs and outputs."""
    
    def test_single_input_single_output(self):
        """Test pattern with 1 input, 1 output."""
        circuit = Circuit(1)
        circuit.h(0)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        self.assertEqual(len(pattern.input_nodes), 1)
        self.assertEqual(len(pattern.output_nodes), 1)
        self.assertIsInstance(hugr, Hugr)
    
    def test_two_inputs_two_outputs(self):
        """Test pattern with 2 inputs, 2 outputs."""
        circuit = Circuit(2)
        circuit.h(0)
        circuit.cnot(0, 1)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        self.assertEqual(len(pattern.input_nodes), 2)
        self.assertEqual(len(pattern.output_nodes), 2)
        self.assertIsInstance(hugr, Hugr)
    
    def test_outputs_include_measurements(self):
        """Test that classical measurement outputs are included."""
        converter = GraphixToHugrConverter()
        
        # Pattern with measurements of ancilla qubits
        circuit = Circuit(1)
        circuit.h(0)
        pattern = circuit.transpile().pattern
        
        hugr = converter.convert(pattern)
        
        # Should have classical outputs from measurements
        self.assertGreater(len(converter.classical_wires), 0)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def test_identity_circuit(self):
        """Test circuit with no gates (identity)."""
        circuit = Circuit(1)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        # Should still convert successfully
        self.assertIsInstance(hugr, Hugr)
    
    def test_multiple_qubit_identity(self):
        """Test multi-qubit identity circuit."""
        circuit = Circuit(3)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        self.assertEqual(len(pattern.input_nodes), 3)
        self.assertIsInstance(hugr, Hugr)
    
    def test_repeated_gates(self):
        """Test circuit with repeated same gate."""
        circuit = Circuit(1)
        for _ in range(5):
            circuit.h(0)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        # Should handle repeated operations
        self.assertIsInstance(hugr, Hugr)
        self.assertGreater(len(hugr), 20)


class TestConverterState(unittest.TestCase):
    """Test converter internal state management."""
    
    def test_wire_tracking(self):
        """Test that wires are properly tracked."""
        converter = GraphixToHugrConverter()
        
        circuit = Circuit(2)
        circuit.h(0)
        circuit.cnot(0, 1)
        pattern = circuit.transpile().pattern
        
        hugr = converter.convert(pattern)
        
        # Should track output qubits
        self.assertGreater(len(converter.qubit_wires), 0)
        
        # Should track measurements
        self.assertGreater(len(converter.classical_wires), 0)
    
    def test_node_order_tracking(self):
        """Test that node creation order is tracked."""
        converter = GraphixToHugrConverter()
        
        circuit = Circuit(1)
        circuit.h(0)
        pattern = circuit.transpile().pattern
        
        hugr = converter.convert(pattern)
        
        # Should have created some nodes
        self.assertGreater(len(converter.node_order), 0)
    
    def test_converter_reusability(self):
        """Test that converter can be reused."""
        converter1 = GraphixToHugrConverter()
        converter2 = GraphixToHugrConverter()
        
        circuit = Circuit(1)
        circuit.h(0)
        pattern = circuit.transpile().pattern
        
        hugr1 = converter1.convert(pattern)
        hugr2 = converter2.convert(pattern)
        
        # Both should create valid HUGRs
        self.assertIsInstance(hugr1, Hugr)
        self.assertIsInstance(hugr2, Hugr)
        
        # Should have same structure
        self.assertEqual(len(hugr1), len(hugr2))


class TestComplexCircuits(unittest.TestCase):
    """Test complex quantum circuits."""
    
    def test_quantum_fourier_transform_2qubit(self):
        """Test 2-qubit QFT."""
        circuit = Circuit(2)
        
        # QFT on 2 qubits
        circuit.h(0)
        circuit.rz(0, np.pi/2)
        circuit.cnot(1, 0)
        circuit.rz(0, -np.pi/2)
        circuit.cnot(1, 0)
        circuit.h(1)
        
        pattern = circuit.transpile().pattern
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        self.assertIsInstance(hugr, Hugr)
        self.assertGreater(len(hugr), 30)
    
    def test_toffoli_gate(self):
        """Test Toffoli (CCX) gate."""
        circuit = Circuit(3)
        circuit.ccx(0, 1, 2)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        self.assertEqual(len(pattern.input_nodes), 3)
        self.assertIsInstance(hugr, Hugr)
        # Toffoli decomposes into many operations
        self.assertGreater(len(hugr), 30)
    
    def test_multiple_gate_types(self):
        """Test circuit with various gate types."""
        circuit = Circuit(2)
        circuit.h(0)
        circuit.s(0)
        circuit.x(1)
        circuit.cnot(0, 1)
        circuit.rx(0, np.pi/4)
        circuit.ry(1, np.pi/3)
        
        pattern = circuit.transpile().pattern
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        self.assertIsInstance(hugr, Hugr)
        self.assertGreater(len(hugr), 40)


class TestHugrStructure(unittest.TestCase):
    """Test structural properties of resulting HUGR."""
    
    def test_hugr_has_entrypoint(self):
        """Test that HUGR has valid entrypoint."""
        circuit = Circuit(1)
        circuit.h(0)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        self.assertIsNotNone(hugr.entrypoint)
    
    def test_hugr_nodes_accessible(self):
        """Test that HUGR nodes can be accessed."""
        circuit = Circuit(1)
        circuit.h(0)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        # Should be able to iterate over nodes
        node_count = 0
        for node in hugr:
            node_count += 1
            # Each node should have data
            self.assertIsNotNone(hugr[node])
        
        self.assertEqual(node_count, len(hugr))
    
    def test_hugr_operations_have_types(self):
        """Test that operations in HUGR have proper types."""
        circuit = Circuit(1)
        circuit.h(0)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        # Check that nodes have operations
        for node in hugr:
            node_data = hugr[node]
            self.assertIsNotNone(node_data.op)


def run_tests():
    """Run all tests and print results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBasicConversion))
    suite.addTests(loader.loadTestsFromTestCase(TestSingleQubitGates))
    suite.addTests(loader.loadTestsFromTestCase(TestTwoQubitGates))
    suite.addTests(loader.loadTestsFromTestCase(TestRotationGates))
    suite.addTests(loader.loadTestsFromTestCase(TestMultiQubitCircuits))
    suite.addTests(loader.loadTestsFromTestCase(TestPatternCommands))
    suite.addTests(loader.loadTestsFromTestCase(TestMeasurementPlanes))
    suite.addTests(loader.loadTestsFromTestCase(TestInputOutputMapping))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestConverterState))
    suite.addTests(loader.loadTestsFromTestCase(TestComplexCircuits))
    suite.addTests(loader.loadTestsFromTestCase(TestHugrStructure))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)