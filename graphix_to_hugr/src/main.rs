use graphix_to_hugr::{
    convert_graphix_pattern_to_hugr, CliffordGate, Command, Pattern, Plane,
};
use std::collections::HashSet;

fn main() {
    println!("Graphix to HUGR Converter Examples\n");
    println!("{}", "=".repeat(60));

    // Example 1: Simple qubit preparation
    example_1_simple_prepare();
    
    // Example 2: Bell state (entangled pair)
    example_2_bell_state();
    
    // Example 3: Measurement
    example_3_measurement();
    
    // Example 4: With corrections
    example_4_corrections();

    println!("\n{}", "=".repeat(60));
    println!("All examples completed successfully!");
}

/// Example 1: Prepare a single qubit
fn example_1_simple_prepare() {
    println!("\n Example 1: Simple Qubit Preparation");
    println!("{}", "-".repeat(60));
    
    // Create a pattern with no inputs, one output (node 0)
    let mut pattern = Pattern::new(vec![], vec![0]);
    
    // Prepare qubit at node 0 in |+⟩ state
    pattern.add_command(Command::N { node: 0 });
    
    // Convert to HUGR
    match convert_graphix_pattern_to_hugr(&pattern) {
        Ok(hugr) => {
            println!("✓ Successfully converted!");
            println!("  Pattern: Prepare 1 qubit");
            println!("  HUGR has {} nodes", hugr.len());
        }
        Err(e) => {
            eprintln!("✗ Conversion failed: {}", e);
        }
    }
}

/// Example 2: Create a Bell state (maximally entangled pair)
fn example_2_bell_state() {
    println!("\n Example 2: Bell State (Entangled Pair)");
    println!("{}", "-".repeat(60));
    
    // Create pattern with 2 input qubits, 2 output qubits
    let mut pattern = Pattern::new(vec![0, 1], vec![0, 1]);
    
    // Apply Hadamard to first qubit
    pattern.add_command(Command::C {
        node: 0,
        clifford: vec![CliffordGate::H],
    });
    
    // Entangle the two qubits with CZ gate
    pattern.add_command(Command::E { nodes: (0, 1) });
    
    // Convert to HUGR
    match convert_graphix_pattern_to_hugr(&pattern) {
        Ok(hugr) => {
            println!("✓ Successfully converted!");
            println!("  Pattern: H(q0) → CZ(q0, q1)");
            println!("  HUGR has {} nodes", hugr.len());
            println!("  Result: Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2");
        }
        Err(e) => {
            eprintln!("✗ Conversion failed: {}", e);
        }
    }
}

/// Example 3: Measure a qubit in different bases
fn example_3_measurement() {
    println!("\n Example 3: Measurement in XY Plane");
    println!("{}", "-".repeat(60));
    
    use std::f64::consts::PI;
    
    // Create pattern with 1 input, no outputs (qubit gets measured)
    let mut pattern = Pattern::new(vec![0], vec![]);
    
    // Measure qubit 0 in XY plane at angle π/4
    pattern.add_command(Command::M {
        node: 0,
        plane: Plane::XY,
        angle: PI / 4.0,
    });
    
    // Convert to HUGR
    match convert_graphix_pattern_to_hugr(&pattern) {
        Ok(hugr) => {
            println!("✓ Successfully converted!");
            println!("  Pattern: Measure q0 in XY plane at π/4");
            println!("  HUGR has {} nodes", hugr.len());
            println!("  Result: Classical measurement outcome");
        }
        Err(e) => {
            eprintln!("✗ Conversion failed: {}", e);
        }
    }
}

/// Example 4: Measurement-based quantum computation with corrections
fn example_4_corrections() {
    println!("\n Example 4: MBQC with Corrections");
    println!("{}", "-".repeat(60));
    
    // Create pattern: 1 input qubit, 1 output qubit
    let mut pattern = Pattern::new(vec![0], vec![0]);
    
    // Prepare ancilla qubit
    pattern.add_command(Command::N { node: 1 });
    
    // Entangle input with ancilla
    pattern.add_command(Command::E { nodes: (0, 1) });
    
    // Measure ancilla
    pattern.add_command(Command::M {
        node: 1,
        plane: Plane::XY,
        angle: 0.0,
    });
    
    // Apply X correction to output based on measurement of node 1
    let mut x_domain = HashSet::new();
    x_domain.insert(1);
    pattern.add_command(Command::X {
        node: 0,
        domain: x_domain,
    });
    
    // Apply Z correction
    let mut z_domain = HashSet::new();
    z_domain.insert(1);
    pattern.add_command(Command::Z {
        node: 0,
        domain: z_domain,
    });
    
    // Convert to HUGR
    match convert_graphix_pattern_to_hugr(&pattern) {
        Ok(hugr) => {
            println!("✓ Successfully converted!");
            println!("  Pattern: MBQC with measurement-based corrections");
            println!("  Steps:");
            println!("    1. Prepare ancilla qubit");
            println!("    2. Entangle input with ancilla");
            println!("    3. Measure ancilla");
            println!("    4. Apply corrections based on measurement");
            println!("  HUGR has {} nodes", hugr.len());
        }
        Err(e) => {
            eprintln!("✗ Conversion failed: {}", e);
        }
    }
}