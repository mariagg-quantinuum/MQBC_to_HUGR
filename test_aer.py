#!/usr/bin/env python3
"""
Bell State Test with Qiskit Aer (WORKING ALTERNATIVE)

Since H1-1E has a bug, use Qiskit Aer instead.
"""

from pytket import Circuit

print("BELL STATE TEST - QISKIT AER SIMULATOR")
print("=" * 70)

# Create Bell state
circuit = Circuit(2, 2)
circuit.H(0)
circuit.CX(0, 1)
circuit.Measure(0, 0)
circuit.Measure(1, 1)

print(f"Circuit: {circuit.n_gates} gates")
print("Expected: ~50% (0,0), ~50% (1,1)\n")

try:
    from pytket.extensions.qiskit import AerBackend
    
    print("Using Qiskit Aer simulator...")
    backend = AerBackend()
    
    # Compile
    compiled = backend.get_compiled_circuit(circuit)
    print(f"Compiled: {compiled.n_gates} gates")
    
    # Execute
    print("\nExecuting 100 shots...")
    handle = backend.process_circuit(compiled, n_shots=100)
    result = backend.get_result(handle)
    counts = result.get_counts()
    
    # Display results
    print("\n" + "=" * 70)
    print("RESULTS:")
    print("=" * 70)
    
    total = sum(counts.values())
    for outcome, count in sorted(counts.items()):
        percentage = 100 * count / total
        bar = "█" * int(percentage / 2)
        print(f"  {outcome}: {count:3d} ({percentage:5.1f}%) {bar}")
    
    # Analysis
    zeros = counts.get((0, 0), 0)
    ones = counts.get((1, 1), 0)
    
    print("\n" + "=" * 70)
    print("ANALYSIS:")
    print("=" * 70)
    print(f"(0, 0): {zeros} ({100*zeros/total:.1f}%)")
    print(f"(1, 1): {ones} ({100*ones/total:.1f}%)")
    
    if 40 <= zeros <= 60 and 40 <= ones <= 60:
        print("\n✓ SUCCESS: Bell state working correctly!")
        print("  Qiskit Aer is executing the circuit properly.")
    else:
        print("\n⚠️  Unexpected distribution")
        
except ImportError:
    print("\n❌ Qiskit Aer not installed")
    print("\nInstall with:")
    print("  pip install pytket-qiskit qiskit-aer")
    print("\nOr with uv:")
    print("  uv pip install pytket-qiskit qiskit-aer")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("NOTE: H1-1E emulator has a bug returning all |00⟩")
print("Use Qiskit Aer or Graphix for testing instead!")
print("=" * 70)