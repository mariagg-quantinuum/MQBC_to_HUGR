use serde::{Deserialize, Serialize};
use std::collections::{HashSet};

/// Measurement plane in MBQC
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Plane {
    XY,
    YZ,
    XZ,
}

/// Command kind enumeration
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CommandKind {
    /// Prepare node (N command)
    N,
    /// Entangle nodes (E command)
    E,
    /// Measure node (M command)
    M,
    /// Pauli X correction (X command)
    X,
    /// Pauli Z correction (Z command)
    Z,
    /// Clifford correction (C command)
    C,
}

/// Clifford gate elements
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CliffordGate {
    I,    // Identity
    X,    // Pauli X
    Y,    // Pauli Y
    Z,    // Pauli Z
    S,    // S gate
    SDG,  // S dagger
    H,    // Hadamard
}

/// Represents a Graphix command
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Command {
    /// Prepare a qubit node in |+⟩ state
    N { node: usize },
    
    /// Entangle two nodes with CZ gate
    E { nodes: (usize, usize) },
    
    /// Measure a node
    M {
        node: usize,
        plane: Plane,
        angle: f64,
    },
    
    /// Apply Pauli X correction based on measurement outcomes
    X {
        node: usize,
        domain: HashSet<usize>,
    },
    
    /// Apply Pauli Z correction based on measurement outcomes
    Z {
        node: usize,
        domain: HashSet<usize>,
    },
    
    /// Apply Clifford correction
    C {
        node: usize,
        clifford: Vec<CliffordGate>,
    },
}

impl Command {
    pub fn kind(&self) -> CommandKind {
        match self {
            Command::N { .. } => CommandKind::N,
            Command::E { .. } => CommandKind::E,
            Command::M { .. } => CommandKind::M,
            Command::X { .. } => CommandKind::X,
            Command::Z { .. } => CommandKind::Z,
            Command::C { .. } => CommandKind::C,
        }
    }
}

/// Represents a Graphix MBQC pattern
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Pattern {
    pub input_nodes: Vec<usize>,
    pub output_nodes: Vec<usize>,
    pub commands: Vec<Command>,
}

impl Pattern {
    pub fn new(input_nodes: Vec<usize>, output_nodes: Vec<usize>) -> Self {
        Self {
            input_nodes,
            output_nodes,
            commands: Vec::new(),
        }
    }
    
    pub fn add_command(&mut self, command: Command) {
        self.commands.push(command);
    }
    
    pub fn iter(&self) -> impl Iterator<Item = &Command> {
        self.commands.iter()
    }
}