# gRPC Architecture

This document describes Statehouse's gRPC-based architecture and client-server communication patterns.

## Overview

Statehouse uses gRPC as its primary communication protocol:

```
┌─────────────────┐          gRPC/HTTP2           ┌──────────────────┐
│  Python Client  │ ◄──────────────────────────► │  statehoused     │
│  (statehouse)   │                               │  (Rust daemon)   │
└─────────────────┘                               └──────────────────┘
                                                           │
                                                           ▼
                                                   ┌──────────────────┐
                                                   │  RocksDB         │
                                                   │  (or InMemory)   │
                                                   └──────────────────┘
```

## Why gRPC?

1. **Strongly typed contracts** - Protocol Buffers define exact API shape
2. **Language agnostic** - Generate clients for any language  
3. **Efficient** - Binary protocol with HTTP/2 multiplexing
4. **Streaming** - Native support for server-streaming (e.g., replay)
5. **Tooling** - Excellent debugging and testing tools

## Architecture Layers

### Layer 1: Protocol Buffers (proto/)

The **source of truth** for the API.

```
proto/
└── statehouse/
    └── v1/
        └── statehouse.proto    # Complete service definition
```

Key aspects:
- All RPCs defined in `.proto` file
- Versioned under `statehouse.v1` package
- Messages use protobuf `Struct` for JSON values
- Explicit error codes and status messages

### Layer 2: Rust Daemon (crates/statehouse-daemon/)

The gRPC server implementation.

**Components:**

1. **tonic server** - HTTP/2 + gRPC handler
2. **Service implementation** - `StatehouseServiceImpl`
3. **State machine** - Single-writer concurrency model
4. **Storage** - RocksDB or InMemory backend

**Flow:**

```
gRPC Request
    │
    ▼
Service Handler (service.rs)
    │
    ├─ Convert protobuf → Rust types
    │
    ▼
State Machine (state_machine.rs)
    │
    ├─ Transaction management
    ├─ Version control
    ├─ Event log
    │
    ▼
Storage (storage.rs)
    │
    └─ RocksDB / InMemory
```

### Layer 3: Python SDK (python/statehouse/)

**Clean Pythonic wrapper** - no gRPC visible to users.

```python
# User writes this:
with client.begin_transaction() as tx:
    tx.write(agent_id="a1", key="k", value={"x": 1})

# SDK handles:
# - gRPC channel management
# - BeginTransaction RPC
# - WriteRequest protobuf construction  
# - CommitRequest RPC
# - Error conversion
# - Type conversion (dict ↔ protobuf.Struct)
```

**Key Design Decisions:**

1. **No protobuf imports in user code**
   - Generated stubs are internal (`_generated/`)
   - User never sees `pb2` or `pb2_grpc`

2. **Pythonic types**
   - `dict` instead of `protobuf.Struct`
   - `dataclass` for results
   - Custom exceptions (not gRPC status codes)

3. **Context managers**
   - `with client.transaction()` for auto-commit
   - `async with` for async operations

## Service Definition

### RPCs

From `statehouse.proto`:

```protobuf
service StatehouseService {
  // Health and metadata
  rpc Health(HealthRequest) returns (HealthResponse);
  rpc Version(VersionRequest) returns (VersionResponse);
  
  // Transaction lifecycle
  rpc BeginTransaction(BeginTransactionRequest) returns (BeginTransactionResponse);
  rpc Write(WriteRequest) returns (WriteResponse);
  rpc Delete(DeleteRequest) returns (DeleteResponse);
  rpc Commit(CommitRequest) returns (CommitResponse);
  rpc Abort(AbortRequest) returns (AbortResponse);
  
  // Reads
  rpc GetState(GetStateRequest) returns (GetStateResponse);
  rpc GetStateAtVersion(GetStateAtVersionRequest) returns (GetStateAtVersionResponse);
  rpc ListKeys(ListKeysRequest) returns (ListKeysResponse);
  rpc ScanPrefix(ScanPrefixRequest) returns (ScanPrefixResponse);
  
  // Replay (streaming)
  rpc Replay(ReplayRequest) returns (stream ReplayEvent);
}
```

### Request/Response Patterns

#### 1. Unary RPC (most operations)

```
Client ──────request──────► Server
       ◄─────response───────
```

Example:
```python
response = stub.GetState(request)
```

#### 2. Server Streaming (replay)

```
Client ──────request──────► Server
       ◄─────event 1────────
       ◄─────event 2────────
       ◄─────event 3────────
       ◄─────...────────────
```

Example:
```python
for event in stub.Replay(request):
    print(event)
```

## Data Flow Examples

### Write Transaction

```
1. Client: BeginTransaction()
   ◄─ Server: {txn_id: "uuid"}

2. Client: Write(txn_id, agent_id, key, value)
   ◄─ Server: {ok}

3. Client: Write(txn_id, agent_id, key2, value2)  
   ◄─ Server: {ok}

4. Client: Commit(txn_id)
   ◄─ Server: {commit_ts: 12345}
```

**State machine behavior:**
- Operations staged in memory during 2-3
- Atomically applied to storage on step 4
- Event appended to log
- Version counters incremented

### Read Latest

```
Client: GetState(namespace, agent_id, key)
   ◄─ Server: {
        namespace,
        agent_id,
        key,
        value,
        version,
        commit_ts
      }
```

**State machine behavior:**
- Read latest version from storage
- No locks required (immutable reads)

### Replay (Streaming)

```
Client: Replay(namespace, agent_id, from_ts, to_ts)
   ◄─ Server: event stream [
        {txn_id, commit_ts, operations: [{...}, {...}]},
        {txn_id, commit_ts, operations: [{...}]},
        ...
      ]
```

**State machine behavior:**
- Storage scans event log
- Filters by namespace, agent_id, time range
- Streams results incrementally (no buffering)
- Backpressure handled by gRPC/HTTP2

## Error Handling

### Error Codes

Defined in `statehouse.proto`:

```protobuf
enum ErrorCode {
  OK = 0;
  NOT_FOUND = 1;
  ALREADY_EXISTS = 2;
  TRANSACTION_EXPIRED = 3;
  INVALID_ARGUMENT = 4;
  INTERNAL_ERROR = 5;
}
```

### gRPC Status Mapping

| ErrorCode          | gRPC Status       |
|--------------------|-------------------|
| OK                 | OK                |
| NOT_FOUND          | NOT_FOUND         |
| ALREADY_EXISTS     | ALREADY_EXISTS    |
| TRANSACTION_EXPIRED| DEADLINE_EXCEEDED |
| INVALID_ARGUMENT   | INVALID_ARGUMENT  |
| INTERNAL_ERROR     | INTERNAL          |

### Python SDK Translation

gRPC status codes are translated to custom exceptions:

```python
grpc.StatusCode.NOT_FOUND       → NotFoundError
grpc.StatusCode.DEADLINE_EXCEEDED → TransactionError  
grpc.StatusCode.INVALID_ARGUMENT  → StatehouseError
grpc.StatusCode.INTERNAL          → StatehouseError
grpc.StatusCode.UNAVAILABLE       → ConnectionError
```

User code:
```python
try:
    result = client.get_state(...)
except NotFoundError:
    # Handle missing key
except ConnectionError:
    # Handle daemon down
```

## Concurrency Model

### Server-Side (Rust)

**Single-writer state machine:**
- All mutations serialize through state machine
- Reads are concurrent (immutable data)
- No distributed locks needed
- Simple, correct, fast

**gRPC threading:**
- tonic uses tokio async runtime
- Multiple concurrent RPC handlers
- State machine uses `Arc<RwLock<...>>` for shared state
- Writes take exclusive lock
- Reads take shared lock

### Client-Side (Python)

**Synchronous client:**
```python
client = Statehouse()  # Creates gRPC channel
result = client.get_state(...)  # Blocking call
```

**Async client (if needed):**
```python
client = StatehouseAsync()
result = await client.get_state(...)
```

## Performance Characteristics

### Latency

Typical latencies (local daemon):
- **Health check:** < 1ms
- **Get state:** 1-2ms
- **Transaction commit (1 op):** 2-5ms
- **Transaction commit (10 ops):** 3-7ms
- **Replay (1000 events):** 10-50ms

### Throughput

Single daemon instance:
- **Reads:** 10,000+ ops/sec
- **Writes:** 2,000-5,000 ops/sec (fsync on)
- **Writes:** 20,000+ ops/sec (fsync off, memory only)

### Bottlenecks

1. **Storage fsync** - dominates write latency
2. **Serialization** - protobuf encoding/decoding
3. **Single-writer** - write transactions serialize

**Mitigations:**
- Batch multiple writes in one transaction
- Use async fsync if durability SLA allows
- Run multiple daemon instances (future: sharding)

## Connection Management

### Client Lifecycle

```python
# 1. Create client
client = Statehouse(url="localhost:50051")

# 2. Use client (reuses connection)
result = client.get_state(...)
result2 = client.list_keys(...)

# 3. Close when done (optional)
client.close()
```

### Connection Pooling

gRPC handles connection pooling automatically:
- HTTP/2 multiplexing (multiple RPCs on one connection)
- Automatic reconnection on failure
- Keepalive pings

### Timeouts

**Server-side:**
- Transaction timeout (default: 30s)
- Enforced by state machine

**Client-side:**
- RPC timeout (configurable)
- Python SDK default: 30s

```python
client = Statehouse(url="localhost:50051", timeout=60)
```

## Security

### Current State (MVP)

- **No authentication** - insecure channel
- **No encryption** - plaintext gRPC

Suitable for:
- Local development
- Trusted internal networks
- Single-tenant deployments

### Production Recommendations

1. **TLS encryption:**
   ```python
   credentials = grpc.ssl_channel_credentials(...)
   channel = grpc.secure_channel(addr, credentials)
   ```

2. **Authentication:**
   - API keys via metadata
   - mTLS client certificates
   - Token-based auth

3. **Network isolation:**
   - Run daemon in private network
   - Firewall gRPC port (50051)
   - VPN or SSH tunnel

## Monitoring and Debugging

### gRPC Tools

1. **grpcurl** - CLI client for testing:
   ```bash
   grpcurl -plaintext localhost:50051 \
     statehouse.v1.StatehouseService/Health
   ```

2. **grpcui** - Web UI for exploring service:
   ```bash
   grpcui -plaintext localhost:50051
   ```

3. **gRPC reflection** (if enabled):
   ```bash
   grpcurl -plaintext localhost:50051 list
   ```

### Logging

Set `RUST_LOG` for daemon logs:
```bash
RUST_LOG=debug ./statehoused
```

Structured logs include:
- Transaction lifecycle (begin, commit, abort)
- RPC handler entry/exit
- Storage operations
- Error details

### Metrics (Future)

Potential Prometheus metrics:
- `statehouse_transactions_total{status}`
- `statehouse_operations_total{type}`
- `statehouse_rpc_duration_seconds{rpc}`
- `statehouse_storage_bytes_written_total`

## Language Clients

### Current Support

- **Python** ✅ - Full SDK with clean API
- **Rust** - Can use `statehouse-proto` crate directly

### Future Clients

Easy to add via protoc codegen:
- **TypeScript/Node.js** - `@grpc/grpc-js` + protoc-gen-ts
- **Go** - `google.golang.org/grpc` + protoc-gen-go
- **Java** - `grpc-java`
- **Ruby** - `grpc` gem

All share same `.proto` file = guaranteed compatibility.

## Migration and Versioning

### Protocol Evolution

Breaking changes require new package version:
- `statehouse.v1` → `statehouse.v2`
- Old clients continue to work
- Gradual migration path

### Non-Breaking Changes

Can be added to `v1`:
- New optional fields
- New RPCs
- New enum values (with unknown handling)

### Storage Migration

Daemon handles storage version upgrades:
- Snapshot format versioning
- Event log format versioning
- Backward-compatible readers

## See Also

- [Protocol Buffers](../crates/statehouse-proto/proto/statehouse/v1/statehouse.proto) - API contract
- [Replay Semantics](replay_semantics.md) - Event log behavior
- [Python SDK](../python/README.md) - Client usage
- [Architecture](architecture.md) - System design
