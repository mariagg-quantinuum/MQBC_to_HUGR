use graphix_to_hugr::{
    convert_graphix_pattern_to_hugr, CliffordGate, Command, Pattern, Plane,
};
use std::collections::HashSet;

fn main() {
    println!("Graphix to HUGR Converter - Rust Edition");
    println!("{}", "=".repeat(50));

    // Example 1: Simple qubit preparation
    println!("\nExample 1: Prepare a qubit");
    let mut pattern1 = Pattern::new(vec![], vec![0]);
    pattern1.add_command(Command::N { node: 0 });
    
    match convert_graphix_pattern_to_hugr(&pattern1) {
        Ok(hugr) => println!("✓ Successfully converted! HUGR nodes: {}", hugr.len()),
        Err(e) => println!("✗ Error: {}", e),
    }

    // Example 2: Entanglement
    println!("\nExample 2: Create entangled pair");
    let mut pattern2 = Pattern::new(vec![], vec![0, 1]);
    pattern2.add_command(Command::N { node: 0 });
    pattern2.add_command(Command::N { node: 1 });
    pattern2.add_command(Command::E { nodes: (0, 1) });
    
    match convert_graphix_pattern_to_hugr(&pattern2) {
        Ok(hugr) => println!("✓ Successfully converted! HUGR nodes: {}", hugr.len()),
        Err(e) => println!("✗ Error: {}", e),
    }

    // Example 3: Measurement in different bases
    println!("\nExample 3: Measure in XY plane");
    let mut pattern3 = Pattern::new(vec![], vec![]);
    pattern3.add_command(Command::N { node: 0 });
    pattern3.add_command(Command::M {
        node: 0,
        plane: Plane::XY,
        angle: std::f64::consts::PI / 4.0,
    });
    
    match convert_graphix_pattern_to_hugr(&pattern3) {
        Ok(hugr) => println!("✓ Successfully converted! HUGR nodes: {}", hugr.len()),
        Err(e) => println!("✗ Error: {}", e),
    }

    // Example 4: Clifford gates
    println!("\nExample 4: Apply Clifford gates (H, S)");
    let mut pattern4 = Pattern::new(vec![0], vec![0]);
    pattern4.add_command(Command::C {
        node: 0,
        clifford: vec![CliffordGate::H, CliffordGate::S],
    });
    
    match convert_graphix_pattern_to_hugr(&pattern4) {
        Ok(hugr) => println!("✓ Successfully converted! HUGR nodes: {}", hugr.len()),
        Err(e) => println!("✗ Error: {}", e),
    }

    // Example 5: Measurement-based corrections
    println!("\nExample 5: Measurement-based X correction");
    let mut pattern5 = Pattern::new(vec![0], vec![0]);
    
    // Prepare ancilla and measure
    pattern5.add_command(Command::N { node: 1 });
    pattern5.add_command(Command::M {
        node: 1,
        plane: Plane::XY,
        angle: 0.0,
    });
    
    // Apply X correction based on measurement
    let mut domain = HashSet::new();
    domain.insert(1);
    pattern5.add_command(Command::X { node: 0, domain });
    
    match convert_graphix_pattern_to_hugr(&pattern5) {
        Ok(hugr) => println!("✓ Successfully converted! HUGR nodes: {}", hugr.len()),
        Err(e) => println!("✗ Error: {}", e),
    }

    // Example 6: Bell state preparation pattern
    println!("\nExample 6: Bell state preparation pattern");
    let mut pattern6 = Pattern::new(vec![0, 1], vec![0, 1]);
    
    // Apply Hadamard on first qubit
    pattern6.add_command(Command::C {
        node: 0,
        clifford: vec![CliffordGate::H],
    });
    
    // Entangle the qubits with CZ
    pattern6.add_command(Command::E { nodes: (0, 1) });
    
    match convert_graphix_pattern_to_hugr(&pattern6) {
        Ok(hugr) => println!("✓ Successfully converted! HUGR nodes: {}", hugr.len()),
        Err(e) => println!("✗ Error: {}", e),
    }

    println!("\n{}", "=".repeat(50));
    println!("All examples completed!");
}