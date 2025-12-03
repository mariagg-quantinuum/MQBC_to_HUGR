use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// HUGR wire handle - represents a dataflow wire
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct Wire {
    pub node_id: usize,
    pub port: usize,
}

impl Wire {
    pub fn new(node_id: usize, port: usize) -> Self {
        Self { node_id, port }
    }
}

/// HUGR type system
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum HugrType {
    Qubit,
    Bool,
    Float64,
}

/// Function signature type
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FunctionType {
    pub inputs: Vec<HugrType>,
    pub outputs: Vec<HugrType>,
}

impl FunctionType {
    pub fn new(inputs: Vec<HugrType>, outputs: Vec<HugrType>) -> Self {
        Self { inputs, outputs }
    }
}

/// HUGR operation types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Operation {
    /// Input node
    Input {
        types: Vec<HugrType>,
    },
    
    /// Output node
    Output {
        types: Vec<HugrType>,
    },
    
    /// Custom operation (quantum gates, etc.)
    Custom {
        name: String,
        signature: FunctionType,
        extension: String,
        args: Vec<f64>, // Type arguments (e.g., rotation angles)
    },
    
    /// Constant value
    Const {
        value: ConstValue,
    },
    
    /// Load a constant
    LoadConst {
        const_node: usize,
    },
    
    /// Dataflow graph container
    DFG {
        signature: FunctionType,
    },
}

/// Constant values
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ConstValue {
    Bool(bool),
    Float(f64),
}

/// HUGR node in the graph
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Node {
    pub id: usize,
    pub operation: Operation,
    pub inputs: Vec<Wire>,
    pub outputs: Vec<Wire>,
}

impl Node {
    pub fn new(id: usize, operation: Operation) -> Self {
        Self {
            id,
            operation,
            inputs: Vec::new(),
            outputs: Vec::new(),
        }
    }
    
    pub fn out(&self, port: usize) -> Wire {
        Wire::new(self.id, port)
    }
}

/// HUGR graph representation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Hugr {
    pub nodes: HashMap<usize, Node>,
    pub next_node_id: usize,
    pub root: usize,
}

impl Hugr {
    pub fn new() -> Self {
        Self {
            nodes: HashMap::new(),
            next_node_id: 0,
            root: 0,
        }
    }
    
    pub fn add_node(&mut self, operation: Operation) -> usize {
        let id = self.next_node_id;
        self.next_node_id += 1;
        
        let node = Node::new(id, operation);
        self.nodes.insert(id, node);
        
        id
    }
    
    pub fn get_node(&self, id: usize) -> Option<&Node> {
        self.nodes.get(&id)
    }
    
    pub fn get_node_mut(&mut self, id: usize) -> Option<&mut Node> {
        self.nodes.get_mut(&id)
    }
    
    pub fn len(&self) -> usize {
        self.nodes.len()
    }
}

impl Default for Hugr {
    fn default() -> Self {
        Self::new()
    }
}

/// Dataflow graph builder
pub struct DfgBuilder {
    pub hugr: Hugr,
    pub input_node_id: usize,
    pub output_node_id: Option<usize>,
    pub input_wires: Vec<Wire>,
}

impl DfgBuilder {
    pub fn new(input_types: Vec<HugrType>) -> Self {
        let mut hugr = Hugr::new();
        
        // Create input node
        let input_op = Operation::Input {
            types: input_types.clone(),
        };
        let input_node_id = hugr.add_node(input_op);
        
        // Create wires from input node
        let input_wires: Vec<Wire> = (0..input_types.len())
            .map(|port| Wire::new(input_node_id, port))
            .collect();
        
        Self {
            hugr,
            input_node_id,
            output_node_id: None,
            input_wires,
        }
    }
    
    pub fn add_op(&mut self, operation: Operation, inputs: Vec<Wire>) -> &Node {
        let node_id = self.hugr.add_node(operation);
        
        if let Some(node) = self.hugr.get_node_mut(node_id) {
            node.inputs = inputs;
            
            // Determine number of outputs based on operation
            let num_outputs = match &node.operation {
                Operation::Custom { signature, .. } => signature.outputs.len(),
                Operation::LoadConst { .. } => 1,
                _ => 0,
            };
            
            node.outputs = (0..num_outputs)
                .map(|port| Wire::new(node_id, port))
                .collect();
        }
        
        self.hugr.get_node(node_id).unwrap()
    }
    
    pub fn add_const(&mut self, value: ConstValue) -> usize {
        let const_op = Operation::Const { value };
        self.hugr.add_node(const_op)
    }
    
    pub fn load_const(&mut self, const_node_id: usize) -> Wire {
        let load_op = Operation::LoadConst {
            const_node: const_node_id,
        };
        let node = self.add_op(load_op, vec![]);
        node.out(0)
    }
    
    pub fn set_outputs(&mut self, outputs: Vec<Wire>) {
        let output_types: Vec<HugrType> = outputs
            .iter()
            .map(|_| HugrType::Qubit) // Simplified - would need proper type tracking
            .collect();
        
        let output_op = Operation::Output { types: output_types };
        let output_node_id = self.hugr.add_node(output_op);
        
        if let Some(node) = self.hugr.get_node_mut(output_node_id) {
            node.inputs = outputs;
        }
        
        self.output_node_id = Some(output_node_id);
    }
}