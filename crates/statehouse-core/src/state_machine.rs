// State machine implementation

use anyhow::{anyhow, Result};
use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use std::time::{Duration, Instant};
use tracing::{info, debug};

use crate::storage::{EventLogEntry, OperationRecord, StateRecord, Storage};
use crate::types::*;

/// Transaction state
#[derive(Debug, Clone)]
struct Transaction {
    txn_id: TxnId,
    created_at: Instant,
    timeout: Duration,
    operations: Vec<StagedOperation>,
}

#[derive(Debug, Clone)]
enum StagedOperation {
    Write {
        namespace: Namespace,
        agent_id: AgentId,
        key: Key,
        value: serde_json::Value,
    },
    Delete {
        namespace: Namespace,
        agent_id: AgentId,
        key: Key,
    },
}

/// Command to the state machine
#[derive(Debug)]
pub enum Command {
    BeginTransaction {
        timeout_ms: Option<u64>,
    },
    Write {
        txn_id: TxnId,
        namespace: Namespace,
        agent_id: AgentId,
        key: Key,
        value: serde_json::Value,
    },
    Delete {
        txn_id: TxnId,
        namespace: Namespace,
        agent_id: AgentId,
        key: Key,
    },
    Commit {
        txn_id: TxnId,
    },
    Abort {
        txn_id: TxnId,
    },
}

/// State machine for Statehouse
/// Single-writer design: all mutations go through one logical thread
pub struct StateMachine {
    storage: Arc<dyn Storage>,
    transactions: Arc<RwLock<HashMap<TxnId, Transaction>>>,
    version_counters: Arc<RwLock<HashMap<RecordId, Version>>>,
    commits_since_snapshot: Arc<RwLock<u64>>,
}

impl StateMachine {
    pub fn new(storage: Arc<dyn Storage>) -> Self {
        Self {
            storage,
            transactions: Arc::new(RwLock::new(HashMap::new())),
            version_counters: Arc::new(RwLock::new(HashMap::new())),
            commits_since_snapshot: Arc::new(RwLock::new(0)),
        }
    }

    /// Begin a new transaction
    pub fn begin_transaction(&self, timeout_ms: Option<u64>) -> Result<TxnId> {
        let txn_id = uuid::Uuid::new_v4().to_string();
        let timeout = Duration::from_millis(timeout_ms.unwrap_or(30000));

        let txn = Transaction {
            txn_id: txn_id.clone(),
            created_at: Instant::now(),
            timeout,
            operations: Vec::new(),
        };

        let mut transactions = self.transactions.write().unwrap();
        transactions.insert(txn_id.clone(), txn);

        debug!("Transaction started: txn_id={}", txn_id);
        Ok(txn_id)
    }

    /// Stage a write operation
    pub fn write(&self, txn_id: &str, namespace: String, agent_id: String, key: String, value: serde_json::Value) -> Result<()> {
        let mut transactions = self.transactions.write().unwrap();
        let txn = transactions.get_mut(txn_id).ok_or_else(|| anyhow!("Transaction not found"))?;

        // Check timeout
        if txn.created_at.elapsed() > txn.timeout {
            transactions.remove(txn_id);
            return Err(anyhow!("Transaction expired"));
        }

        txn.operations.push(StagedOperation::Write {
            namespace,
            agent_id,
            key,
            value,
        });

        Ok(())
    }

    /// Stage a delete operation
    pub fn delete(&self, txn_id: &str, namespace: String, agent_id: String, key: String) -> Result<()> {
        let mut transactions = self.transactions.write().unwrap();
        let txn = transactions.get_mut(txn_id).ok_or_else(|| anyhow!("Transaction not found"))?;

        // Check timeout
        if txn.created_at.elapsed() > txn.timeout {
            transactions.remove(txn_id);
            return Err(anyhow!("Transaction expired"));
        }

        txn.operations.push(StagedOperation::Delete {
            namespace,
            agent_id,
            key,
        });

        Ok(())
    }

    /// Commit a transaction atomically
    pub fn commit(&self, txn_id: &str) -> Result<CommitTs> {
        use tracing::{info, debug};
        
        debug!(txn_id = %txn_id, "Committing transaction");
        
        // Remove transaction from staging
        let txn = {
            let mut transactions = self.transactions.write().unwrap();
            transactions.remove(txn_id).ok_or_else(|| anyhow!("Transaction not found"))?
        };

        // Check timeout
        if txn.created_at.elapsed() > txn.timeout {
            debug!(txn_id = %txn_id, "Transaction expired");
            return Err(anyhow!("Transaction expired"));
        }

        // Get commit timestamp
        let commit_ts = self.storage.next_commit_ts()?;

        // Apply operations
        let mut operation_records = Vec::new();
        let mut version_counters = self.version_counters.write().unwrap();

        for op in txn.operations {
            match op {
                StagedOperation::Write { namespace, agent_id, key, value } => {
                    let record_id = RecordId::new(namespace.clone(), agent_id.clone(), key.clone());

                    // Get next version for this key
                    let version = version_counters.entry(record_id.clone()).or_insert(0);
                    *version += 1;
                    let current_version = *version;

                    // Write to storage
                    let record = StateRecord {
                        namespace: namespace.clone(),
                        agent_id: agent_id.clone(),
                        key: key.clone(),
                        value: Some(value.clone()),
                        version: current_version,
                        commit_ts,
                        deleted: false,
                    };
                    self.storage.write_state(record)?;

                    // Record operation
                    operation_records.push(OperationRecord {
                        namespace,
                        agent_id,
                        key,
                        value: Some(value),
                        version: current_version,
                    });
                }
                StagedOperation::Delete { namespace, agent_id, key } => {
                    let record_id = RecordId::new(namespace.clone(), agent_id.clone(), key.clone());

                    // Get next version for this key
                    let version = version_counters.entry(record_id.clone()).or_insert(0);
                    *version += 1;
                    let current_version = *version;

                    // Write tombstone to storage
                    let record = StateRecord {
                        namespace: namespace.clone(),
                        agent_id: agent_id.clone(),
                        key: key.clone(),
                        value: None,
                        version: current_version,
                        commit_ts,
                        deleted: true,
                    };
                    self.storage.write_state(record)?;

                    // Record operation
                    operation_records.push(OperationRecord {
                        namespace,
                        agent_id,
                        key,
                        value: None,
                        version: current_version,
                    });
                }
            }
        }

        // Append event to log
        let event = EventLogEntry {
            txn_id: txn.txn_id.clone(),
            commit_ts,
            operations: operation_records.clone(),
        };
        self.storage.append_event(event)?;

        // Flush if needed
        self.storage.flush()?;

        // Log successful commit
        info!(
            txn_id = %txn_id,
            commit_ts = commit_ts,
            operations = operation_records.len(),
            "Transaction committed"
        );

        Ok(commit_ts)
    }

    /// Abort a transaction
    pub fn abort(&self, txn_id: &str) -> Result<()> {
        use tracing::debug;
        
        let mut transactions = self.transactions.write().unwrap();
        if transactions.remove(txn_id).is_some() {
            debug!(txn_id = %txn_id, "Transaction aborted");
        }
        Ok(())
    }

    /// Read latest state
    pub fn get_state(&self, namespace: &str, agent_id: &str, key: &str) -> Result<Option<StateRecord>> {
        let record_id = RecordId::new(namespace.to_string(), agent_id.to_string(), key.to_string());
        self.storage.read_state(&record_id)
    }

    /// Read state at specific version
    pub fn get_state_at_version(&self, namespace: &str, agent_id: &str, key: &str, version: Version) -> Result<Option<StateRecord>> {
        let record_id = RecordId::new(namespace.to_string(), agent_id.to_string(), key.to_string());
        self.storage.read_state_at_version(&record_id, version)
    }

    /// List keys for an agent
    pub fn list_keys(&self, namespace: &str, agent_id: &str) -> Result<Vec<String>> {
        self.storage.list_keys(namespace, agent_id)
    }

    /// Scan keys with prefix
    pub fn scan_prefix(&self, namespace: &str, agent_id: &str, prefix: &str) -> Result<Vec<StateRecord>> {
        self.storage.scan_prefix(namespace, agent_id, prefix)
    }

    /// Replay events for an agent
    pub fn replay(&self, namespace: &str, agent_id: &str, start_ts: Option<CommitTs>, end_ts: Option<CommitTs>) -> Result<Vec<EventLogEntry>> {
        info!(
            namespace = %namespace,
            agent_id = %agent_id,
            start_ts = ?start_ts,
            end_ts = ?end_ts,
            "Replay started"
        );

        let events = self.storage.replay_events(namespace, agent_id, start_ts, end_ts)?;
        let event_count = events.len();

        info!(
            namespace = %namespace,
            agent_id = %agent_id,
            event_count = event_count,
            "Replay completed"
        );

        Ok(events)
    }

    /// Cleanup expired transactions (should be called periodically)
    pub fn cleanup_expired_transactions(&self) {
        let mut transactions = self.transactions.write().unwrap();
        transactions.retain(|_, txn| txn.created_at.elapsed() <= txn.timeout);
    }

    /// Create a snapshot of current state
    pub fn create_snapshot(&self) -> Result<()> {
        let snapshot = self.storage.create_snapshot()?;
        self.storage.save_snapshot(&snapshot)?;
        
        // Reset counter after successful snapshot
        let mut counter = self.commits_since_snapshot.write().unwrap();
        *counter = 0;
        
        Ok(())
    }

    /// Check if snapshot should be created and do it if needed
    pub fn maybe_snapshot(&self, snapshot_interval: u64) -> Result<()> {
        let mut counter = self.commits_since_snapshot.write().unwrap();
        *counter += 1;
        
        if *counter >= snapshot_interval {
            drop(counter); // Release lock before creating snapshot
            self.create_snapshot()?;
        }
        
        Ok(())
    }

    /// Load snapshot and replay events after snapshot timestamp
    pub fn recover_from_snapshot(&self, snapshot: &crate::storage::Snapshot) -> Result<()> {
        // Restore version counters from snapshot
        let mut version_counters = self.version_counters.write().unwrap();
        version_counters.clear();
        
        for record in &snapshot.records {
            let record_id = RecordId::new(
                record.namespace.clone(),
                record.agent_id.clone(),
                record.key.clone(),
            );
            version_counters.insert(record_id, record.version);
        }
        
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::storage::InMemoryStorage;

    #[test]
    fn test_transaction_lifecycle() {
        let storage = Arc::new(InMemoryStorage::new());
        let sm = StateMachine::new(storage);

        // Begin transaction
        let txn_id = sm.begin_transaction(None).unwrap();

        // Write
        sm.write(&txn_id, "default".to_string(), "agent-1".to_string(), "key1".to_string(), serde_json::json!({"value": 42})).unwrap();

        // Commit
        let commit_ts = sm.commit(&txn_id).unwrap();
        assert!(commit_ts > 0);

        // Read
        let state = sm.get_state("default", "agent-1", "key1").unwrap();
        assert!(state.is_some());
        let record = state.unwrap();
        assert_eq!(record.value.unwrap()["value"], 42);
    }

    #[test]
    fn test_delete() {
        let storage = Arc::new(InMemoryStorage::new());
        let sm = StateMachine::new(storage);

        // Write
        let txn_id = sm.begin_transaction(None).unwrap();
        sm.write(&txn_id, "default".to_string(), "agent-1".to_string(), "key1".to_string(), serde_json::json!({"value": 42})).unwrap();
        sm.commit(&txn_id).unwrap();

        // Delete
        let txn_id = sm.begin_transaction(None).unwrap();
        sm.delete(&txn_id, "default".to_string(), "agent-1".to_string(), "key1".to_string()).unwrap();
        sm.commit(&txn_id).unwrap();

        // Read should show deleted
        let state = sm.get_state("default", "agent-1", "key1").unwrap();
        assert!(state.is_some());
        assert!(state.unwrap().deleted);
    }

    #[test]
    fn test_versioning() {
        let storage = Arc::new(InMemoryStorage::new());
        let sm = StateMachine::new(storage);

        // Write v1
        let txn_id = sm.begin_transaction(None).unwrap();
        sm.write(&txn_id, "default".to_string(), "agent-1".to_string(), "key1".to_string(), serde_json::json!({"value": 1})).unwrap();
        sm.commit(&txn_id).unwrap();

        // Write v2
        let txn_id = sm.begin_transaction(None).unwrap();
        sm.write(&txn_id, "default".to_string(), "agent-1".to_string(), "key1".to_string(), serde_json::json!({"value": 2})).unwrap();
        sm.commit(&txn_id).unwrap();

        // Read at version 1
        let state_v1 = sm.get_state_at_version("default", "agent-1", "key1", 1).unwrap();
        assert_eq!(state_v1.unwrap().value.unwrap()["value"], 1);

        // Read at version 2
        let state_v2 = sm.get_state_at_version("default", "agent-1", "key1", 2).unwrap();
        assert_eq!(state_v2.unwrap().value.unwrap()["value"], 2);

        // Read latest
        let state_latest = sm.get_state("default", "agent-1", "key1").unwrap();
        assert_eq!(state_latest.unwrap().value.unwrap()["value"], 2);
    }

    #[test]
    fn test_read_after_write() {
        let storage = Arc::new(InMemoryStorage::new());
        let sm = StateMachine::new(storage);

        // Write
        let txn_id = sm.begin_transaction(None).unwrap();
        sm.write(&txn_id, "default".to_string(), "agent-1".to_string(), "counter".to_string(), serde_json::json!(1)).unwrap();
        sm.commit(&txn_id).unwrap();

        // Read should immediately see the value
        let state = sm.get_state("default", "agent-1", "counter").unwrap();
        assert!(state.is_some());
        assert_eq!(state.unwrap().value.unwrap(), serde_json::json!(1));
    }

    #[test]
    fn test_aborted_tx_has_no_effect() {
        let storage = Arc::new(InMemoryStorage::new());
        let sm = StateMachine::new(storage);

        // Begin transaction
        let txn_id = sm.begin_transaction(None).unwrap();
        
        // Write
        sm.write(&txn_id, "default".to_string(), "agent-1".to_string(), "temp".to_string(), serde_json::json!(42)).unwrap();
        
        // Abort
        sm.abort(&txn_id).unwrap();

        // Read should return None (no state)
        let state = sm.get_state("default", "agent-1", "temp").unwrap();
        assert!(state.is_none());
    }

    #[test]
    fn test_concurrent_commits_serialize() {
        use std::thread;

        let storage = Arc::new(InMemoryStorage::new());
        let sm = Arc::new(StateMachine::new(storage));

        let mut handles = vec![];

        // Spawn multiple threads that each commit a transaction
        for i in 0..10 {
            let sm_clone = sm.clone();
            let handle = thread::spawn(move || {
                let txn_id = sm_clone.begin_transaction(None).unwrap();
                sm_clone.write(
                    &txn_id,
                    "default".to_string(),
                    "agent-1".to_string(),
                    format!("key{}", i),
                    serde_json::json!(i),
                ).unwrap();
                sm_clone.commit(&txn_id).unwrap();
            });
            handles.push(handle);
        }

        // Wait for all threads to complete
        for handle in handles {
            handle.join().unwrap();
        }

        // Verify all writes succeeded
        for i in 0..10 {
            let state = sm.get_state("default", "agent-1", &format!("key{}", i)).unwrap();
            assert!(state.is_some());
            assert_eq!(state.unwrap().value.unwrap(), serde_json::json!(i));
        }
    }

    #[test]
    fn test_transaction_timeout() {
        use std::time::Duration;
        use std::thread;

        let storage = Arc::new(InMemoryStorage::new());
        let sm = StateMachine::new(storage);

        // Begin transaction with very short timeout
        let txn_id = sm.begin_transaction(Some(100)).unwrap(); // 100ms timeout

        // Wait for timeout
        thread::sleep(Duration::from_millis(150));

        // Try to commit - should fail
        let result = sm.commit(&txn_id);
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("expired"));
    }

    #[test]
    fn test_list_keys_after_operations() {
        let storage = Arc::new(InMemoryStorage::new());
        let sm = StateMachine::new(storage);

        // Write multiple keys
        for i in 1..=5 {
            let txn_id = sm.begin_transaction(None).unwrap();
            sm.write(
                &txn_id,
                "default".to_string(),
                "agent-1".to_string(),
                format!("key{}", i),
                serde_json::json!(i),
            ).unwrap();
            sm.commit(&txn_id).unwrap();
        }

        // Delete one key
        let txn_id = sm.begin_transaction(None).unwrap();
        sm.delete(&txn_id, "default".to_string(), "agent-1".to_string(), "key3".to_string()).unwrap();
        sm.commit(&txn_id).unwrap();

        // List should show 4 keys (5 - 1 deleted)
        let keys = sm.list_keys("default", "agent-1").unwrap();
        assert_eq!(keys.len(), 4);
        assert!(!keys.contains(&"key3".to_string()));
    }

    #[test]
    fn test_replay_determinism() {
        let storage = Arc::new(InMemoryStorage::new());
        let sm = StateMachine::new(storage);

        // Perform multiple transactions
        for i in 1..=5 {
            let txn_id = sm.begin_transaction(None).unwrap();
            sm.write(
                &txn_id,
                "default".to_string(),
                "agent-1".to_string(),
                format!("key{}", i),
                serde_json::json!({"step": i}),
            ).unwrap();
            sm.commit(&txn_id).unwrap();
        }

        // Replay events
        let events = sm.replay("default", "agent-1", None, None).unwrap();
        assert_eq!(events.len(), 5);

        // Verify events are in order by commit_ts
        for i in 1..events.len() {
            assert!(events[i].commit_ts > events[i-1].commit_ts);
        }
    }

    #[test]
    fn test_create_snapshot() {
        let storage = Arc::new(InMemoryStorage::new());
        let sm = StateMachine::new(storage.clone());

        // Write some data
        for i in 1..=3 {
            let txn_id = sm.begin_transaction(None).unwrap();
            sm.write(
                &txn_id,
                "default".to_string(),
                "agent-1".to_string(),
                format!("key{}", i),
                serde_json::json!({"value": i}),
            ).unwrap();
            sm.commit(&txn_id).unwrap();
        }

        // Create snapshot
        let snapshot = storage.create_snapshot().unwrap();
        assert_eq!(snapshot.metadata.version, 1);
        assert_eq!(snapshot.metadata.record_count, 3);
        assert_eq!(snapshot.records.len(), 3);
    }

    #[test]
    fn test_snapshot_persistence_with_rocksdb() {
        use tempfile::TempDir;
        use crate::storage::RocksStorage;

        // Create temporary directory for test
        let temp_dir = TempDir::new().unwrap();
        let config = crate::storage::StorageConfig {
            data_dir: temp_dir.path().to_path_buf(),
            fsync_on_commit: true,
            snapshot_interval: 10,
            max_log_size: 1024 * 1024,
        };

        // Write data and create snapshot
        {
            let storage = Arc::new(RocksStorage::new(config.clone()).unwrap());
            let sm = StateMachine::new(storage.clone());

            for i in 1..=5 {
                let txn_id = sm.begin_transaction(None).unwrap();
                sm.write(
                    &txn_id,
                    "default".to_string(),
                    "agent-1".to_string(),
                    format!("key{}", i),
                    serde_json::json!({"value": i}),
                ).unwrap();
                sm.commit(&txn_id).unwrap();
            }

            // Create and save snapshot
            sm.create_snapshot().unwrap();
        }

        // Simulate restart - load snapshot
        {
            let storage = Arc::new(RocksStorage::new(config.clone()).unwrap());
            let snapshot = storage.load_snapshot().unwrap();
            assert!(snapshot.is_some());
            
            let snapshot = snapshot.unwrap();
            assert_eq!(snapshot.metadata.version, crate::storage::SNAPSHOT_VERSION);
            assert_eq!(snapshot.metadata.record_count, 5);
            
            let sm = StateMachine::new(storage);
            sm.recover_from_snapshot(&snapshot).unwrap();

            // Verify data is accessible
            for i in 1..=5 {
                let state = sm.get_state("default", "agent-1", &format!("key{}", i)).unwrap();
                assert!(state.is_some());
                assert_eq!(state.unwrap().value.unwrap()["value"], i);
            }
        }
    }

    #[test]
    fn test_log_replay_after_snapshot() {
        use tempfile::TempDir;
        use crate::storage::RocksStorage;

        // Create temporary directory for test
        let temp_dir = TempDir::new().unwrap();
        let config = crate::storage::StorageConfig {
            data_dir: temp_dir.path().to_path_buf(),
            fsync_on_commit: true,
            snapshot_interval: 3,
            max_log_size: 1024 * 1024,
        };

        let snapshot_ts;
        
        // Phase 1: Write data before snapshot
        {
            let storage = Arc::new(RocksStorage::new(config.clone()).unwrap());
            let sm = StateMachine::new(storage.clone());

            for i in 1..=3 {
                let txn_id = sm.begin_transaction(None).unwrap();
                sm.write(
                    &txn_id,
                    "default".to_string(),
                    "agent-1".to_string(),
                    format!("before_{}", i),
                    serde_json::json!(i),
                ).unwrap();
                sm.commit(&txn_id).unwrap();
            }

            // Create snapshot
            sm.create_snapshot().unwrap();
            let snapshot = storage.create_snapshot().unwrap();
            snapshot_ts = snapshot.metadata.snapshot_ts;
        }

        // Phase 2: Write more data after snapshot (simulating crash recovery)
        {
            let storage = Arc::new(RocksStorage::new(config.clone()).unwrap());
            let sm = StateMachine::new(storage.clone());

            for i in 1..=2 {
                let txn_id = sm.begin_transaction(None).unwrap();
                sm.write(
                    &txn_id,
                    "default".to_string(),
                    "agent-1".to_string(),
                    format!("after_{}", i),
                    serde_json::json!(i + 100),
                ).unwrap();
                sm.commit(&txn_id).unwrap();
            }
        }

        // Phase 3: Restart and verify both snapshot and new data
        {
            let storage = Arc::new(RocksStorage::new(config.clone()).unwrap());
            let sm = StateMachine::new(storage.clone());

            // Load snapshot
            let snapshot = storage.load_snapshot().unwrap();
            assert!(snapshot.is_some());
            sm.recover_from_snapshot(&snapshot.unwrap()).unwrap();

            // Verify snapshot data is accessible
            for i in 1..=3 {
                let state = sm.get_state("default", "agent-1", &format!("before_{}", i)).unwrap();
                assert!(state.is_some());
            }

            // Verify data written after snapshot is also accessible
            for i in 1..=2 {
                let state = sm.get_state("default", "agent-1", &format!("after_{}", i)).unwrap();
                assert!(state.is_some());
                assert_eq!(state.unwrap().value.unwrap(), serde_json::json!(i + 100));
            }

            // Replay should include events after snapshot
            let events = sm.replay("default", "agent-1", Some(snapshot_ts), None).unwrap();
            // Should have events for writes after snapshot
            assert!(events.len() >= 2);
        }
    }

    #[test]
    fn test_crash_recovery() {
        use tempfile::TempDir;
        use crate::storage::RocksStorage;

        let temp_dir = TempDir::new().unwrap();
        let config = crate::storage::StorageConfig {
            data_dir: temp_dir.path().to_path_buf(),
            fsync_on_commit: true,
            snapshot_interval: 10,
            max_log_size: 1024 * 1024,
        };

        // Phase 1: Normal operation
        {
            let storage = Arc::new(RocksStorage::new(config.clone()).unwrap());
            let sm = StateMachine::new(storage);

            let txn_id = sm.begin_transaction(None).unwrap();
            sm.write(
                &txn_id,
                "default".to_string(),
                "agent-1".to_string(),
                "crash_test".to_string(),
                serde_json::json!({"status": "committed"}),
            ).unwrap();
            sm.commit(&txn_id).unwrap();
        }
        // Simulate crash (storage dropped)

        // Phase 2: Restart after crash
        {
            let storage = Arc::new(RocksStorage::new(config.clone()).unwrap());
            let sm = StateMachine::new(storage);

            // Data should still be accessible
            let state = sm.get_state("default", "agent-1", "crash_test").unwrap();
            assert!(state.is_some());
            assert_eq!(state.unwrap().value.unwrap()["status"], "committed");
        }
    }
}
