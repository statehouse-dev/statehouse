# Replay Semantics

This document defines the exact behavior and guarantees of Statehouse's replay functionality.

## Overview

**Replay** is the ability to retrieve the complete history of state changes for an agent in chronological order.

```python
for event in client.replay(agent_id="agent-1"):
    print(f"[{event.timestamp}] {event.operation.name} {event.key}")
```

Replay is essential for:
- **Debugging** - understand what an agent did
- **Auditing** - compliance and accountability
- **Provenance** - trace decisions back to their inputs
- **Recovery** - rebuild state from scratch
- **Testing** - verify agent behavior deterministically

## Core Guarantees

### 1. Completeness

**Guarantee:** Replay returns **all** committed operations for the specified agent.

- Every successful `commit()` is recorded
- No operations are lost (subject to storage durability)
- Aborted transactions are **not** included

```python
# This transaction will appear in replay:
with client.begin_transaction() as tx:
    tx.write(agent_id="a1", key="k", value={"x": 1})
# Auto-commits

# This transaction will NOT appear in replay:
tx = client.begin_transaction()
tx.write(agent_id="a1", key="k", value={"x": 2})
tx.abort()  # Discarded
```

### 2. Ordering

**Guarantee:** Events are returned in **commit timestamp order**.

The order is determined by:
1. When the transaction was committed
2. A monotonically increasing `commit_ts`

Not by:
- When operations were staged
- When BeginTransaction was called
- Wall-clock time of client

**Example:**

```python
# Transaction A started first
tx_a = client.begin_transaction()
tx_a.write(agent_id="a1", key="ka", value={"x": 1})

# Transaction B started second
tx_b = client.begin_transaction()
tx_b.write(agent_id="a1", key="kb", value={"y": 2})

# But B commits first!
tx_b.commit()  # commit_ts = 10
tx_a.commit()  # commit_ts = 11

# Replay order: B before A
for event in client.replay(agent_id="a1"):
    # Event 1: commit_ts=10, key=kb
    # Event 2: commit_ts=11, key=ka
```

### 3. Atomicity

**Guarantee:** Multi-operation transactions appear as a single event.

```python
with client.begin_transaction() as tx:
    tx.write(agent_id="a1", key="k1", value={"x": 1})
    tx.write(agent_id="a1", key="k2", value={"y": 2})
    tx.delete(agent_id="a1", key="k3")

# Replay shows ONE event with three operations:
for event in client.replay(agent_id="a1"):
    print(event.operations)  # [write(k1), write(k2), delete(k3)]
```

All operations in a transaction have:
- Same `commit_ts`
- Same `txn_id`
- Appear together in replay

### 4. Isolation

**Guarantee:** Replay for one agent does not include other agents' events.

```python
# Agent 1 writes
with client.begin_transaction() as tx:
    tx.write(agent_id="agent-1", key="k", value={"x": 1})

# Agent 2 writes  
with client.begin_transaction() as tx:
    tx.write(agent_id="agent-2", key="k", value={"x": 2})

# Replay for agent-1 only shows agent-1's events
events = list(client.replay(agent_id="agent-1"))
assert all(e.operations[0].agent_id == "agent-1" for e in events)
```

**Note:** Namespace isolation works the same way.

### 5. Consistency

**Guarantee:** Replay reflects **committed** state exactly.

If you:
1. Replay all events
2. Apply them in order
3. You will reconstruct current state precisely

```python
# Write some data
with client.begin_transaction() as tx:
    tx.write(agent_id="a1", key="k1", value={"x": 1})
with client.begin_transaction() as tx:
    tx.write(agent_id="a1", key="k1", value={"x": 2})  # Update

# Replay shows both writes
events = list(client.replay(agent_id="a1"))
assert len(events) == 2

# Final state matches last replay event
state = client.get_state(agent_id="a1", key="k1")
assert state.value == events[-1].operations[0].value
```

## Event Structure

Each event returned by replay contains:

```python
@dataclass
class ReplayEvent:
    txn_id: str          # Transaction ID
    commit_ts: int       # Commit timestamp (monotonic)
    timestamp: str       # ISO timestamp (for display)
    operations: List[Operation]  # Operations in this transaction
```

Each operation:

```python
@dataclass
class Operation:
    type: OperationType  # WRITE or DELETE
    namespace: str
    agent_id: str
    key: str
    value: Optional[dict]  # None for DELETE
    version: int         # Version number for this key
```

## Filtering

### By Time Range

```python
# Only events between two timestamps
for event in client.replay(
    agent_id="a1",
    from_timestamp="2026-02-07T10:00:00Z",
    to_timestamp="2026-02-07T11:00:00Z"
):
    print(event)
```

**Semantics:**
- Inclusive of `from_timestamp`
- Exclusive of `to_timestamp`
- Uses commit timestamp, not wall-clock time

### By Namespace

```python
# Only events in "production" namespace
for event in client.replay(
    agent_id="a1",
    namespace="production"
):
    print(event)
```

### By Agent

Replay is always filtered by agent - this is required.

```python
# Get ALL events for agent-1 across all namespaces
for namespace in ["dev", "staging", "prod"]:
    for event in client.replay(agent_id="a1", namespace=namespace):
        print(event)
```

## Performance Characteristics

### Streaming

Replay uses **server-side streaming**:
- Events are sent incrementally
- Client processes them one-by-one
- No buffering of entire history in memory

```python
# Memory-efficient for large histories
for event in client.replay(agent_id="a1"):
    process(event)  # Processed immediately
    # Previous events are garbage-collected
```

### Scan Efficiency

Replay scans the event log sequentially:
- **Fast** for small time ranges
- **Fast** for recent events
- **Slower** for full history of old agents

**Optimization tips:**
1. Use time range filters when possible
2. Replay from last known checkpoint
3. Create periodic snapshots for old agents

### Backpressure

gRPC handles backpressure automatically:
- If client is slow, server pauses sending
- No events are lost
- Memory usage bounded

## Use Cases

### 1. Debugging

**Problem:** Agent made a wrong decision. Why?

```python
# See all agent actions leading to bad state
for event in client.replay(agent_id="problematic-agent"):
    print(f"[{event.timestamp}] {event.operations}")
    
# Find the problematic write
for event in client.replay(agent_id="problematic-agent"):
    for op in event.operations:
        if op.key == "decision":
            print(f"Decision at {event.timestamp}: {op.value}")
```

### 2. Auditing

**Problem:** Need to prove what agent did for compliance.

```python
# Export complete audit log
with open("audit.jsonl", "w") as f:
    for event in client.replay(agent_id="audit-agent"):
        f.write(json.dumps({
            "timestamp": event.timestamp,
            "txn_id": event.txn_id,
            "operations": [
                {
                    "type": op.type.name,
                    "key": op.key,
                    "value": op.value
                }
                for op in event.operations
            ]
        }) + "\n")
```

### 3. State Reconstruction

**Problem:** Need to rebuild state from scratch.

```python
# Start with empty state
state = {}

# Replay all events
for event in client.replay(agent_id="a1"):
    for op in event.operations:
        if op.type == OperationType.WRITE:
            state[op.key] = op.value
        elif op.type == OperationType.DELETE:
            state.pop(op.key, None)

# State now matches current state
```

### 4. Testing

**Problem:** Verify agent behavior is deterministic.

```python
# Run agent
agent.run(input="test input")

# Capture replay
events_1 = list(client.replay(agent_id=agent.id))

# Reset agent, run again
agent.reset()
agent.run(input="test input")

# Replay should be identical
events_2 = list(client.replay(agent_id=agent.id))

assert events_1 == events_2  # Determinism check
```

### 5. Provenance Tracking

**Problem:** Trace final answer back to sources.

```python
# Agent stores provenance with each step
with client.begin_transaction() as tx:
    tx.write(
        agent_id="research-agent",
        key="step:1",
        value={
            "action": "search",
            "query": "statehouse architecture",
            "sources": ["doc1.pdf", "doc2.pdf"]
        }
    )
    tx.write(
        agent_id="research-agent",
        key="answer",
        value={
            "text": "Statehouse uses gRPC...",
            "based_on": ["step:1"]
        }
    )

# Later: trace answer provenance
for event in client.replay(agent_id="research-agent"):
    for op in event.operations:
        if "answer" in op.key:
            print(f"Answer: {op.value['text']}")
            print(f"Based on: {op.value['based_on']}")
        elif "step:" in op.key:
            print(f"  Step: {op.value['action']}")
            print(f"  Sources: {op.value['sources']}")
```

## Edge Cases

### Empty Replay

No events exist:
```python
events = list(client.replay(agent_id="new-agent"))
assert events == []  # Empty list, not an error
```

### Concurrent Replay

Multiple clients can replay simultaneously:
```python
# Thread 1
for event in client1.replay(agent_id="a1"):
    print(event)

# Thread 2 (same agent, same time)
for event in client2.replay(agent_id="a1"):
    print(event)

# Both see the same events in the same order
```

### Replay During Writes

Replay is consistent with committed state at replay start:

```python
# Start replay
replay_iter = client.replay(agent_id="a1")

# New write happens
with client.begin_transaction() as tx:
    tx.write(agent_id="a1", key="new", value={"x": 1})

# Replay will NOT include the new write
# (It started before the write was committed)
```

To see new events:
```python
# Start a new replay
for event in client.replay(agent_id="a1"):
    print(event)  # Includes the new write
```

### Deleted Keys

DELETE operations appear in replay:

```python
# Write then delete
with client.begin_transaction() as tx:
    tx.write(agent_id="a1", key="temp", value={"x": 1})
with client.begin_transaction() as tx:
    tx.delete(agent_id="a1", key="temp")

# Both events appear in replay
events = list(client.replay(agent_id="a1"))
assert len(events) == 2
assert events[0].operations[0].type == OperationType.WRITE
assert events[1].operations[0].type == OperationType.DELETE
```

Current state does NOT include deleted key:
```python
result = client.get_state(agent_id="a1", key="temp")
assert result is None  # Key was deleted
```

## Implementation Details

### Storage

Events are stored in an **append-only log**:

```
Event Log:
  [commit_ts=1] {txn_id, operations: [write(k1, v1)]}
  [commit_ts=2] {txn_id, operations: [write(k2, v2), delete(k3)]}
  [commit_ts=3] {txn_id, operations: [write(k1, v1_new)]}
  ...
```

State is derived:
```
State:
  k1 → v1_new (version=2, commit_ts=3)
  k2 → v2     (version=1, commit_ts=2)
  k3 → <deleted> (version=1, commit_ts=2)
```

### Snapshots

Snapshots are **optimization only**:
- State can be reconstructed from event log alone
- Snapshots speed up reads, not replay
- Replay always reads from event log

### Compaction

**Future feature:** Compact old events while preserving:
- Latest state (for reads)
- Summary events (for audit)
- Configurable retention policy

## Comparison with Other Systems

### vs. Database Changelog

| Feature | Statehouse Replay | DB Changelog (e.g., MySQL binlog) |
|---------|------------------|-----------------------------------|
| Scope | Per-agent isolation | Global (all tables) |
| Format | Application-level events | Low-level row operations |
| Filtering | By agent, namespace, time | By table, time |
| Streaming | Built-in gRPC stream | External tools (Debezium, etc.) |
| Purpose | Auditability, debugging | Replication, backup |

### vs. Event Sourcing

| Feature | Statehouse Replay | Event Sourcing (e.g., EventStore) |
|---------|------------------|-----------------------------------|
| Philosophy | State + audit log | Events are source of truth |
| Reads | State reads are fast | State derived from events |
| Schema | Versioned state records | Event schemas |
| Replay | For debugging, audit | For state reconstruction |

Statehouse is **state-first** with event log for replay.
Event sourcing is **events-first** with materialized views.

### vs. Git

| Feature | Statehouse Replay | Git Log |
|---------|------------------|---------|
| Granularity | Per-transaction | Per-commit |
| Branches | No (single timeline) | Yes |
| Merges | No | Yes |
| Purpose | Agent state audit | Source code version control |

Statehouse is **linear** - no branches or merges.

## Best Practices

### 1. Structure Keys for Replay

Use prefixes to make replay useful:

```python
# Good: time-based or sequential keys
tx.write(agent_id="a1", key="session:2026-02-07:question", value={...})
tx.write(agent_id="a1", key="session:2026-02-07:answer", value={...})

# Later: easy to filter
for event in client.replay(agent_id="a1"):
    for op in event.operations:
        if op.key.startswith("session:2026-02-07:"):
            print(op)
```

### 2. Include Metadata

Store provenance in values:

```python
tx.write(
    agent_id="a1",
    key="decision:123",
    value={
        "decision": "approve",
        "reason": "score > threshold",
        "score": 0.95,
        "threshold": 0.8,
        "timestamp": "2026-02-07T12:00:00Z",
        "model": "gpt-4"
    }
)
```

### 3. Periodic Summaries

For long-running agents, periodically write summaries:

```python
# Every 100 steps
if step % 100 == 0:
    tx.write(
        agent_id="a1",
        key=f"summary:step-{step}",
        value={
            "step": step,
            "total_decisions": count_decisions(),
            "accuracy": compute_accuracy(),
            "last_checkpoint": last_checkpoint_time
        }
    )
```

### 4. Test Replay

Include replay in your tests:

```python
def test_agent_behavior():
    agent = MyAgent()
    agent.run()
    
    # Verify replay is complete
    events = list(client.replay(agent_id=agent.id))
    assert len(events) > 0
    
    # Verify expected operations
    assert any(
        op.key == "expected_key"
        for event in events
        for op in event.operations
    )
```

## See Also

- [gRPC Architecture](grpc_architecture.md) - How replay is implemented
- [API Contract](api_contract.md) - Replay RPC definition
- [Python SDK](../python/README.md) - Client usage
- [Example Agent](../examples/agent_research/) - Agent with replay
