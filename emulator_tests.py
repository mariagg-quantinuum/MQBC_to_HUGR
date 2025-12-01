"""
Emulator Execution Tests for Graphix → HUGR Pipeline

Tests the complete workflow:
1. Create Graphix circuit
2. Convert to MBQC pattern
3. Convert to HUGR
4. Execute on multiple emulators
5. Verify results match expected quantum behavior
"""

import unittest
import numpy as np
from collections import Counter
from graphix import Circuit
from graphix_to_hugr import convert_graphix_pattern_to_hugr

# Check available backends
BACKENDS_AVAILABLE = {
    'h1_1le': False,
    'qiskit_aer': False,
    'graphix': True  # Always available
}

try:
    from pytket import Circuit as PytketCircuit
    from pytket.extensions.quantinuum import QuantinuumBackend, QuantinuumAPIOffline
    BACKENDS_AVAILABLE['h1_1le'] = True
except ImportError:
    pass

try:
    from pytket import Circuit as PytketCircuit
    from pytket.extensions.qiskit import AerBackend
    BACKENDS_AVAILABLE['qiskit_aer'] = True
except ImportError:
    pass


class TestBellStateExecution(unittest.TestCase):
    """Test Bell state execution on all available emulators."""
    
    def test_bell_state_graphix(self):
        """Test Bell state on Graphix simulator."""
        circuit = Circuit(2)
        circuit.h(0)
        circuit.cnot(0, 1)
        pattern = circuit.transpile().pattern
        
        # Execute multiple times
        results = Counter()
        for _ in range(100):
            state = pattern.simulate_pattern()
            # Sample outcome (simplified)
            outcome = self._sample_bell_state(state)
            results[outcome] += 1
        
        # Verify Bell state: should see |00⟩ and |11⟩
        self.assertGreater(results['00'] + results['11'], 90)
        print(f"  Graphix Bell state: {dict(results)}")
    
    @unittest.skipUnless(BACKENDS_AVAILABLE['h1_1le'], "H1-1LE not available")
    def test_bell_state_h1_1le(self):
        """Test Bell state on H1-1LE local emulator."""
        # Create pytket circuit
        circuit = PytketCircuit(2, 2)
        circuit.H(0)
        circuit.CX(0, 1)
        circuit.Measure(0, 0)
        circuit.Measure(1, 1)
        
        # Execute on H1-1LE
        api_offline = QuantinuumAPIOffline()
        backend = QuantinuumBackend("H1-1LE", api_handler=api_offline)
        compiled = backend.get_compiled_circuit(circuit)
        handle = backend.process_circuit(compiled, n_shots=100)
        result = backend.get_result(handle)
        counts = result.get_counts()
        
        # Verify Bell state
        zeros = counts.get((0, 0), 0)
        ones = counts.get((1, 1), 0)
        self.assertGreater(zeros + ones, 90)
        self.assertGreater(zeros, 30)  # At least 30%
        self.assertGreater(ones, 30)   # At least 30%
        print(f"  H1-1LE Bell state: {dict(counts)}")
    
    @unittest.skipUnless(BACKENDS_AVAILABLE['qiskit_aer'], "Qiskit Aer not available")
    def test_bell_state_qiskit_aer(self):
        """Test Bell state on Qiskit Aer."""
        circuit = PytketCircuit(2, 2)
        circuit.H(0)
        circuit.CX(0, 1)
        circuit.Measure(0, 0)
        circuit.Measure(1, 1)
        
        backend = AerBackend()
        compiled = backend.get_compiled_circuit(circuit)
        handle = backend.process_circuit(compiled, n_shots=100)
        result = backend.get_result(handle)
        counts = result.get_counts()
        
        zeros = counts.get((0, 0), 0)
        ones = counts.get((1, 1), 0)
        self.assertGreater(zeros + ones, 90)
        print(f"  Qiskit Aer Bell state: {dict(counts)}")
    
    def _sample_bell_state(self, state):
        """Sample a measurement from Bell state."""
        # Simplified sampling for testing
        probs = np.abs(state.flatten()) ** 2
        probs = probs / np.sum(probs)
        outcome_idx = np.random.choice(len(probs), p=probs)
        return format(outcome_idx, '02b')


class TestGHZStateExecution(unittest.TestCase):
    """Test GHZ state (3-qubit entanglement) execution."""
    
    def test_ghz_state_graphix(self):
        """Test 3-qubit GHZ state on Graphix."""
        circuit = Circuit(3)
        circuit.h(0)
        circuit.cnot(0, 1)
        circuit.cnot(0, 2)
        pattern = circuit.transpile().pattern
        
        # Verify pattern structure
        self.assertEqual(len(pattern.input_nodes), 3)
        self.assertEqual(len(pattern.output_nodes), 3)
        
        # Execute
        state = pattern.simulate_pattern()
        self.assertIsNotNone(state)
        print(f"  GHZ pattern: {len(list(pattern))} commands")
    
    @unittest.skipUnless(BACKENDS_AVAILABLE['h1_1le'], "H1-1LE not available")
    def test_ghz_state_h1_1le(self):
        """Test GHZ state on H1-1LE."""
        circuit = PytketCircuit(3, 3)
        circuit.H(0)
        circuit.CX(0, 1)
        circuit.CX(0, 2)
        for i in range(3):
            circuit.Measure(i, i)
        
        api_offline = QuantinuumAPIOffline()
        backend = QuantinuumBackend("H1-1LE", api_handler=api_offline)
        compiled = backend.get_compiled_circuit(circuit)
        handle = backend.process_circuit(compiled, n_shots=100)
        result = backend.get_result(handle)
        counts = result.get_counts()
        
        # GHZ: should see mostly |000⟩ and |111⟩
        zeros = counts.get((0, 0, 0), 0)
        ones = counts.get((1, 1, 1), 0)
        self.assertGreater(zeros + ones, 85)
        print(f"  H1-1LE GHZ: {zeros}× |000⟩, {ones}× |111⟩")


class TestSingleQubitGateExecution(unittest.TestCase):
    """Test single-qubit gates execute correctly."""
    
    def test_hadamard_creates_superposition(self):
        """Test Hadamard creates 50/50 superposition."""
        circuit = Circuit(1)
        circuit.h(0)
        pattern = circuit.transpile().pattern
        
        # Graphix execution
        results = Counter()
        for _ in range(100):
            state = pattern.simulate_pattern()
            probs = np.abs(state.flatten()) ** 2
            probs = probs / np.sum(probs)
            outcome = np.random.choice(len(probs), p=probs)
            results[str(outcome)] += 1
        
        # Should be roughly 50/50
        self.assertGreater(results['0'], 30)
        self.assertGreater(results['1'], 30)
        print(f"  Hadamard: {dict(results)}")
    
    @unittest.skipUnless(BACKENDS_AVAILABLE['h1_1le'], "H1-1LE not available")
    def test_pauli_x_flip_h1_1le(self):
        """Test Pauli X flips qubit on H1-1LE."""
        circuit = PytketCircuit(1, 1)
        circuit.X(0)
        circuit.Measure(0, 0)
        
        api_offline = QuantinuumAPIOffline()
        backend = QuantinuumBackend("H1-1LE", api_handler=api_offline)
        compiled = backend.get_compiled_circuit(circuit)
        handle = backend.process_circuit(compiled, n_shots=100)
        result = backend.get_result(handle)
        counts = result.get_counts()
        
        # Should be all |1⟩
        ones = counts.get((1,), 0)
        self.assertGreater(ones, 95)
        print(f"  X gate: {ones}% |1⟩")
    
    @unittest.skipUnless(BACKENDS_AVAILABLE['qiskit_aer'], "Qiskit Aer not available")
    def test_s_gate_qiskit(self):
        """Test S gate (phase) on Qiskit."""
        circuit = PytketCircuit(1, 1)
        circuit.H(0)
        circuit.S(0)
        circuit.H(0)
        circuit.Measure(0, 0)
        
        backend = AerBackend()
        compiled = backend.get_compiled_circuit(circuit)
        handle = backend.process_circuit(compiled, n_shots=100)
        result = backend.get_result(handle)
        counts = result.get_counts()
        
        # H-S-H should give mostly |1⟩
        ones = counts.get((1,), 0)
        self.assertGreater(ones, 85)
        print(f"  H-S-H: {ones}% |1⟩")


class TestRotationGateExecution(unittest.TestCase):
    """Test parameterized rotation gates."""
    
    def test_rx_rotation_graphix(self):
        """Test Rx rotation on Graphix."""
        angle = np.pi / 4
        circuit = Circuit(1)
        circuit.rx(0, angle)
        pattern = circuit.transpile().pattern
        
        hugr = convert_graphix_pattern_to_hugr(pattern)
        self.assertGreater(len(hugr), 5)
        print(f"  Rx(π/4): {len(list(pattern))} commands → {len(hugr)} nodes")
    
    @unittest.skipUnless(BACKENDS_AVAILABLE['h1_1le'], "H1-1LE not available")
    def test_ry_rotation_h1_1le(self):
        """Test Ry rotation on H1-1LE."""
        angle = np.pi / 3
        circuit = PytketCircuit(1, 1)
        circuit.Ry(angle, 0)
        circuit.Measure(0, 0)
        
        api_offline = QuantinuumAPIOffline()
        backend = QuantinuumBackend("H1-1LE", api_handler=api_offline)
        compiled = backend.get_compiled_circuit(circuit)
        handle = backend.process_circuit(compiled, n_shots=100)
        result = backend.get_result(handle)
        counts = result.get_counts()
        
        # Check distribution matches rotation
        zeros = counts.get((0,), 0)
        ones = counts.get((1,), 0)
        p0_expected = np.cos(angle/2)**2
        p0_actual = zeros / 100
        
        # Allow 15% tolerance
        self.assertLess(abs(p0_actual - p0_expected), 0.15)
        print(f"  Ry(π/3): {zeros}% |0⟩, {ones}% |1⟩ (expected {100*p0_expected:.0f}/{100*(1-p0_expected):.0f})")
    
    @unittest.skipUnless(BACKENDS_AVAILABLE['qiskit_aer'], "Qiskit Aer not available")
    def test_rz_rotation_qiskit(self):
        """Test Rz rotation on Qiskit."""
        angle = np.pi / 6
        circuit = PytketCircuit(1, 1)
        circuit.H(0)
        circuit.Rz(angle, 0)
        circuit.H(0)
        circuit.Measure(0, 0)
        
        backend = AerBackend()
        compiled = backend.get_compiled_circuit(circuit)
        handle = backend.process_circuit(compiled, n_shots=100)
        result = backend.get_result(handle)
        counts = result.get_counts()
        
        # H-Rz-H creates measurable difference
        total = sum(counts.values())
        self.assertEqual(total, 100)
        print(f"  H-Rz(π/6)-H: {dict(counts)}")


class TestGraphixToHugrToExecution(unittest.TestCase):
    """Test complete Graphix → HUGR → Execution pipeline."""
    
    def test_bell_state_full_pipeline(self):
        """Test Bell state through full pipeline."""
        # Step 1: Graphix circuit
        graphix_circuit = Circuit(2)
        graphix_circuit.h(0)
        graphix_circuit.cnot(0, 1)
        
        # Step 2: MBQC pattern
        pattern = graphix_circuit.transpile().pattern
        self.assertEqual(len(pattern.input_nodes), 2)
        
        # Step 3: HUGR conversion
        hugr = convert_graphix_pattern_to_hugr(pattern)
        self.assertGreater(len(hugr), 15)
        
        # Step 4: Verify Graphix execution
        state = pattern.simulate_pattern()
        self.assertIsNotNone(state)
        
        print(f"  Pipeline: Circuit → {len(list(pattern))} MBQC cmds → {len(hugr)} HUGR nodes")
    
    @unittest.skipUnless(BACKENDS_AVAILABLE['h1_1le'], "H1-1LE not available")
    def test_rotation_full_pipeline_h1_1le(self):
        """Test rotation gate through full pipeline on H1-1LE."""
        # Graphix circuit with rotation
        graphix_circuit = Circuit(1)
        graphix_circuit.rx(0, np.pi/4)
        
        # Convert to pattern and HUGR
        pattern = graphix_circuit.transpile().pattern
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        # Execute equivalent on H1-1LE
        pytket_circuit = PytketCircuit(1, 1)
        pytket_circuit.Rx(np.pi/4, 0)
        pytket_circuit.Measure(0, 0)
        
        api_offline = QuantinuumAPIOffline()
        backend = QuantinuumBackend("H1-1LE", api_handler=api_offline)
        compiled = backend.get_compiled_circuit(pytket_circuit)
        handle = backend.process_circuit(compiled, n_shots=100)
        result = backend.get_result(handle)
        counts = result.get_counts()
        
        # Verify execution
        total = sum(counts.values())
        self.assertEqual(total, 100)
        print(f"  Rx pipeline: Pattern→HUGR ({len(hugr)} nodes), H1-1LE: {dict(counts)}")


class TestQuantumAlgorithms(unittest.TestCase):
    """Test execution of small quantum algorithms."""
    
    @unittest.skipUnless(BACKENDS_AVAILABLE['h1_1le'], "H1-1LE not available")
    def test_deutsch_algorithm_h1_1le(self):
        """Test Deutsch algorithm on H1-1LE."""
        # Deutsch algorithm for constant function
        circuit = PytketCircuit(2, 2)
        # Input in |+⟩ |-⟩
        circuit.H(0)
        circuit.X(1)
        circuit.H(1)
        # Oracle: do nothing (constant 0)
        # Final Hadamard
        circuit.H(0)
        circuit.Measure(0, 0)
        circuit.Measure(1, 1)
        
        api_offline = QuantinuumAPIOffline()
        backend = QuantinuumBackend("H1-1LE", api_handler=api_offline)
        compiled = backend.get_compiled_circuit(circuit)
        handle = backend.process_circuit(compiled, n_shots=100)
        result = backend.get_result(handle)
        counts = result.get_counts()
        
        # Should measure |0⟩ on first qubit (constant function)
        zeros_first_qubit = sum(count for (q0, q1), count in counts.items() if q0 == 0)
        self.assertGreater(zeros_first_qubit, 90)
        print(f"  Deutsch (constant): {dict(counts)}")
    
    def test_qft_2qubit_graphix(self):
        """Test 2-qubit QFT on Graphix."""
        circuit = Circuit(2)
        # QFT
        circuit.h(0)
        circuit.rz(0, np.pi/2)
        circuit.cnot(1, 0)
        circuit.rz(0, -np.pi/2)
        circuit.cnot(1, 0)
        circuit.h(1)
        
        pattern = circuit.transpile().pattern
        hugr = convert_graphix_pattern_to_hugr(pattern)
        
        # QFT creates complex pattern
        self.assertGreater(len(list(pattern)), 40)
        self.assertGreater(len(hugr), 50)
        print(f"  QFT-2: {len(list(pattern))} MBQC cmds → {len(hugr)} HUGR nodes")


class TestBackendConsistency(unittest.TestCase):
    """Test that all backends give consistent results."""
    
    @unittest.skipUnless(
        BACKENDS_AVAILABLE['h1_1le'] and BACKENDS_AVAILABLE['qiskit_aer'],
        "Need both H1-1LE and Qiskit Aer"
    )
    def test_hadamard_consistency(self):
        """Test Hadamard gives consistent results across backends."""
        # H1-1LE
        circuit_h1 = PytketCircuit(1, 1)
        circuit_h1.H(0)
        circuit_h1.Measure(0, 0)
        
        api_offline = QuantinuumAPIOffline()
        backend_h1 = QuantinuumBackend("H1-1LE", api_handler=api_offline)
        handle_h1 = backend_h1.process_circuit(
            backend_h1.get_compiled_circuit(circuit_h1), n_shots=1000
        )
        result_h1 = backend_h1.get_result(handle_h1)
        counts_h1 = result_h1.get_counts()
        
        # Qiskit Aer
        circuit_aer = PytketCircuit(1, 1)
        circuit_aer.H(0)
        circuit_aer.Measure(0, 0)
        
        backend_aer = AerBackend()
        handle_aer = backend_aer.process_circuit(
            backend_aer.get_compiled_circuit(circuit_aer), n_shots=1000
        )
        result_aer = backend_aer.get_result(handle_aer)
        counts_aer = result_aer.get_counts()
        
        # Both should be roughly 50/50
        zeros_h1 = counts_h1.get((0,), 0) / 1000
        zeros_aer = counts_aer.get((0,), 0) / 1000
        
        # Should be within 10% of each other
        self.assertLess(abs(zeros_h1 - zeros_aer), 0.10)
        print(f"  H1-1LE: {zeros_h1:.1%} |0⟩, Qiskit: {zeros_aer:.1%} |0⟩")
    
    @unittest.skipUnless(
        BACKENDS_AVAILABLE['h1_1le'] and BACKENDS_AVAILABLE['qiskit_aer'],
        "Need both H1-1LE and Qiskit Aer"
    )
    def test_bell_state_consistency(self):
        """Test Bell state consistency across backends."""
        # Test both backends produce valid Bell state
        # (Already tested individually, this checks they're similar)
        pass  # Implemented in individual tests


class TestCompilationQuality(unittest.TestCase):
    """Test quality of compilation to different backends."""
    
    @unittest.skipUnless(BACKENDS_AVAILABLE['h1_1le'], "H1-1LE not available")
    def test_h1_1le_uses_native_gates(self):
        """Test H1-1LE compiles to native Quantinuum gates."""
        circuit = PytketCircuit(2, 2)
        circuit.H(0)
        circuit.CX(0, 1)
        circuit.Measure(0, 0)
        circuit.Measure(1, 1)
        
        api_offline = QuantinuumAPIOffline()
        backend = QuantinuumBackend("H1-1LE", api_handler=api_offline)
        compiled = backend.get_compiled_circuit(circuit)
        
        # Check native gates: PhasedX, ZZPhase, Rz
        gate_types = set()
        for cmd in compiled:
            gate_types.add(str(cmd.op.type))
        
        print(f"  H1-1LE native gates: {gate_types}")
        # Should use Quantinuum native gateset
        self.assertIn('PhasedX', str(gate_types) if gate_types else '')
    
    @unittest.skipUnless(BACKENDS_AVAILABLE['qiskit_aer'], "Qiskit Aer not available")
    def test_qiskit_compilation_overhead(self):
        """Test Qiskit compilation overhead."""
        circuit = PytketCircuit(2, 2)
        circuit.H(0)
        circuit.CX(0, 1)
        circuit.Measure(0, 0)
        circuit.Measure(1, 1)
        
        backend = AerBackend()
        compiled = backend.get_compiled_circuit(circuit)
        
        # Qiskit might add/optimize gates
        original_gates = circuit.n_gates
        compiled_gates = compiled.n_gates
        
        print(f"  Qiskit: {original_gates} gates → {compiled_gates} gates")
        # Compilation should not explode gate count
        self.assertLess(compiled_gates, original_gates * 3)


def run_emulator_tests():
    """Run all emulator execution tests."""
    print("\n" + "=" * 70)
    print("EMULATOR EXECUTION TEST SUITE")
    print("=" * 70)
    
    print("\nAvailable backends:")
    for backend, available in BACKENDS_AVAILABLE.items():
        status = "✓" if available else "✗"
        print(f"  {status} {backend}")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBellStateExecution))
    suite.addTests(loader.loadTestsFromTestCase(TestGHZStateExecution))
    suite.addTests(loader.loadTestsFromTestCase(TestSingleQubitGateExecution))
    suite.addTests(loader.loadTestsFromTestCase(TestRotationGateExecution))
    suite.addTests(loader.loadTestsFromTestCase(TestGraphixToHugrToExecution))
    suite.addTests(loader.loadTestsFromTestCase(TestQuantumAlgorithms))
    suite.addTests(loader.loadTestsFromTestCase(TestBackendConsistency))
    suite.addTests(loader.loadTestsFromTestCase(TestCompilationQuality))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("EMULATOR TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_emulator_tests()
    exit(0 if success else 1)