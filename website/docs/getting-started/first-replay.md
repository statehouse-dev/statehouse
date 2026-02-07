# First Replay

Replay your agent's transaction history to see what happened.

## Prerequisites

- Daemon running
- Some transactions written (see [First Transaction](first-transaction))

## Basic Replay

```python
from statehouse import Statehouse

client = Statehouse(url="localhost:50051")

# Replay all events for an agent
for event in client.replay(agent_id="my-agent"):
    print(f"Transaction {event.txn_id} at commit_ts={event.commit_ts}")
    for op in event.operations:
        print(f"  {op.key}: {op.value}")
```

## Example Workflow

```python
# Write some state
with client.begin_transaction() as tx:
    tx.write(agent_id="my-agent", key="step1", value={"status": "started"})

with client.begin_transaction() as tx:
    tx.write(agent_id="my-agent", key="step1", value={"status": "completed"})
    tx.write(agent_id="my-agent", key="step2", value={"status": "started"})

# Replay to see the history
print("Replay history:")
for event in client.replay(agent_id="my-agent"):
    print(f"\nTransaction {event.txn_id} (commit_ts={event.commit_ts})")
    for op in event.operations:
        if op.operation == "write":
            print(f"  WRITE {op.key}: {op.value}")
        elif op.operation == "delete":
            print(f"  DELETE {op.key}")
```

Output:

```
Replay history:

Transaction abc-123 (commit_ts=1)
  WRITE step1: {'status': 'started'}

Transaction def-456 (commit_ts=2)
  WRITE step1: {'status': 'completed'}
  WRITE step2: {'status': 'started'}
```

## Time Range Filtering

Filter replay by commit timestamp range:

```python
# Replay events in a time range
for event in client.replay(
    agent_id="my-agent",
    start_ts=10,
    end_ts=20
):
    # Only events with commit_ts between 10 and 20
    print(event)
```

## Collecting Events

You can collect all events into a list:

```python
events = list(client.replay(agent_id="my-agent"))
print(f"Total events: {len(events)}")

# Access specific events
first_event = events[0]
last_event = events[-1]
```

## Use Cases

### Debugging

```python
# What did the agent do?
for event in client.replay(agent_id="agent-1"):
    print(f"At {event.commit_ts}:")
    for op in event.operations:
        print(f"  {op.operation} {op.key}")
```

### Audit Trail

```python
# Generate audit log
with open("audit.log", "w") as f:
    for event in client.replay(agent_id="agent-1"):
        f.write(f"{event.commit_ts},{event.txn_id}\n")
        for op in event.operations:
            f.write(f"  {op.operation},{op.key}\n")
```

### State Reconstruction

```python
# Reconstruct state by replaying events
state = {}
for event in client.replay(agent_id="agent-1"):
    for op in event.operations:
        if op.operation == "write":
            state[op.key] = op.value
        elif op.operation == "delete":
            state.pop(op.key, None)

print("Reconstructed state:", state)
```

## Next Steps

- [Concepts: Replay](concepts/replay) - Learn about replay guarantees
- [Python SDK: Replay](python-sdk/replay) - Complete replay API reference
- [Examples](examples/reference-agent) - See replay in a real agent
