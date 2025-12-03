use crate::hugr::{
    ConstValue, DfgBuilder, FunctionType, Hugr, HugrType, Operation, Wire,
};
use crate::types::{CliffordGate, Command, Pattern, Plane};
use std::collections::{HashMap, HashSet};
use thiserror::Error;

const QUANTUM_EXTENSION: &str = "quantum.mbqc";
const LOGIC_EXTENSION: &str = "logic";

#[derive(Error, Debug)]
pub enum ConversionError {
    #[error("Output node {0} not found in qubit wires")]
    OutputNodeNotFound(usize),
    
    #[error("Node {0} not found in wires")]
    NodeNotFound(usize),
    
}

pub struct GraphixToHugrConverter {
    dfg: Option<DfgBuilder>,
    qubit_wires: HashMap<usize, Wire>,
    classical_wires: HashMap<usize, Wire>,
    node_order: Vec<usize>,
}

impl GraphixToHugrConverter {
    pub fn new() -> Self {
        Self {
            dfg: None,
            qubit_wires: HashMap::new(),
            classical_wires: HashMap::new(),
            node_order: Vec::new(),
        }
    }
    
    /// Convert a Graphix Pattern to a HUGR
    pub fn convert(&mut self, pattern: &Pattern) -> Result<Hugr, ConversionError> {
        // Determine input and output qubits
        let input_nodes: Vec<usize> = {
            let mut nodes = pattern.input_nodes.clone();
            nodes.sort();
            nodes
        };
        
        let output_nodes: Vec<usize> = {
            let mut nodes = pattern.output_nodes.clone();
            nodes.sort();
            nodes
        };
        
        let measured_nodes = self.get_measured_nodes(pattern);
        
        // Calculate how many qubits we need
        let n_inputs = input_nodes.len();
        let n_outputs = output_nodes.len();
        let n_classical_outputs = measured_nodes.len();
        
        // Build the function signature
        let input_types = vec![HugrType::Qubit; n_inputs];
        let mut output_types = vec![HugrType::Qubit; n_outputs];
        output_types.extend(vec![HugrType::Bool; n_classical_outputs]);
        
        // Create a DFG (dataflow graph) - removed mut as it's not needed
        let dfg = DfgBuilder::new(input_types);
        
        // Initialize input qubits
        for (i, &node_idx) in input_nodes.iter().enumerate() {
            let wire = dfg.input_wires[i];
            self.qubit_wires.insert(node_idx, wire);
        }
        
        self.dfg = Some(dfg);
        
        // Process pattern commands in order
        for cmd in pattern.iter() {
            self.process_command(cmd);
        }
        
        // Collect outputs
        let mut output_wires = Vec::new();
        
        // Add output qubits
        for &node_idx in &output_nodes {
            if let Some(&wire) = self.qubit_wires.get(&node_idx) {
                output_wires.push(wire);
            } else {
                return Err(ConversionError::OutputNodeNotFound(node_idx));
            }
        }
        
        // Add classical measurement results
        for &node_idx in &measured_nodes {
            if let Some(&wire) = self.classical_wires.get(&node_idx) {
                output_wires.push(wire);
            } else {
                // If no classical wire, create a constant false
                let dfg = self.dfg.as_mut().unwrap();
                let false_const = dfg.add_const(ConstValue::Bool(false));
                let false_wire = dfg.load_const(false_const);
                output_wires.push(false_wire);
            }
        }
        
        // Set the outputs
        let dfg = self.dfg.as_mut().unwrap();
        dfg.set_outputs(output_wires);
        
        Ok(dfg.hugr.clone())
    }
    
    fn get_measured_nodes(&self, pattern: &Pattern) -> Vec<usize> {
        let mut measured = Vec::new();
        let output_set: HashSet<_> = pattern.output_nodes.iter().cloned().collect();
        
        for cmd in pattern.iter() {
            if let Command::M { node, .. } = cmd {
                if !output_set.contains(node) {
                    measured.push(*node);
                }
            }
        }
        
        measured.sort();
        measured.dedup();
        measured
    }
    
    fn process_command(&mut self, cmd: &Command) {
        match cmd {
            Command::N { node } => self.process_prepare(*node),
            Command::E { nodes } => self.process_entangle(*nodes),
            Command::M { node, plane, angle } => self.process_measure(*node, *plane, *angle),
            Command::X { node, domain } => self.process_pauli_x(*node, domain),
            Command::Z { node, domain } => self.process_pauli_z(*node, domain),
            Command::C { node, clifford } => self.process_clifford(*node, clifford),
        }
    }
    
    fn process_prepare(&mut self, node: usize) {
        let dfg = self.dfg.as_mut().unwrap();
        
        let prep_op = Operation::Custom {
            name: "PrepareQubit".to_string(),
            signature: FunctionType::new(vec![], vec![HugrType::Qubit]),
            extension: QUANTUM_EXTENSION.to_string(),
            args: vec![],
        };
        
        let result_node = dfg.add_op(prep_op, vec![]);
        let wire = result_node.out(0);
        
        self.qubit_wires.insert(node, wire);
        self.node_order.push(node);
    }
    
    fn process_entangle(&mut self, nodes: (usize, usize)) {
        let (node1, node2) = nodes;
        
        if let (Some(&q1), Some(&q2)) = (
            self.qubit_wires.get(&node1),
            self.qubit_wires.get(&node2),
        ) {
            // FIXED: Create the operation first (immutable borrow)
            let cz_op = self.create_cz_gate();
            
            // Then get mutable reference to dfg
            let dfg = self.dfg.as_mut().unwrap();
            let result_node = dfg.add_op(cz_op, vec![q1, q2]);
            
            self.qubit_wires.insert(node1, result_node.out(0));
            self.qubit_wires.insert(node2, result_node.out(1));
        }
    }
    
    fn process_measure(&mut self, node: usize, plane: Plane, angle: f64) {
        if let Some(mut qubit_wire) = self.qubit_wires.get(&node).cloned() {
            // Apply basis change based on measurement plane
            match plane {
                Plane::XY => {
                    // XY plane: Rz(-angle) * H
                    if angle.abs() > 1e-10 {
                        let rz_op = self.create_rz_gate(-angle);
                        let dfg = self.dfg.as_mut().unwrap();
                        let node = dfg.add_op(rz_op, vec![qubit_wire]);
                        qubit_wire = node.out(0);
                    }
                    
                    let h_op = self.create_h_gate();
                    let dfg = self.dfg.as_mut().unwrap();
                    let node = dfg.add_op(h_op, vec![qubit_wire]);
                    qubit_wire = node.out(0);
                }
                Plane::YZ => {
                    if angle.abs() > 1e-10 {
                        let rx_op = self.create_rx_gate(-angle);
                        let dfg = self.dfg.as_mut().unwrap();
                        let node = dfg.add_op(rx_op, vec![qubit_wire]);
                        qubit_wire = node.out(0);
                    }
                }
                Plane::XZ => {
                    if angle.abs() > 1e-10 {
                        let ry_op = self.create_ry_gate(angle);
                        let dfg = self.dfg.as_mut().unwrap();
                        let node = dfg.add_op(ry_op, vec![qubit_wire]);
                        qubit_wire = node.out(0);
                    }
                }
            }
            
            // Perform measurement in Z basis
            let meas_op = self.create_measure_op();
            let dfg = self.dfg.as_mut().unwrap();
            let result_node = dfg.add_op(meas_op, vec![qubit_wire]);
            
            self.classical_wires.insert(node, result_node.out(0));
            self.qubit_wires.remove(&node);
        }
    }
    
    fn process_pauli_x(&mut self, node: usize, domain: &HashSet<usize>) {
        if let Some(qubit_wire) = self.qubit_wires.get(&node).cloned() {
            let condition = self.compute_xor_of_measurements(domain);
            let new_wire = self.apply_conditional_gate(qubit_wire, condition, "X");
            self.qubit_wires.insert(node, new_wire);
        }
    }
    
    fn process_pauli_z(&mut self, node: usize, domain: &HashSet<usize>) {
        if let Some(qubit_wire) = self.qubit_wires.get(&node).cloned() {
            let condition = self.compute_xor_of_measurements(domain);
            let new_wire = self.apply_conditional_gate(qubit_wire, condition, "Z");
            self.qubit_wires.insert(node, new_wire);
        }
    }
    
    fn process_clifford(&mut self, node: usize, clifford: &[CliffordGate]) {
        if let Some(mut qubit_wire) = self.qubit_wires.get(&node).cloned() {
            for &gate in clifford {
                let op = match gate {
                    CliffordGate::H => self.create_h_gate(),
                    CliffordGate::S => self.create_s_gate(),
                    CliffordGate::X => self.create_x_gate(),
                    CliffordGate::Y => self.create_y_gate(),
                    CliffordGate::Z => self.create_z_gate(),
                    CliffordGate::SDG => self.create_sdg_gate(),
                    CliffordGate::I => continue, // Skip identity
                };
                
                let dfg = self.dfg.as_mut().unwrap();
                let result_node = dfg.add_op(op, vec![qubit_wire]);
                qubit_wire = result_node.out(0);
            }
            
            self.qubit_wires.insert(node, qubit_wire);
        }
    }
    
    fn compute_xor_of_measurements(&mut self, domain: &HashSet<usize>) -> Wire {
        if domain.is_empty() {
            let dfg = self.dfg.as_mut().unwrap();
            let false_const = dfg.add_const(ConstValue::Bool(false));
            return dfg.load_const(false_const);
        }
        
        let mut domain_list: Vec<_> = domain.iter().cloned().collect();
        domain_list.sort();
        
        let first_node = domain_list[0];
        if let Some(&result) = self.classical_wires.get(&first_node) {
            let mut xor_result = result;
            
            for &node_idx in &domain_list[1..] {
                if let Some(&wire) = self.classical_wires.get(&node_idx) {
                    let dfg = self.dfg.as_mut().unwrap();
                    let xor_op = Operation::Custom {
                        name: "XOR".to_string(),
                        signature: FunctionType::new(
                            vec![HugrType::Bool, HugrType::Bool],
                            vec![HugrType::Bool],
                        ),
                        extension: LOGIC_EXTENSION.to_string(),
                        args: vec![],
                    };
                    
                    let result_node = dfg.add_op(xor_op, vec![xor_result, wire]);
                    xor_result = result_node.out(0);
                }
            }
            
            xor_result
        } else {
            let dfg = self.dfg.as_mut().unwrap();
            let false_const = dfg.add_const(ConstValue::Bool(false));
            dfg.load_const(false_const)
        }
    }
    
    fn apply_conditional_gate(&mut self, qubit_wire: Wire, condition: Wire, gate_name: &str) -> Wire {
        let dfg = self.dfg.as_mut().unwrap();
        
        let cond_gate_op = Operation::Custom {
            name: format!("Conditional{}", gate_name),
            signature: FunctionType::new(
                vec![HugrType::Bool, HugrType::Qubit],
                vec![HugrType::Qubit],
            ),
            extension: QUANTUM_EXTENSION.to_string(),
            args: vec![],
        };
        
        let result_node = dfg.add_op(cond_gate_op, vec![condition, qubit_wire]);
        result_node.out(0)
    }
    
    // Gate creation methods
    
    fn create_h_gate(&self) -> Operation {
        Operation::Custom {
            name: "H".to_string(),
            signature: FunctionType::new(vec![HugrType::Qubit], vec![HugrType::Qubit]),
            extension: QUANTUM_EXTENSION.to_string(),
            args: vec![],
        }
    }
    
    fn create_x_gate(&self) -> Operation {
        Operation::Custom {
            name: "X".to_string(),
            signature: FunctionType::new(vec![HugrType::Qubit], vec![HugrType::Qubit]),
            extension: QUANTUM_EXTENSION.to_string(),
            args: vec![],
        }
    }
    
    fn create_y_gate(&self) -> Operation {
        Operation::Custom {
            name: "Y".to_string(),
            signature: FunctionType::new(vec![HugrType::Qubit], vec![HugrType::Qubit]),
            extension: QUANTUM_EXTENSION.to_string(),
            args: vec![],
        }
    }
    
    fn create_z_gate(&self) -> Operation {
        Operation::Custom {
            name: "Z".to_string(),
            signature: FunctionType::new(vec![HugrType::Qubit], vec![HugrType::Qubit]),
            extension: QUANTUM_EXTENSION.to_string(),
            args: vec![],
        }
    }
    
    fn create_s_gate(&self) -> Operation {
        Operation::Custom {
            name: "S".to_string(),
            signature: FunctionType::new(vec![HugrType::Qubit], vec![HugrType::Qubit]),
            extension: QUANTUM_EXTENSION.to_string(),
            args: vec![],
        }
    }
    
    fn create_sdg_gate(&self) -> Operation {
        Operation::Custom {
            name: "Sdg".to_string(),
            signature: FunctionType::new(vec![HugrType::Qubit], vec![HugrType::Qubit]),
            extension: QUANTUM_EXTENSION.to_string(),
            args: vec![],
        }
    }
    
    fn create_cz_gate(&self) -> Operation {
        Operation::Custom {
            name: "CZ".to_string(),
            signature: FunctionType::new(
                vec![HugrType::Qubit, HugrType::Qubit],
                vec![HugrType::Qubit, HugrType::Qubit],
            ),
            extension: QUANTUM_EXTENSION.to_string(),
            args: vec![],
        }
    }
    
    fn create_rz_gate(&self, angle: f64) -> Operation {
        Operation::Custom {
            name: "Rz".to_string(),
            signature: FunctionType::new(vec![HugrType::Qubit], vec![HugrType::Qubit]),
            extension: QUANTUM_EXTENSION.to_string(),
            args: vec![angle],
        }
    }
    
    fn create_rx_gate(&self, angle: f64) -> Operation {
        Operation::Custom {
            name: "Rx".to_string(),
            signature: FunctionType::new(vec![HugrType::Qubit], vec![HugrType::Qubit]),
            extension: QUANTUM_EXTENSION.to_string(),
            args: vec![angle],
        }
    }
    
    fn create_ry_gate(&self, angle: f64) -> Operation {
        Operation::Custom {
            name: "Ry".to_string(),
            signature: FunctionType::new(vec![HugrType::Qubit], vec![HugrType::Qubit]),
            extension: QUANTUM_EXTENSION.to_string(),
            args: vec![angle],
        }
    }
    
    fn create_measure_op(&self) -> Operation {
        Operation::Custom {
            name: "Measure".to_string(),
            signature: FunctionType::new(vec![HugrType::Qubit], vec![HugrType::Bool]),
            extension: QUANTUM_EXTENSION.to_string(),
            args: vec![],
        }
    }
}

impl Default for GraphixToHugrConverter {
    fn default() -> Self {
        Self::new()
    }
}

/// Convenience function to convert a Graphix Pattern to HUGR
pub fn convert_graphix_pattern_to_hugr(pattern: &Pattern) -> Result<Hugr, ConversionError> {
    let mut converter = GraphixToHugrConverter::new();
    converter.convert(pattern)
}