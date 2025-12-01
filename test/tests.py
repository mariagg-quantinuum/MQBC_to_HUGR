#!/usr/bin/env python3
"""
Complete Test Suite Runner

Runs all tests:
1. Conversion tests (Graphix → HUGR)
2. Emulator execution tests (H1-1LE, Qiskit Aer, Graphix)
"""

import sys
import unittest

# Import test modules
try:
    from test.hugr_tests import (
        TestBasicConversion, TestSingleQubitGates, TestTwoQubitGates,
        TestRotationGates, TestMultiQubitCircuits, TestPatternCommands,
        TestMeasurementPlanes, TestInputOutputMapping, TestEdgeCases,
        TestConverterState, TestComplexCircuits, TestHugrStructure
    )
    CONVERSION_TESTS_AVAILABLE = True
except ImportError:
    CONVERSION_TESTS_AVAILABLE = False
    print("⚠️  Conversion tests not found (test_graphix_to_hugr.py)")

try:
    from test.emulator_tests import (
        TestBellStateExecution, TestGHZStateExecution,
        TestSingleQubitGateExecution, TestRotationGateExecution,
        TestGraphixToHugrToExecution, TestQuantumAlgorithms,
        TestBackendConsistency, TestCompilationQuality,
        BACKENDS_AVAILABLE
    )
    EMULATOR_TESTS_AVAILABLE = True
except ImportError:
    EMULATOR_TESTS_AVAILABLE = False
    BACKENDS_AVAILABLE = {}
    print("⚠️  Emulator tests not found (test_emulator_execution.py)")


def run_all_tests(verbose=2):
    """Run complete test suite."""
    print("\n" + "=" * 70)
    print("COMPLETE TEST SUITE - GRAPHIX → HUGR → EXECUTION")
    print("=" * 70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add conversion tests
    if CONVERSION_TESTS_AVAILABLE:
        print("\n📦 Loading Conversion Tests (Graphix → HUGR)...")
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
        print("   ✓ Loaded 12 conversion test suites")
    else:
        print("\n⚠️  Conversion tests not available")
    
    # Add emulator tests
    if EMULATOR_TESTS_AVAILABLE:
        print("\n🖥️  Loading Emulator Execution Tests...")
        print("   Available backends:")
        for backend, available in BACKENDS_AVAILABLE.items():
            status = "✓" if available else "✗"
            print(f"     {status} {backend}")
        
        suite.addTests(loader.loadTestsFromTestCase(TestBellStateExecution))
        suite.addTests(loader.loadTestsFromTestCase(TestGHZStateExecution))
        suite.addTests(loader.loadTestsFromTestCase(TestSingleQubitGateExecution))
        suite.addTests(loader.loadTestsFromTestCase(TestRotationGateExecution))
        suite.addTests(loader.loadTestsFromTestCase(TestGraphixToHugrToExecution))
        suite.addTests(loader.loadTestsFromTestCase(TestQuantumAlgorithms))
        suite.addTests(loader.loadTestsFromTestCase(TestBackendConsistency))
        suite.addTests(loader.loadTestsFromTestCase(TestCompilationQuality))
        print("   ✓ Loaded 8 emulator test suites")
    else:
        print("\n⚠️  Emulator tests not available")
    
    if suite.countTestCases() == 0:
        print("\n❌ No tests loaded!")
        return False
    
    print(f"\n📊 Total tests to run: {suite.countTestCases()}")
    
    # Run tests
    print("\n" + "=" * 70)
    print("RUNNING TESTS")
    print("=" * 70 + "\n")
    
    runner = unittest.TextTestRunner(verbosity=verbose)
    result = runner.run(suite)
    
    # Print detailed summary
    print("\n" + "=" * 70)
    print("FINAL TEST SUMMARY")
    print("=" * 70)
    
    print(f"\nTests run:     {result.testsRun}")
    print(f"Successes:     {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures:      {len(result.failures)}")
    print(f"Errors:        {len(result.errors)}")
    print(f"Skipped:       {len(result.skipped)}")
    
    # Calculate success rate
    if result.testsRun > 0:
        success_rate = 100 * (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun
        print(f"\nSuccess rate:  {success_rate:.1f}%")
    
    # Show failures/errors if any
    if result.failures:
        print(f"\n⚠️  {len(result.failures)} FAILURES:")
        for test, traceback in result.failures[:3]:  # Show first 3
            print(f"   • {test}")
        if len(result.failures) > 3:
            print(f"   ... and {len(result.failures) - 3} more")
    
    if result.errors:
        print(f"\n❌ {len(result.errors)} ERRORS:")
        for test, traceback in result.errors[:3]:
            print(f"   • {test}")
        if len(result.errors) > 3:
            print(f"   ... and {len(result.errors) - 3} more")
    
    # Final verdict
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 70)
    
    return result.wasSuccessful()


def run_conversion_tests_only():
    """Run only conversion tests."""
    if not CONVERSION_TESTS_AVAILABLE:
        print("❌ Conversion tests not available")
        return False
    
    print("\n📦 Running Conversion Tests Only (Graphix → HUGR)")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
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
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_emulator_tests_only():
    """Run only emulator execution tests."""
    if not EMULATOR_TESTS_AVAILABLE:
        print("❌ Emulator tests not available")
        return False
    
    print("\n🖥️  Running Emulator Tests Only")
    print(f"Available backends: {[k for k, v in BACKENDS_AVAILABLE.items() if v]}")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestBellStateExecution))
    suite.addTests(loader.loadTestsFromTestCase(TestGHZStateExecution))
    suite.addTests(loader.loadTestsFromTestCase(TestSingleQubitGateExecution))
    suite.addTests(loader.loadTestsFromTestCase(TestRotationGateExecution))
    suite.addTests(loader.loadTestsFromTestCase(TestGraphixToHugrToExecution))
    suite.addTests(loader.loadTestsFromTestCase(TestQuantumAlgorithms))
    suite.addTests(loader.loadTestsFromTestCase(TestBackendConsistency))
    suite.addTests(loader.loadTestsFromTestCase(TestCompilationQuality))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Graphix → HUGR test suite')
    parser.add_argument('--conversion-only', action='store_true',
                       help='Run only conversion tests')
    parser.add_argument('--emulator-only', action='store_true',
                       help='Run only emulator tests')
    parser.add_argument('--verbose', '-v', type=int, default=2,
                       help='Verbosity level (0-2)')
    
    args = parser.parse_args()
    
    if args.conversion_only:
        success = run_conversion_tests_only()
    elif args.emulator_only:
        success = run_emulator_tests_only()
    else:
        success = run_all_tests(verbose=args.verbose)
    
    sys.exit(0 if success else 1)