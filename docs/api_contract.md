# Statehouse API Contract

> Language-agnostic API specification for Statehouse

---

## Design Principles

1. **gRPC is the source of truth**: Protobuf defines the contract
2. **No gRPC in user code**: Client SDKs hide protobuf types
3. **Explicit over implicit**: No magic, clear semantics
4. **Errors are values**: Structured error handling

---

## Core Types (Conceptual)

These types are defined in protobuf (see `crates/statehouse-proto/proto/statehouse/v1/statehouse.proto`).

### Namespace
- **Type**: `string`
- **Default**: `"default"`
- **Purpose**: Logical isolation boundary for multi-agent systems

### AgentId
- **Type**: `string`
- **Purpose**: Unique identifier for an agent or workflow instance
- **Examples**: `"agent-123"`, `"workflow-abc"`, `"research-task-456"`

### Key
- **Type**: `string`
- **Purpose**: State key within an agent's namespace
- **Examples**: `"memory"`, `"context"`, `"task_status"`

### Record Identity Tuple
- **Definition**: `(namespace, agent_id, key)`
- **Uniqueness**: This tuple uniquely identifies a state record
- **Scoping**: All operations are scoped to this identity

### Value
- **Type**: JSON-compatible structure (protobuf `Struct`)
- **Purpose**: Arbitrary state payload
- **Max size**: Configurable (default: 1MB)
- **Representation**: Protobuf `google.protobuf.Struct` for language-agnostic JSON

### Version
- **Type**: `u64`
- **Purpose**: Monotonic version counter per `(namespace, agent_id, key)`
- **Semantics**: Increments on every write to that key

### TxnId
- **Type**: `string` (UUID recommended)
- **Purpose**: Unique transaction identifier
- **Lifecycle**: Assigned by server on `BeginTransaction`

### CommitTs
- **Type**: `u64` (logical timestamp)
- **Purpose**: Commit ordering
- **Semantics**: Monotonically increasing, global

### Tombstone Semantics
- **Concept**: Deletes are represented as tombstones, not physical removal
- **Behavior**: 
  - A delete operation sets `value = None` in the event log
  - The key is marked as "deleted" but the history is preserved
  - Reading a deleted key returns `exists = false`
  - Deleted keys do not appear in `ListKeys` results
- **Replay**: Tombstones are replayed as delete operations
- **Compaction**: Physical removal may happen during snapshot/compaction (future)

---

## API Operations

### 1. Health Check

**RPC**: `Health`

**Request**: `HealthRequest {}`

**Response**: `HealthResponse { status: string }`

**Purpose**: Verify daemon is running

---

### 2. Version

**RPC**: `Version`

**Request**: `VersionRequest {}`

**Response**: `VersionResponse { version: string, git_sha: string }`

**Purpose**: Retrieve server version and build info

---

### 3. Begin Transaction

**RPC**: `BeginTransaction`

**Request**: `BeginTransactionRequest { timeout_ms?: u64 }`

**Response**: `BeginTransactionResponse { txn_id: string }`

**Semantics**:
- Server assigns unique `txn_id`
- Transaction auto-aborts after `timeout_ms` if not committed
- Default timeout: 30 seconds

---

### 4. Write State

**RPC**: `Write`

**Request**:
```protobuf
WriteRequest {
  txn_id: string,
  namespace: string,
  agent_id: string,
  key: string,
  value: Struct,
}
```

**Response**: `WriteResponse {}`

**Semantics**:
- Stages a write in the transaction
- Does not commit immediately
- Overwrites previous value for this key (within txn)

---

### 5. Delete State

**RPC**: `Delete`

**Request**:
```protobuf
DeleteRequest {
  txn_id: string,
  namespace: string,
  agent_id: string,
  key: string,
}
```

**Response**: `DeleteResponse {}`

**Semantics**:
- Stages a delete (tombstone) in the transaction
- Does not commit immediately

---

### 6. Commit Transaction

**RPC**: `Commit`

**Request**: `CommitRequest { txn_id: string }`

**Response**: `CommitResponse { commit_ts: u64 }`

**Semantics**:
- Atomically applies all staged operations
- Appends event to log
- Returns commit timestamp
- Transaction is now visible to reads

**Errors**:
- Transaction not found (expired or invalid)
- Transaction already committed
- Transaction aborted

---

### 7. Abort Transaction

**RPC**: `Abort`

**Request**: `AbortRequest { txn_id: string }`

**Response**: `AbortResponse {}`

**Semantics**:
- Discards all staged operations
- Idempotent (aborting twice is safe)

---

### 8. Get State (Latest)

**RPC**: `GetState`

**Request**:
```protobuf
GetStateRequest {
  namespace: string,
  agent_id: string,
  key: string,
}
```

**Response**:
```protobuf
GetStateResponse {
  value?: Struct,
  version: u64,
  commit_ts: u64,
  exists: bool,
}
```

**Semantics**:
- Returns latest committed value
- If key does not exist, `exists = false`

---

### 9. Get State at Version

**RPC**: `GetStateAtVersion`

**Request**:
```protobuf
GetStateAtVersionRequest {
  namespace: string,
  agent_id: string,
  key: string,
  version: u64,
}
```

**Response**: (same as `GetStateResponse`)

**Semantics**:
- Returns value at specific version
- Error if version does not exist

---

### 10. List Keys

**RPC**: `ListKeys`

**Request**:
```protobuf
ListKeysRequest {
  namespace: string,
  agent_id: string,
}
```

**Response**:
```protobuf
ListKeysResponse {
  keys: Vec<string>,
}
```

**Semantics**:
- Returns all keys for an agent (latest snapshot)
- Excludes deleted keys

---

### 11. Scan Prefix

**RPC**: `ScanPrefix`

**Request**:
```protobuf
ScanPrefixRequest {
  namespace: string,
  agent_id: string,
  prefix: string,
}
```

**Response**:
```protobuf
ScanPrefixResponse {
  entries: Vec<StateEntry>,
}

StateEntry {
  key: string,
  value: Struct,
  version: u64,
  commit_ts: u64,
}
```

**Semantics**:
- Returns all keys matching prefix
- Lexicographic order

---

### 12. Replay (Streaming)

**RPC**: `Replay` (server-streaming)

**Request**:
```protobuf
ReplayRequest {
  namespace: string,
  agent_id: string,
  start_ts?: u64,
  end_ts?: u64,
}
```

**Response Stream**:
```protobuf
ReplayEvent {
  txn_id: string,
  commit_ts: u64,
  operations: Vec<Operation>,
}

Operation {
  key: string,
  value?: Struct,  // None = delete
  version: u64,
}
```

**Semantics**:
- Streams events in commit order
- If `start_ts` is omitted, starts from beginning
- If `end_ts` is omitted, streams until current state

---

## Error Handling

### Error Structure

```protobuf
StatehouseError {
  code: ErrorCode,
  message: string,
  details?: map<string, string>,
}

enum ErrorCode {
  UNKNOWN = 0,
  INVALID_REQUEST = 1,
  TXN_NOT_FOUND = 2,
  TXN_EXPIRED = 3,
  TXN_ALREADY_COMMITTED = 4,
  KEY_NOT_FOUND = 5,
  VERSION_NOT_FOUND = 6,
  STORAGE_ERROR = 7,
  INTERNAL_ERROR = 8,
}
```

### gRPC Status Code Mapping

| ErrorCode | gRPC Status |
|-----------|-------------|
| INVALID_REQUEST | INVALID_ARGUMENT |
| TXN_NOT_FOUND | NOT_FOUND |
| TXN_EXPIRED | DEADLINE_EXCEEDED |
| TXN_ALREADY_COMMITTED | FAILED_PRECONDITION |
| KEY_NOT_FOUND | NOT_FOUND |
| VERSION_NOT_FOUND | NOT_FOUND |
| STORAGE_ERROR | INTERNAL |
| INTERNAL_ERROR | INTERNAL |

---

## Python SDK API (User-Facing)

The Python SDK hides all gRPC/protobuf details.

### Example Usage

```python
from statehouse import Statehouse

client = Statehouse(url="localhost:50051")

# Write
tx = client.begin_transaction()
tx.write(agent_id="agent-1", key="memory", value={"fact": "sky is blue"})
tx.commit()

# Read
state = client.get_state(agent_id="agent-1", key="memory")
print(state.value)  # {"fact": "sky is blue"}

# Replay
for event in client.replay(agent_id="agent-1"):
    print(event.commit_ts, event.operations)
```

**Key Points**:
- No `namespace` visible (defaults to "default")
- No protobuf types in user code
- Exceptions instead of gRPC status codes
- Pythonic API (snake_case, context managers, etc.)

---

**Status**: This contract is the foundation for all Statehouse implementations. Changes require careful versioning.
