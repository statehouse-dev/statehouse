// Storage trait and implementations

use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;

use crate::types::*;

/// Snapshot format version for compatibility
pub const SNAPSHOT_VERSION: u32 = 1;

/// Storage configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StorageConfig {
    /// Data directory for persistent storage
    pub data_dir: PathBuf,
    /// Enable fsync on commit (slower but safer)
    pub fsync_on_commit: bool,
    /// Snapshot interval (number of commits)
    pub snapshot_interval: u64,
    /// Max log size before compaction (bytes)
    pub max_log_size: u64,
}

impl Default for StorageConfig {
    fn default() -> Self {
        Self {
            data_dir: PathBuf::from("./data"),
            fsync_on_commit: true,
            snapshot_interval: 1000,
            max_log_size: 100 * 1024 * 1024, // 100MB
        }
    }
}

/// State record stored in the database
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StateRecord {
    pub namespace: Namespace,
    pub agent_id: AgentId,
    pub key: Key,
    pub value: Option<serde_json::Value>,
    pub version: Version,
    pub commit_ts: CommitTs,
    pub deleted: bool,
}

/// Event log entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EventLogEntry {
    pub txn_id: TxnId,
    pub commit_ts: CommitTs,
    pub operations: Vec<OperationRecord>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OperationRecord {
    pub namespace: Namespace,
    pub agent_id: AgentId,
    pub key: Key,
    pub value: Option<serde_json::Value>,
    pub version: Version,
}

/// Snapshot metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SnapshotMetadata {
    /// Snapshot format version
    pub version: u32,
    /// Commit timestamp when snapshot was created
    pub snapshot_ts: CommitTs,
    /// Number of state records in snapshot
    pub record_count: usize,
    /// Timestamp when snapshot was created (system time)
    pub created_at: u64,
}

/// Complete snapshot of system state
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Snapshot {
    pub metadata: SnapshotMetadata,
    pub records: Vec<StateRecord>,
}

/// Storage abstraction for Statehouse
pub trait Storage: Send + Sync {
    /// Health check
    fn health_check(&self) -> Result<()>;

    /// Write a state record
    fn write_state(&self, record: StateRecord) -> Result<()>;

    /// Read a state record
    fn read_state(&self, record_id: &RecordId) -> Result<Option<StateRecord>>;

    /// Read state at specific version
    fn read_state_at_version(&self, record_id: &RecordId, version: Version) -> Result<Option<StateRecord>>;

    /// List all keys for an agent
    fn list_keys(&self, namespace: &str, agent_id: &str) -> Result<Vec<String>>;

    /// Scan keys with prefix
    fn scan_prefix(&self, namespace: &str, agent_id: &str, prefix: &str) -> Result<Vec<StateRecord>>;

    /// Append event to log
    fn append_event(&self, event: EventLogEntry) -> Result<()>;

    /// Replay events for an agent
    fn replay_events(&self, namespace: &str, agent_id: &str, start_ts: Option<CommitTs>, end_ts: Option<CommitTs>) -> Result<Vec<EventLogEntry>>;

    /// Get next commit timestamp
    fn next_commit_ts(&self) -> Result<CommitTs>;

    /// Flush writes to disk
    fn flush(&self) -> Result<()>;

    /// Create a snapshot of current state
    fn create_snapshot(&self) -> Result<Snapshot>;

    /// Save snapshot to disk
    fn save_snapshot(&self, snapshot: &Snapshot) -> Result<()>;

    /// Load latest snapshot from disk
    fn load_snapshot(&self) -> Result<Option<Snapshot>>;

    /// Get all state records (for snapshotting)
    fn get_all_state(&self) -> Result<Vec<StateRecord>>;
}

// ============================================================================
// In-Memory Storage (for tests)
// ============================================================================

use std::sync::{Arc, RwLock};

pub struct InMemoryStorage {
    state: Arc<RwLock<HashMap<RecordId, Vec<StateRecord>>>>,
    events: Arc<RwLock<Vec<EventLogEntry>>>,
    commit_ts_counter: Arc<RwLock<CommitTs>>,
}

impl InMemoryStorage {
    pub fn new() -> Self {
        Self {
            state: Arc::new(RwLock::new(HashMap::new())),
            events: Arc::new(RwLock::new(Vec::new())),
            commit_ts_counter: Arc::new(RwLock::new(0)),
        }
    }
}

impl Default for InMemoryStorage {
    fn default() -> Self {
        Self::new()
    }
}

impl Storage for InMemoryStorage {
    fn health_check(&self) -> Result<()> {
        Ok(())
    }

    fn write_state(&self, record: StateRecord) -> Result<()> {
        let mut state = self.state.write().unwrap();
        let record_id = RecordId::new(
            record.namespace.clone(),
            record.agent_id.clone(),
            record.key.clone(),
        );
        state.entry(record_id).or_insert_with(Vec::new).push(record);
        Ok(())
    }

    fn read_state(&self, record_id: &RecordId) -> Result<Option<StateRecord>> {
        let state = self.state.read().unwrap();
        Ok(state.get(record_id).and_then(|versions| versions.last().cloned()))
    }

    fn read_state_at_version(&self, record_id: &RecordId, version: Version) -> Result<Option<StateRecord>> {
        let state = self.state.read().unwrap();
        Ok(state.get(record_id).and_then(|versions| {
            versions.iter().find(|r| r.version == version).cloned()
        }))
    }

    fn list_keys(&self, namespace: &str, agent_id: &str) -> Result<Vec<String>> {
        let state = self.state.read().unwrap();
        let keys: Vec<String> = state
            .iter()
            .filter(|(id, versions)| {
                id.namespace == namespace
                    && id.agent_id == agent_id
                    && versions.last().map(|r| !r.deleted).unwrap_or(false)
            })
            .map(|(id, _)| id.key.clone())
            .collect();
        Ok(keys)
    }

    fn scan_prefix(&self, namespace: &str, agent_id: &str, prefix: &str) -> Result<Vec<StateRecord>> {
        let state = self.state.read().unwrap();
        let records: Vec<StateRecord> = state
            .iter()
            .filter(|(id, _)| {
                id.namespace == namespace
                    && id.agent_id == agent_id
                    && id.key.starts_with(prefix)
            })
            .filter_map(|(_, versions)| versions.last().cloned())
            .filter(|r| !r.deleted)
            .collect();
        Ok(records)
    }

    fn append_event(&self, event: EventLogEntry) -> Result<()> {
        let mut events = self.events.write().unwrap();
        events.push(event);
        Ok(())
    }

    fn replay_events(&self, namespace: &str, agent_id: &str, start_ts: Option<CommitTs>, end_ts: Option<CommitTs>) -> Result<Vec<EventLogEntry>> {
        let events = self.events.read().unwrap();
        let filtered: Vec<EventLogEntry> = events
            .iter()
            .filter(|e| {
                e.operations.iter().any(|op| {
                    op.namespace == namespace && op.agent_id == agent_id
                })
            })
            .filter(|e| {
                if let Some(start) = start_ts {
                    e.commit_ts >= start
                } else {
                    true
                }
            })
            .filter(|e| {
                if let Some(end) = end_ts {
                    e.commit_ts <= end
                } else {
                    true
                }
            })
            .cloned()
            .collect();
        Ok(filtered)
    }

    fn next_commit_ts(&self) -> Result<CommitTs> {
        let mut counter = self.commit_ts_counter.write().unwrap();
        *counter += 1;
        Ok(*counter)
    }

    fn flush(&self) -> Result<()> {
        Ok(())
    }

    fn create_snapshot(&self) -> Result<Snapshot> {
        let state = self.state.read().unwrap();
        let commit_ts_counter = self.commit_ts_counter.read().unwrap();
        
        // Collect all latest state records
        let mut records = Vec::new();
        for versions in state.values() {
            if let Some(record) = versions.last() {
                records.push(record.clone());
            }
        }

        let metadata = SnapshotMetadata {
            version: SNAPSHOT_VERSION,
            snapshot_ts: *commit_ts_counter,
            record_count: records.len(),
            created_at: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
        };

        Ok(Snapshot { metadata, records })
    }

    fn save_snapshot(&self, _snapshot: &Snapshot) -> Result<()> {
        // In-memory storage doesn't persist snapshots
        Ok(())
    }

    fn load_snapshot(&self) -> Result<Option<Snapshot>> {
        // In-memory storage doesn't persist snapshots
        Ok(None)
    }

    fn get_all_state(&self) -> Result<Vec<StateRecord>> {
        let state = self.state.read().unwrap();
        let mut records = Vec::new();
        for versions in state.values() {
            if let Some(record) = versions.last() {
                records.push(record.clone());
            }
        }
        Ok(records)
    }
}

// ============================================================================
// RocksDB Storage
// ============================================================================

use rocksdb::{Options, DB};

pub struct RocksStorage {
    db: Arc<DB>,
    config: StorageConfig,
    commit_ts_counter: Arc<RwLock<CommitTs>>,
}

impl RocksStorage {
    pub fn new(config: StorageConfig) -> Result<Self> {
        std::fs::create_dir_all(&config.data_dir)?;

        let mut opts = Options::default();
        opts.create_if_missing(true);
        opts.create_missing_column_families(true);

        let db_path = config.data_dir.join("rocksdb");
        let db = DB::open(&opts, db_path)?;

        // Load current commit timestamp
        let commit_ts = if let Some(value) = db.get(b"__commit_ts__")? {
            u64::from_be_bytes(value.try_into().unwrap_or([0; 8]))
        } else {
            0
        };

        Ok(Self {
            db: Arc::new(db),
            config,
            commit_ts_counter: Arc::new(RwLock::new(commit_ts)),
        })
    }

    /// Restore state from snapshot
    pub fn restore_from_snapshot(&self, snapshot: &Snapshot) -> Result<()> {
        // Write all records from snapshot
        for record in &snapshot.records {
            self.write_state(record.clone())?;
        }

        // Update commit timestamp counter
        let mut counter = self.commit_ts_counter.write().unwrap();
        *counter = snapshot.metadata.snapshot_ts;
        self.db.put(b"__commit_ts__", &counter.to_be_bytes())?;

        self.flush()?;
        Ok(())
    }

    /// Get path for snapshot file
    fn snapshot_path(&self) -> PathBuf {
        self.config.data_dir.join("snapshot.json")
    }

    fn state_key(record_id: &RecordId) -> Vec<u8> {
        format!("state:{}:{}:{}", record_id.namespace, record_id.agent_id, record_id.key).into_bytes()
    }

    fn version_key(record_id: &RecordId, version: Version) -> Vec<u8> {
        format!("version:{}:{}:{}:{:020}", record_id.namespace, record_id.agent_id, record_id.key, version).into_bytes()
    }

    fn event_key(commit_ts: CommitTs) -> Vec<u8> {
        format!("event:{:020}", commit_ts).into_bytes()
    }
}

impl Storage for RocksStorage {
    fn health_check(&self) -> Result<()> {
        // Try a simple read
        self.db.get(b"__health__")?;
        Ok(())
    }

    fn write_state(&self, record: StateRecord) -> Result<()> {
        let record_id = RecordId::new(
            record.namespace.clone(),
            record.agent_id.clone(),
            record.key.clone(),
        );

        // Write latest state
        let state_key = Self::state_key(&record_id);
        let state_value = serde_json::to_vec(&record)?;
        self.db.put(&state_key, &state_value)?;

        // Write versioned state
        let version_key = Self::version_key(&record_id, record.version);
        self.db.put(&version_key, &state_value)?;

        if self.config.fsync_on_commit {
            self.db.flush()?;
        }

        Ok(())
    }

    fn read_state(&self, record_id: &RecordId) -> Result<Option<StateRecord>> {
        let key = Self::state_key(record_id);
        if let Some(value) = self.db.get(&key)? {
            let record: StateRecord = serde_json::from_slice(&value)?;
            Ok(Some(record))
        } else {
            Ok(None)
        }
    }

    fn read_state_at_version(&self, record_id: &RecordId, version: Version) -> Result<Option<StateRecord>> {
        let key = Self::version_key(record_id, version);
        if let Some(value) = self.db.get(&key)? {
            let record: StateRecord = serde_json::from_slice(&value)?;
            Ok(Some(record))
        } else {
            Ok(None)
        }
    }

    fn list_keys(&self, namespace: &str, agent_id: &str) -> Result<Vec<String>> {
        let prefix = format!("state:{}:{}:", namespace, agent_id);
        let mut keys = Vec::new();

        let iter = self.db.prefix_iterator(prefix.as_bytes());
        for item in iter {
            let (key, value) = item?;
            let key_str = String::from_utf8_lossy(&key);
            if !key_str.starts_with(&prefix) {
                break;
            }

            let record: StateRecord = serde_json::from_slice(&value)?;
            if !record.deleted {
                keys.push(record.key);
            }
        }

        Ok(keys)
    }

    fn scan_prefix(&self, namespace: &str, agent_id: &str, prefix: &str) -> Result<Vec<StateRecord>> {
        let state_prefix = format!("state:{}:{}:{}", namespace, agent_id, prefix);
        let mut records = Vec::new();

        let iter = self.db.prefix_iterator(state_prefix.as_bytes());
        for item in iter {
            let (key, value) = item?;
            let key_str = String::from_utf8_lossy(&key);
            if !key_str.starts_with(&state_prefix) {
                break;
            }

            let record: StateRecord = serde_json::from_slice(&value)?;
            if !record.deleted {
                records.push(record);
            }
        }

        Ok(records)
    }

    fn append_event(&self, event: EventLogEntry) -> Result<()> {
        let key = Self::event_key(event.commit_ts);
        let value = serde_json::to_vec(&event)?;
        self.db.put(&key, &value)?;

        if self.config.fsync_on_commit {
            self.db.flush()?;
        }

        Ok(())
    }

    fn replay_events(&self, namespace: &str, agent_id: &str, start_ts: Option<CommitTs>, end_ts: Option<CommitTs>) -> Result<Vec<EventLogEntry>> {
        let start_key = if let Some(ts) = start_ts {
            Self::event_key(ts)
        } else {
            b"event:".to_vec()
        };

        let mut events = Vec::new();
        let iter = self.db.prefix_iterator(&start_key);

        for item in iter {
            let (key, value) = item?;
            let key_str = String::from_utf8_lossy(&key);
            if !key_str.starts_with("event:") {
                break;
            }

            let event: EventLogEntry = serde_json::from_slice(&value)?;

            // Check if event is relevant to this agent
            let relevant = event.operations.iter().any(|op| {
                op.namespace == namespace && op.agent_id == agent_id
            });

            if relevant {
                if let Some(end) = end_ts {
                    if event.commit_ts > end {
                        break;
                    }
                }
                events.push(event);
            }
        }

        Ok(events)
    }

    fn next_commit_ts(&self) -> Result<CommitTs> {
        let mut counter = self.commit_ts_counter.write().unwrap();
        *counter += 1;
        let ts = *counter;

        // Persist commit timestamp
        self.db.put(b"__commit_ts__", &ts.to_be_bytes())?;

        Ok(ts)
    }

    fn flush(&self) -> Result<()> {
        self.db.flush()?;
        Ok(())
    }

    fn create_snapshot(&self) -> Result<Snapshot> {
        let commit_ts_counter = self.commit_ts_counter.read().unwrap();
        let records = self.get_all_state()?;

        let metadata = SnapshotMetadata {
            version: SNAPSHOT_VERSION,
            snapshot_ts: *commit_ts_counter,
            record_count: records.len(),
            created_at: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
        };

        Ok(Snapshot { metadata, records })
    }

    fn save_snapshot(&self, snapshot: &Snapshot) -> Result<()> {
        let path = self.snapshot_path();
        let json = serde_json::to_string_pretty(snapshot)?;
        std::fs::write(path, json)?;
        Ok(())
    }

    fn load_snapshot(&self) -> Result<Option<Snapshot>> {
        let path = self.snapshot_path();
        
        if !path.exists() {
            return Ok(None);
        }

        let json = std::fs::read_to_string(path)?;
        let snapshot: Snapshot = serde_json::from_str(&json)?;

        // Verify snapshot version
        if snapshot.metadata.version != SNAPSHOT_VERSION {
            return Err(anyhow::anyhow!(
                "Snapshot version mismatch: expected {}, got {}",
                SNAPSHOT_VERSION,
                snapshot.metadata.version
            ));
        }

        Ok(Some(snapshot))
    }

    fn get_all_state(&self) -> Result<Vec<StateRecord>> {
        let mut records = Vec::new();
        let iter = self.db.prefix_iterator(b"state:");

        for item in iter {
            let (key, value) = item?;
            let key_str = String::from_utf8_lossy(&key);
            
            if !key_str.starts_with("state:") {
                break;
            }

            let record: StateRecord = serde_json::from_slice(&value)?;
            records.push(record);
        }

        Ok(records)
    }
}
