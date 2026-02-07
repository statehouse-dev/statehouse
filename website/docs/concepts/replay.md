# Replay

Replay is the ability to retrieve the complete history of state changes for an agent in chronological order.

## Overview

```python
for event in client.replay(agent_id="agent-1"):
    print(f"[{event.commit_ts}] Transaction {event.txn_id}")
    for op in event.operations:
        print(f"  {op.key}: {op.value}")
```

Replay is essential for:
- **Debugging** - understand what an agent did
- **Auditing** - compliance and accountability
- **Provenance** - trace decisions back to their inputs
- **Recovery** - rebuild state from scratch
- **Testing** - verify agent behavior deterministically

## Core Guarantees

### Completeness

Replay returns **all** committed operations for the specified agent:
- Every successful `commit()` is recorded
- No operations are lost (subject to storage durability)
- Aborted transactions are **not** included

### Ordering

Events are returned in **commit timestamp order**:
- Determined by when the transaction was committed
- Not by when operations were staged
- Not by wall-clock time

### Atomicity

Multi-operation transactions appear as a single event:
- All operations share the same `txn_id` and `commit_ts`
- Appear together in replay

### Isolation

Replay for one agent does not include other agents' events:
- Scoped to `(namespace, agent_id)`
- Namespace isolation works the same way

### Consistency

Replay reflects **committed** state exactly:
- If you replay all events and apply them in order
- You will reconstruct current state precisely

## Event Structure

Each event contains:

```python
@dataclass
class ReplayEvent:
    txn_id: str          # Transaction ID
    commit_ts: int       # Commit timestamp (monotonic)
    operations: [        # All operations in this transaction
        {
            agent_id: str,
            key: str,
            operation: "write" | "delete",
            value: dict | None
        }
    ]
```

## Example

```python
# Write some state
with client.begin_transaction() as tx:
    tx.write(agent_id="agent-1", key="step1", value={"status": "started"})
    tx.write(agent_id="agent-1", key="step2", value={"status": "pending"})

with client.begin_transaction() as tx:
    tx.write(agent_id="agent-1", key="step1", value={"status": "completed"})
    tx.write(agent_id="agent-1", key="step2", value={"status": "started"})

# Replay shows both transactions
for event in client.replay(agent_id="agent-1"):
    print(f"Transaction {event.txn_id} at commit_ts={event.commit_ts}")
    for op in event.operations:
        print(f"  {op.key}: {op.value}")
```

## Time Range Filtering

You can filter replay by time range:

```python
# Replay events in a time range
for event in client.replay(
    agent_id="agent-1",
    start_ts=10,
    end_ts=20
):
    # Only events with commit_ts between 10 and 20
    print(event)
```

## Streaming

Replay is implemented as a **server-streaming** RPC:
- Events are streamed as they are read
- Memory-efficient for large histories
- Can be interrupted without losing progress

## Determinism

Replay is **deterministic**:
- Same events, same order, every time
- Enables reproducible debugging
- Enables deterministic testing

## Next Steps

- [Determinism](determinism) - Learn about deterministic guarantees
- [Examples](../examples/reference-agent) - See replay in action
