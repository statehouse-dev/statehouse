# Statehouse Architecture

> Design documentation for the Statehouse MVP

---

## System Overview

Statehouse is a **strongly consistent state and memory engine** for AI agents.

Architecture principles:
1. **gRPC-first**: All communication via gRPC (no REST, no HTTP)
2. **Single-writer core**: One logical writer ensures consistency
3. **Append-only foundation**: Event log is the source of truth
4. **Language-agnostic protocol**: Protobuf defines the contract
5. **Client library abstraction**: Hide gRPC complexity from users

---

## Component Architecture

```
┌─────────────────────────────────────────────────────┐
│                   User Code                         │
│              (Python SDK, future: Go, JS)           │
└────────────────────┬────────────────────────────────┘
                     │ Clean object API
                     │ (no gRPC visible)
                     │
┌────────────────────▼────────────────────────────────┐
│              Python SDK Layer                        │
│  - Statehouse client class                          │
│  - Transaction wrapper                               │
│  - Protobuf <-> dict conversion                      │
│  - Error mapping                                     │
└────────────────────┬────────────────────────────────┘
                     │ gRPC (internal)
                     │
┌────────────────────▼────────────────────────────────┐
│           statehoused (Rust gRPC server)            │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │          gRPC Service Layer                  │  │
│  │  - StatehouseService impl                    │  │
│  │  - Request validation                        │  │
│  │  - Error mapping                             │  │
│  └─────────────────┬────────────────────────────┘  │
│                    │                                 │
│  ┌─────────────────▼────────────────────────────┐  │
│  │         State Machine (single writer)        │  │
│  │  - Transaction staging                       │  │
│  │  - Commit -> event batch                     │  │
│  │  - Apply loop (deterministic)                │  │
│  │  - Versioning                                │  │
│  └─────────────────┬────────────────────────────┘  │
│                    │                                 │
│  ┌─────────────────▼────────────────────────────┐  │
│  │         Storage Engine (RocksDB)             │  │
│  │  - K/V persistence                           │  │
│  │  - Event log                                 │  │
│  │  - Snapshots                                 │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## Data Model

### Identity Tuple

Every record is uniquely identified by:

```
(namespace, agent_id, key) -> value
```

- **Namespace**: Logical isolation boundary (default: "default")
- **AgentId**: The agent or workflow instance
- **Key**: The state key

### Versioning

Every write increments a version counter:

```
(namespace, agent_id, key) -> (value, version, commit_ts)
```

- **Version**: Monotonic u64, per-(namespace, agent_id, key)
- **CommitTs**: Logical timestamp when committed

### Event Log

All commits are appended to an immutable event log:

```rust
Event {
  txn_id: TxnId,
  commit_ts: CommitTs,
  operations: Vec<Operation>,
}

Operation {
  namespace: String,
  agent_id: String,
  key: String,
  value: Option<Struct>,  // None = delete
  version: u64,
}
```

---

## Transaction Lifecycle

1. **Begin**: Client requests `txn_id` from server
2. **Stage**: Client sends `Write` and `Delete` requests (txn_id included)
3. **Commit**: Client sends `Commit` request
4. **Apply**: Server atomically applies all staged operations
5. **Event**: Server appends event to log
6. **Response**: Server returns success/failure to client

### Failure Modes

- **Timeout**: Uncommitted transactions auto-abort after TTL
- **Conflict**: (Not in MVP, always succeeds for now)
- **Crash**: Uncommitted transactions lost (expected)

---

## Consistency Model

### Strong Consistency

- All writes go through a single logical writer
- Commits are serialized
- Read-after-write always sees the latest committed value

### No Distributed Consensus (MVP)

- Single-node only
- No clustering, no Raft
- State lives on one machine

---

## Replay

Replay reconstructs the state of an agent by replaying its event log.

**Use cases**:
- Debugging agent behavior
- Auditing decisions
- Reproducing failures

**Mechanism**:
- Server streams events in commit order
- Client reconstructs state incrementally
- Deterministic if operations are deterministic

---

## Storage Layout

```
data/
  rocksdb/
    events/       # Event log (immutable)
    state/        # Latest state snapshot
    metadata/     # Version, config, etc.
  snapshots/
    snapshot-001.db
    snapshot-002.db
```

---

## Invariants

Statehouse's correctness depends on maintaining these fundamental invariants:

### 1. Committed Write is Immediately Readable

**Statement**: Once a transaction commits successfully, all subsequent reads must see the committed values.

**Guarantees**:
- `Commit()` returns success → state is durable and visible
- No read-after-write races
- No "eventual consistency" delays

**Implementation**:
- Single-writer state machine
- Synchronous commit to storage
- Linearizable reads

**Violation would mean**: A client commits data but can't read it back → unacceptable.

---

### 2. No Partial Transactions Visible

**Statement**: Either all operations in a transaction are visible, or none are.

**Guarantees**:
- Atomicity: transactions are all-or-nothing
- No torn reads (seeing half a transaction's writes)
- Failure during commit → entire transaction aborted

**Implementation**:
- Transaction staging buffer
- Atomic batch commit
- No intermediate state exposed to reads

**Violation would mean**: Agent sees inconsistent state mid-transaction → data corruption.

---

### 3. Replay is Deterministic

**Statement**: Given the same event log, replay produces the same final state.

**Guarantees**:
- Event log is the source of truth
- Applying events in order always yields identical results
- No hidden state or non-deterministic operations

**Implementation**:
- Events are immutable once committed
- Total ordering via `commit_ts`
- No random or time-based state in apply logic

**Violation would mean**: Replay debugging is useless, state can't be reconstructed.

---

### 4. Order of Events is Total Per Agent

**Statement**: For any given agent, all events have a strict total order.

**Guarantees**:
- No concurrent writes to the same agent (single-writer)
- Event sequence is unambiguous
- Replay always sees events in the same order

**Implementation**:
- Single-threaded apply loop
- Monotonic `commit_ts` per commit
- Agent events serialized by state machine

**Violation would mean**: Non-deterministic replay, race conditions.

---

### 5. Daemon is Single-Writer Internally

**Statement**: Only one logical writer can modify state at a time.

**Guarantees**:
- No internal concurrency bugs
- No locks needed (simpler correctness)
- Strong consistency without coordination

**Implementation**:
- Single state machine thread
- All commits go through one apply loop
- gRPC handlers enqueue requests, don't mutate directly

**Violation would mean**: Data races, corrupted state, lost writes.

---

### 6. Python SDK Exposes No gRPC Concepts

**Statement**: Users never interact with protobuf types, gRPC stubs, or channels directly.

**Guarantees**:
- Clean, Pythonic API
- No `*_pb2.py` imports in user code
- Errors are Python exceptions, not gRPC status codes

**Implementation**:
- SDK wraps all gRPC calls internally
- Converts `Struct` ↔ `dict` transparently
- Maps gRPC errors to custom exceptions

**Violation would mean**: Bad developer experience, leaky abstraction.

---

## Why These Invariants Matter

These are **not** implementation details — they are **guarantees** to users:

1. **Correctness**: State is always consistent
2. **Debuggability**: Replay works reliably
3. **Simplicity**: No distributed systems complexity in MVP
4. **Trust**: Agent decisions are auditable and reproducible

If any invariant is violated, Statehouse's core value proposition breaks.

---

## Non-goals (MVP)

- Clustering
- Sharding
- Multi-node replication
- SQL query layer
- Vector search
- Authentication/Authorization
- Encryption at rest
- Network-level security

These are intentionally deferred to post-MVP.

---

**Status**: This document will evolve as the implementation progresses.
