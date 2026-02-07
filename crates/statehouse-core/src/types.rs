// Core types for Statehouse

use serde::{Deserialize, Serialize};

/// Namespace for logical isolation
pub type Namespace = String;

/// Agent identifier
pub type AgentId = String;

/// State key
pub type Key = String;

/// Transaction ID
pub type TxnId = String;

/// Version counter
pub type Version = u64;

/// Commit timestamp (logical)
pub type CommitTs = u64;

/// Record identity tuple
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct RecordId {
    pub namespace: Namespace,
    pub agent_id: AgentId,
    pub key: Key,
}

impl RecordId {
    pub fn new(namespace: Namespace, agent_id: AgentId, key: Key) -> Self {
        Self {
            namespace,
            agent_id,
            key,
        }
    }
}
