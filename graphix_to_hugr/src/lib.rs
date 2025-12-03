pub mod converter;
pub mod hugr;
pub mod types;

pub use converter::{convert_graphix_pattern_to_hugr, ConversionError, GraphixToHugrConverter};
pub use hugr::{ConstValue, DfgBuilder, FunctionType, Hugr, HugrType, Node, Operation, Wire};
pub use types::{CliffordGate, Command, CommandKind, Pattern, Plane};

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashSet;

    #[test]
    fn test_simple_prepare() {
        let mut pattern = Pattern::new(vec![], vec![0]);
        pattern.add_command(Command::N { node: 0 });
        
        let result = convert_graphix_pattern_to_hugr(&pattern);
        assert!(result.is_ok());
        
        let hugr = result.unwrap();
        assert!(hugr.len() > 0);
    }
    
    #[test]
    fn test_prepare_and_measure() {
        let mut pattern = Pattern::new(vec![], vec![]);
        pattern.add_command(Command::N { node: 0 });
        pattern.add_command(Command::M {
            node: 0,
            plane: Plane::XY,
            angle: 0.0,
        });
        
        let result = convert_graphix_pattern_to_hugr(&pattern);
        assert!(result.is_ok());
    }
    
    #[test]
    fn test_entanglement() {
        let mut pattern = Pattern::new(vec![], vec![0, 1]);
        pattern.add_command(Command::N { node: 0 });
        pattern.add_command(Command::N { node: 1 });
        pattern.add_command(Command::E { nodes: (0, 1) });
        
        let result = convert_graphix_pattern_to_hugr(&pattern);
        assert!(result.is_ok());
    }
    
    #[test]
    fn test_clifford_gates() {
        let mut pattern = Pattern::new(vec![0], vec![0]);
        pattern.add_command(Command::C {
            node: 0,
            clifford: vec![CliffordGate::H, CliffordGate::S],
        });
        
        let result = convert_graphix_pattern_to_hugr(&pattern);
        assert!(result.is_ok());
    }
    
    #[test]
    fn test_pauli_corrections() {
        let mut pattern = Pattern::new(vec![0], vec![0]);
        
        // Measure a node
        pattern.add_command(Command::N { node: 1 });
        pattern.add_command(Command::M {
            node: 1,
            plane: Plane::XY,
            angle: 0.0,
        });
        
        // Apply X correction based on measurement
        let mut domain = HashSet::new();
        domain.insert(1);
        pattern.add_command(Command::X { node: 0, domain });
        
        let result = convert_graphix_pattern_to_hugr(&pattern);
        assert!(result.is_ok());
    }
}