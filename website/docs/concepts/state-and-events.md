# State and Events

Statehouse is built on a simple but powerful model: **state** is derived from an **immutable event log**.

## State Model

State is stored as **versioned records**, identified by a tuple:

```
(namespace, agent_id, key) -> (value, version, commit_ts)
```

- **Namespace**: Logical isolation boundary (default: "default")
- **AgentId**: The agent or workflow instance
- **Key**: The state key within an agent's namespace
- **Value**: JSON-compatible structure (protobuf Struct)
- **Version**: Monotonic u64 counter, incremented on each write
- **CommitTs**: Logical timestamp when the write was committed

## Event Log

Under the hood, Statehouse is **append-only**. Every committed transaction creates an event:

```python
Event {
    txn_id: str,           # Unique transaction ID
    commit_ts: int,        # Commit timestamp (monotonic)
    operations: [          # All operations in this transaction
        {
            agent_id: str,
            key: str,
            operation: "write" | "delete",
            value: dict | None
        }
    ]
}
```

## Key Properties

### Immutability

Once written, events are never modified. This ensures:
- Complete audit trail
- Deterministic replay
- Crash recovery

### Atomicity

All operations in a transaction appear as a single event:
- Same `txn_id`
- Same `commit_ts`
- All-or-nothing semantics

### Ordering

Events are ordered by `commit_ts`, which is:
- Monotonically increasing
- Assigned at commit time
- Determines replay order

## State Derivation

Current state is derived by:
1. Starting from the latest snapshot (if available)
2. Replaying events from the snapshot forward
3. Applying each event's operations in order

This means:
- Snapshots are **derived**, not authoritative
- The event log is the **source of truth**
- State can be reconstructed at any point in time

## Example

```python
# Transaction 1: Write initial state
with client.begin_transaction() as tx:
    tx.write(agent_id="agent-1", key="counter", value={"count": 0})

# Transaction 2: Update state
with client.begin_transaction() as tx:
    tx.write(agent_id="agent-1", key="counter", value={"count": 1})

# Current state
result = client.get_state(agent_id="agent-1", key="counter")
print(result.value)  # {"count": 1}
print(result.version)  # 2

# Event log contains both transactions
for event in client.replay(agent_id="agent-1"):
    print(f"commit_ts={event.commit_ts}, value={event.operations[0].value}")
    # commit_ts=1, value={"count": 0}
    # commit_ts=2, value={"count": 1}
```

## Next Steps

- [Transactions](transactions) - Learn about transaction semantics
- [Versions](versions) - Understand versioning
- [Replay](replay) - See how replay works
