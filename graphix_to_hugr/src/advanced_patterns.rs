use graphix_to_hugr::{
    convert_graphix_pattern_to_hugr, CliffordGate, Command, Pattern, Plane,
};
use std::collections::HashSet;

fn main() {
    println!("Advanced Graphix to HUGR Examples");
    println!("{}", "=".repeat(60));

    // Example 1: Bell State Preparation and Measurement
    bell_state_example();
    
    // Example 2: Quantum Teleportation Pattern
    teleportation_example();
    
    // Example 3: Complex measurement-based computation
    mbqc_computation_example();
    
    // Example 4: Cluster state generation
    cluster_state_example();
    
    println!("\n{}", "=".repeat(60));
    println!("All advanced examples completed!");
}

/// Example: Bell state preparation using MBQC pattern
fn bell_state_example() {
    println!("\n--- Bell State Preparation ---");
    
    // Create pattern with 2 input qubits
    let mut pattern = Pattern::new(vec![0, 1], vec![0, 1]);
    
    // Apply Hadamard on first qubit (using Clifford command)
    pattern.add_command(Command::C {
        node: 0,
        clifford: vec![CliffordGate::H],
    });
    
    // Entangle with CZ gate
    pattern.add_command(Command::E { nodes: (0, 1) });
    
    // Convert and print results
    match convert_graphix_pattern_to_hugr(&pattern) {
        Ok(hugr) => {
            println!("✓ Bell state pattern converted");
            println!("  HUGR nodes: {}", hugr.len());
            println!("  Input qubits: 2, Output qubits: 2");
        }
        Err(e) => println!("✗ Error: {}", e),
    }
}

/// Example: Quantum teleportation using MBQC
fn teleportation_example() {
    println!("\n--- Quantum Teleportation Pattern ---");
    
    // Pattern with 3 qubits: 0=state to teleport, 1=ancilla, 2=target
    let mut pattern = Pattern::new(vec![0], vec![2]);
    
    // Prepare ancilla qubits for Bell pair
    pattern.add_command(Command::N { node: 1 });
    pattern.add_command(Command::N { node: 2 });
    
    // Create Bell pair between ancilla (1) and target (2)
    pattern.add_command(Command::C {
        node: 1,
        clifford: vec![CliffordGate::H],
    });
    pattern.add_command(Command::E { nodes: (1, 2) });
    
    // Entangle state (0) with ancilla (1)
    pattern.add_command(Command::E { nodes: (0, 1) });
    
    // Apply Hadamard to state qubit
    pattern.add_command(Command::C {
        node: 0,
        clifford: vec![CliffordGate::H],
    });
    
    // Measure state qubit and ancilla
    pattern.add_command(Command::M {
        node: 0,
        plane: Plane::XY,
        angle: 0.0,
    });
    pattern.add_command(Command::M {
        node: 1,
        plane: Plane::XY,
        angle: 0.0,
    });
    
    // Apply corrections to target based on measurements
    let mut x_domain = HashSet::new();
    x_domain.insert(1);
    pattern.add_command(Command::X {
        node: 2,
        domain: x_domain,
    });
    
    let mut z_domain = HashSet::new();
    z_domain.insert(0);
    pattern.add_command(Command::Z {
        node: 2,
        domain: z_domain,
    });
    
    match convert_graphix_pattern_to_hugr(&pattern) {
        Ok(hugr) => {
            println!("✓ Teleportation pattern converted");
            println!("  HUGR nodes: {}", hugr.len());
            println!("  Demonstrates: Bell pair, entanglement, measurements, corrections");
        }
        Err(e) => println!("✗ Error: {}", e),
    }
}

/// Example: MBQC computation with multiple measurements
fn mbqc_computation_example() {
    println!("\n--- MBQC Computation Pattern ---");
    
    // Create a pattern representing computation on a graph state
    let mut pattern = Pattern::new(vec![0], vec![4]);
    
    // Build a graph state
    pattern.add_command(Command::N { node: 1 });
    pattern.add_command(Command::N { node: 2 });
    pattern.add_command(Command::N { node: 3 });
    pattern.add_command(Command::N { node: 4 });
    
    // Create graph edges
    pattern.add_command(Command::E { nodes: (0, 1) });
    pattern.add_command(Command::E { nodes: (1, 2) });
    pattern.add_command(Command::E { nodes: (2, 3) });
    pattern.add_command(Command::E { nodes: (3, 4) });
    
    // Measure intermediate nodes with different angles
    use std::f64::consts::PI;
    
    pattern.add_command(Command::M {
        node: 1,
        plane: Plane::XY,
        angle: PI / 4.0,
    });
    
    pattern.add_command(Command::M {
        node: 2,
        plane: Plane::XY,
        angle: PI / 8.0,
    });
    
    // Apply adaptive measurements (depend on previous outcomes)
    let mut z_domain = HashSet::new();
    z_domain.insert(1);
    pattern.add_command(Command::Z {
        node: 3,
        domain: z_domain,
    });
    
    pattern.add_command(Command::M {
        node: 3,
        plane: Plane::XY,
        angle: 0.0,
    });
    
    // Final corrections on output
    let mut final_x_domain = HashSet::new();
    final_x_domain.insert(2);
    final_x_domain.insert(3);
    pattern.add_command(Command::X {
        node: 4,
        domain: final_x_domain,
    });
    
    let mut final_z_domain = HashSet::new();
    final_z_domain.insert(1);
    pattern.add_command(Command::Z {
        node: 4,
        domain: final_z_domain,
    });
    
    match convert_graphix_pattern_to_hugr(&pattern) {
        Ok(hugr) => {
            println!("✓ MBQC computation pattern converted");
            println!("  HUGR nodes: {}", hugr.len());
            println!("  Features: Graph state, adaptive measurements, corrections");
        }
        Err(e) => println!("✗ Error: {}", e),
    }
}

/// Example: 2D cluster state generation
fn cluster_state_example() {
    println!("\n--- 2D Cluster State (3x3) ---");
    
    // Create a 3x3 cluster state pattern
    let mut pattern = Pattern::new(vec![], vec![0, 1, 2, 3, 4, 5, 6, 7, 8]);
    
    // Prepare all qubits
    for i in 0..9 {
        pattern.add_command(Command::N { node: i });
    }
    
    // Create horizontal edges
    for row in 0..3 {
        for col in 0..2 {
            let node1 = row * 3 + col;
            let node2 = row * 3 + col + 1;
            pattern.add_command(Command::E {
                nodes: (node1, node2),
            });
        }
    }
    
    // Create vertical edges
    for row in 0..2 {
        for col in 0..3 {
            let node1 = row * 3 + col;
            let node2 = (row + 1) * 3 + col;
            pattern.add_command(Command::E {
                nodes: (node1, node2),
            });
        }
    }
    
    match convert_graphix_pattern_to_hugr(&pattern) {
        Ok(hugr) => {
            println!("✓ 2D cluster state pattern converted");
            println!("  HUGR nodes: {}", hugr.len());
            println!("  Grid size: 3x3 (9 qubits)");
            println!("  Edges: 12 (horizontal + vertical)");
        }
        Err(e) => println!("✗ Error: {}", e),
    }
}