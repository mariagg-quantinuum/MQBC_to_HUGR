# Graphix MBQC Pattern Converters

Three converters that translate (Graphix)[https://graphix.readthedocs.io/en/latest/] measurement-based quantum computation (MBQC) patterns into the Quantinuum software stack.

## What we have

| Converter | Target | Conditional Logic | Output Type |
|-----------|--------|-------------------|-------------|
| graphix_to_guppy | Guppy | Custom if-statements | String code / GuppyModule |
| graphix_to_hugr | HUGR | Custom ConditionalX/Z ops | HUGR dataflow graph |
| graphix_to_pytket | pytket | Native `condition` kwarg | pytket Circuit |

## Key Differences between translators

### Conditional Corrections

MBQC patterns require conditional Pauli corrections based on measurement outcomes (XOR of results). Each converter handles this differently:

Guppy: Generates explicit if-statements with XOR logic
```python
if m_0 ^ m_1:
    q_2 = x(q_2)
```

HUGR: Creates custom `ConditionalX` and `ConditionalZ` operations in the dataflow graph
```python
# Custom operation applies gate conditionally
cond_gate_op = ops.Custom(
    "ConditionalX",
    tys.FunctionType([tys.Bool, tys.Qubit], [tys.Qubit]),
    extension=QUANTUM_EXTENSION
)
```

pytket: Uses pytket's built-in conditional system
```python
# Native pytket conditional expression
condition = reg_eq(bit_0 ^ bit_1, 1)
circuit.X(qubit, condition=condition)
```

## Usage Examples

### Graphix to Guppy

```python
from graphix import Circuit
from graphix_to_guppy import convert_graphix_pattern_to_guppy

# Create and transpile circuit
circuit = Circuit(1)
circuit.h(0)
pattern = circuit.transpile().pattern

# Convert to Guppy code
guppy_code = convert_graphix_pattern_to_guppy(pattern)
print(guppy_code)
```

Output: Python code string with `@guppy` decorator
```python
from guppy import guppy
from guppy.prelude.quantum import qubit, measure, h, x, z, ...

@guppy
def quantum_circuit(q_in_0: qubit) -> qubit:
    q_0 = qubit()
    q_0 = h(q_0)
    q_0, q_in_0 = cz(q_0, q_in_0)
    m_0 = measure(q_0)
    if m_0:
        q_in_0 = z(q_in_0)
    return q_in_0
```

### Graphix to HUGR

```python
from graphix_to_hugr import convert_graphix_pattern_to_hugr

# Convert to HUGR dataflow graph
hugr = convert_graphix_pattern_to_hugr(pattern)
print(f"HUGR nodes: {len(hugr)}")
```

Output: HUGR dataflow graph with custom quantum operations
- Uses `PrepareQubit`, `CZ`, `Measure`, `ConditionalX`, `ConditionalZ` ops
- Dataflow representation with explicit wire dependencies
- Suitable for optimization and hardware compilation

### Graphix to pytket

```python
from graphix_to_pytket import convert_graphix_pattern_to_pytket

# Convert to pytket Circuit
pytket_circuit = convert_graphix_pattern_to_pytket(pattern)
print(f"Gates: {pytket_circuit.n_gates}")
print(pytket_circuit.get_commands())
```

Output: pytket Circuit with conditional gates
```python
# Pseudo-circuit representation
H q[0];
CZ q[0], q[1];
Measure q[0] -> m[0];
if (m[0] == 1) Z q[1];  # Using pytket's condition system
```

## Implementation Details

### Measurement Basis Conversion

All three converters handle arbitrary measurement angles by:
1. Applying basis rotation gates (Rz, Rx, Ry)
2. Measuring in computational (Z) basis

Example (XY-plane measurement at angle θ):
```python
# All converters do:
Rz(-θ)
H
Measure → m
```

### Clifford Gates

Clifford operations decompose into H, S, and Pauli gates using standard 24-element decomposition tables:
- Identity: `[]`
- S gate: `['S']`
- Z gate: `['S', 'S']`
- Hadamard: `['H']`
- ...and 20 more combinations

### Qubit Preparation

- Guppy: Allocates qubit in |0⟩, applies H
- HUGR: Custom `PrepareQubit` operation
- pytket: Uses existing qubit register, applies H

## Dependencies

```bash
pip install graphix guppy hugr pytket
```
---

## Rust Implementation

The repository includes a Rust implementation alongside the Python converters.

### What It Does

The Rust implementation provides a native rust hugr crate converter from MBQC patterns to HUGR.

### Module Structure

`lib.rs` - Main library exports and integration tests
```rust
pub use converter::convert_graphix_pattern_to_hugr;
pub use types::{Pattern, Command, Plane, CliffordGate};
```

`types.rs` - MBQC pattern data structures
- `Pattern`: Represents Graphix MBQC patterns with input/output nodes
- `Command`: Enum for N, E, M, X, Z, C operations
- `Plane`: XY, YZ, XZ measurement planes
- `CliffordGate`: Single-qubit Clifford elements

`converter.rs` - Core conversion logic 
- `GraphixToHugrConverter`: Stateful converter tracking qubits and classical bits
- Processes commands sequentially, building dataflow graph
- Implements conditional operations with XOR logic
- Creates custom quantum operations (PrepareQubit, CZ, ConditionalX/Z)

`hugr.rs` - HUGR construction utilities
- `DfgBuilder`: Dataflow graph builder
- `Wire`, `Node`, `Operation` types
- Manages HUGR node creation and wire connections

`main.rs` - Command-line interface with 4 examples:
1. Simple qubit preparation
2. Bell state creation
3. Measurement in different planes
4. MBQC with corrections

`basic_usage.rs` - 6 introductory examples showing:
- Qubit preparation, entanglement, measurements
- Clifford gates, conditional corrections
- Bell state patterns

`advanced_patterns.rs` - Complex examples:
- Quantum teleportation
- 2D cluster states (3×3 grid)
- Adaptive MBQC computation
- Multi-qubit graph states

### Usage Example

```rust
use graphix_to_hugr::{Pattern, Command, CliffordGate, convert_graphix_pattern_to_hugr};

// Create Bell state pattern
let mut pattern = Pattern::new(vec![0, 1], vec![0, 1]);
pattern.add_command(Command::C {
    node: 0,
    clifford: vec![CliffordGate::H],
});
pattern.add_command(Command::E { nodes: (0, 1) });

// Convert to HUGR
match convert_graphix_pattern_to_hugr(&pattern) {
    Ok(hugr) => println!("HUGR nodes: {}", hugr.len()),
    Err(e) => eprintln!("Error: {}", e),
}
```

---

## NEXUS Runs

### `mbqc_vqe_nexus.ipynb` - VQE on Quantinuum Hardware

MBQC copy of the Variational Quantum Eigensolver (VQE) workflow Nexus example, using Quantinuum's H2 simulator:

Pipeline:
```
Ansatz Circuit → Graphix MBQC → Guppy Code → HUGR → Quantinuum H2
```

Key Features:
- Converts gate-based VQE ansatz to MBQC using Graphix
- Generates Guppy quantum code from MBQC patterns
- Compiles to HUGR for Quantinuum execution
- Uses Nexus to track VQE parameters (angles, energies)
- Implements context management for resuming interrupted workflows
- Calculates H₂ ground state energy with parameterized circuits

---

## Available Notebook Examples for each converter

### `main.ipynb`

Quick start guide covering:
- Basic converter usage for all three targets
- Simple circuit examples (1-2 qubits)
- Pattern inspection and visualization
- HUGR structure examination
- Error handling and debugging tips

### `examples_execution_to_hugr.ipynb`

Execution demonstrations on multiple backends:

Method 1: Graphix Built-in Simulator
- Runs MBQC patterns directly
- Bell states, GHZ states, rotation gates
- Measurement sampling and statistics

Method 2: Quantinuum H1-1E Emulator
- Local emulation of Quantinuum hardware
- pytket integration examples
- Circuit compilation and execution

Method 3: Qiskit Aer Simulator
- General-purpose quantum simulation
- Conversion from MBQC to gate-based
- Comparative results

Shows: How HUGR circuits execute on real simulators with statistical analysis of outcomes

### `guppy_examples.ipynb`

Tutorial on Graphix → Guppy conversion:
- Single-qubit gates (H, X, Y, Z, S, Rz)
- Two-qubit gates (CNOT, CZ)
- Multi-qubit circuits (Bell states, GHZ states)
- Conditional corrections in MBQC (measurement-dependent Pauli gates)
- Code structure analysis (function signatures, type annotations)
- Shows generated Guppy code with explanations

### `comparison_notebook.ipynb`

Side-by-side comparison of three converters:
- Guppy approach: `if` statements for conditionals
- pytket approach: Native `condition` argument
- HUGR approach: Custom `ConditionalX/Z` operations

Compares:
- Code generation strategies
- Conditional logic implementation
- Output formats and structure
- Performance characteristics

Example circuits: Hadamard, CNOT, rotation gates with adaptive corrections

---

## Tests

Run the complete test suite with coverage analysis:

```bash
coverage run tests.py
```

### Test Files

`hugr_tests.py` - HUGR Conversion Tests (644 lines)
- TestBasicConversion: HUGR structure validation
- TestSingleQubitGates: H, X, Y, Z, S, T gates
- TestTwoQubitGates: CNOT, CZ, SWAP
- TestRotationGates: Rx, Ry, Rz with various angles
- TestMultiQubitCircuits: Bell, GHZ, W states
- TestPatternCommands: N, E, M, X, Z, C commands
- TestMeasurementPlanes: XY, YZ, XZ plane measurements
- TestInputOutputMapping: Qubit tracking across conversions
- TestEdgeCases: Empty patterns, single operations
- TestConverterState: State management, wire tracking
- TestComplexCircuits: QFT, teleportation, cluster states
- TestHugrStructure: Node count, entrypoint, type system

Run specific test classes:
```bash
python -m unittest hugr_tests.TestRotationGates
```

`guppy_tests.py` - Guppy Code Generation Tests (533 lines)
- TestSingleQubitGateConversion: Code structure for basic gates
- TestRotationGateConversion: Parameterized gate handling
- TestTwoQubitGateConversion: Multi-qubit operations
- TestMultiQubitCircuits: Complex entangled states
- TestCodeStructure: Function signatures, imports, type annotations
- TestVariableManagement: Qubit variable naming, classical bits
- TestEdgeCases: Boundary conditions, error handling
- TestGuppyCompilation: Actual Guppy module compilation (if Guppy installed)
- TestComparisonWithHUGR: Verify consistency between converters

`emulator_tests.py` - Hardware Simulation Tests
- TestBellStateExecution: Bell state fidelity on multiple backends
- TestSingleQubitGateExecution: Hadamard superposition, X flip, S gate
- TestRotationGateExecution: Rx, Ry rotation accuracy

Backends tested:
- ✓ Graphix simulator (always available)
- ✓ H1-1LE emulator (if pytket-quantinuum installed)
- ✓ Qiskit Aer (if pytket-qiskit installed)

`test_h1.py` - Quantinuum H1-1LE Quick Test
- Minimal Bell state test on local H1-1LE emulator
- Verifies pytket-quantinuum integration
- Checks for 50/50 |00⟩/|11⟩ distribution

`test_aer.py` - Qiskit Aer Quick Test
- Bell state on Qiskit Aer backend
- Alternative when H1-1LE unavailable
- Statistical validation of entanglement

`tests.py` - Master Test Runner
- Aggregates all test suites
- Provides test filtering options:
  ```bash
  python tests.py --conversion-only  # Just HUGR/Guppy conversion
  python tests.py --emulator-only    # Just execution tests
  python tests.py -v 2               # Verbose output
  ```
- Generates summary statistics
- Shows backend availability

---

## Dependencies

```bash
pip install graphix guppy hugr pytket pytket-quantinuum pytket-qiskit qiskit-aer
```

Core:
- `graphix` - MBQC pattern library
- `hugr` - Hierarchical Unified Graph Representation
- `numpy` - Numerical computations

Converters:
- `guppy` (optional) - Guppy quantum language
- `pytket` (optional) - Cambridge Quantum toolkit

Execution:
- `pytket-quantinuum` (optional) - H1-1LE emulator
- `pytket-qiskit` (optional) - Qiskit integration
- `qiskit-aer` (optional) - Aer simulator

Testing:
- `coverage` - Code coverage analysis
- `unittest` - Python testing framework
