from pytket import Circuit
from pytket.extensions.quantinuum import QuantinuumBackend, QuantinuumAPIOffline

print("H1-1LE LOCAL EMULATOR TEST")
print("=" * 70)

circuit = Circuit(2, 2)
circuit.H(0)
circuit.CX(0, 1)
circuit.Measure(0, 0)
circuit.Measure(1, 1)

print("Initializing H1-1LE local emulator...")
api_offline = QuantinuumAPIOffline()
backend = QuantinuumBackend("H1-1LE", api_handler=api_offline)

compiled = backend.get_compiled_circuit(circuit)
print(f"Compiled: {compiled.n_gates} gates")

print("\nExecuting 100 shots...")
handle = backend.process_circuit(compiled, n_shots=100)
result = backend.get_result(handle)
counts = result.get_counts()

print("\nResults:")
for outcome, count in sorted(counts.items()):
    print(f"  {outcome}: {count}")

zeros = counts.get((0, 0), 0)
ones = counts.get((1, 1), 0)

if 40 <= zeros <= 60 and 40 <= ones <= 60:
    print("\n✓✓✓ SUCCESS! ✓✓✓")
    print("H1-1LE is working correctly!")
else:
    print(f"\n❌ Unexpected: {zeros}% |00⟩, {ones}% |11⟩")

