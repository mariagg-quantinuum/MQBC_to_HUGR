# Graphix MBQC Pattern Converters

Three converters that translate (Graphix)[https://graphix.readthedocs.io/en/latest/] measurement-based quantum computation (MBQC) patterns into the Quantinuum software stack.

## What we have

| Converter | Target | Conditional Logic | Output Type |
|-----------|--------|-------------------|-------------|
| **graphix_to_guppy** | Guppy | Custom if-statements | String code / GuppyModule |
| **graphix_to_hugr** | HUGR | Custom ConditionalX/Z ops | HUGR dataflow graph |
| **graphix_to_pytket** | pytket | Native `condition` kwarg | pytket Circuit |

## Key Differences between translators

### Conditional Corrections

MBQC patterns require conditional Pauli corrections based on measurement outcomes (XOR of results). Each converter handles this differently:

**Guppy**: Generates explicit if-statements with XOR logic
```python
if m_0 ^ m_1:
    q_2 = x(q_2)
```

**HUGR**: Creates custom `ConditionalX` and `ConditionalZ` operations in the dataflow graph
```python
# Custom operation applies gate conditionally
cond_gate_op = ops.Custom(
    "ConditionalX",
    tys.FunctionType([tys.Bool, tys.Qubit], [tys.Qubit]),
    extension=QUANTUM_EXTENSION
)
```

**pytket**: Uses pytket's built-in conditional system
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

**Output**: Python code string with `@guppy` decorator
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

**Output**: HUGR dataflow graph with custom quantum operations
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

**Output**: pytket Circuit with conditional gates
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

**Example** (XY-plane measurement at angle θ):
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

- **Guppy**: Allocates qubit in |0⟩, applies H
- **HUGR**: Custom `PrepareQubit` operation
- **pytket**: Uses existing qubit register, applies H

## Dependencies

```bash
pip install graphix guppy hugr pytket
```

## Rust implementation
talk about it - what does it do
difference with the python ones
what each doc does

## NEXUS runs
mbqc_vqe_nexus.py - runs on nexus h2 simulator!
made with the template vqe notebook 


## Available examples
other available notebook examples include (explain what they show a bit):

guppy_examples.ipynb
comparison_notebook.ipynb
main.ipynb
examples_execution_to_hugr.ipynb

## Tests
all these python files are tests - explain what they are testing and how they can be run with
```
coverage run tests.py
```
: 

test_aer - sim test
test_h1 - sim test
tests
emulator_tests
hugr_tests




