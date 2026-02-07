# Replay

Replay streams the event log for an agent, allowing you to reconstruct state history or audit operations.

## Basic Replay

```python
for event in client.replay(agent_id="my-agent"):
    print(f"Transaction: {event.txn_id}")
    print(f"Timestamp: {event.commit_ts}")
    for op in event.operations:
        print(f"  {op.key} v{op.version}: {op.value}")
```

## ReplayEvent Structure

| Field | Type | Description |
|-------|------|-------------|
| `txn_id` | `str` | Transaction identifier |
| `commit_ts` | `int` | Commit timestamp |
| `operations` | `list[Operation]` | List of operations in this transaction |

## Operation Structure

| Field | Type | Description |
|-------|------|-------------|
| `key` | `str` | Affected key |
| `value` | `Dict[str, Any] \| None` | New value (None for deletes) |
| `version` | `int` | Version after this operation |

## Time Range Filtering

Filter events by timestamp:

```python
# Events after timestamp 1000
for event in client.replay(agent_id="agent", start_ts=1000):
    print(event)

# Events before timestamp 2000
for event in client.replay(agent_id="agent", end_ts=2000):
    print(event)

# Events in range [1000, 2000]
for event in client.replay(agent_id="agent", start_ts=1000, end_ts=2000):
    print(event)
```

## Streaming Behavior

Replay uses gRPC streaming internally. Events are delivered as they become available, with proper backpressure handling.

```python
# Large replays are streamed efficiently
count = 0
for event in client.replay(agent_id="agent"):
    count += len(event.operations)
    if count > 10000:
        break  # Early termination is supported
```

## Use Cases

### Audit Trail

```python
def audit_agent(client, agent_id):
    """Print complete audit trail for an agent."""
    for event in client.replay(agent_id=agent_id):
        print(f"[{event.commit_ts}] Transaction {event.txn_id}")
        for op in event.operations:
            if op.value is None:
                print(f"  DELETE {op.key}")
            else:
                print(f"  WRITE {op.key} = {op.value}")
```

### State Reconstruction

```python
def reconstruct_state(client, agent_id, at_ts):
    """Reconstruct state as of a specific timestamp."""
    state = {}
    for event in client.replay(agent_id=agent_id, end_ts=at_ts):
        for op in event.operations:
            if op.value is None:
                state.pop(op.key, None)
            else:
                state[op.key] = op.value
    return state
```

### Resume After Crash

```python
def find_last_step(client, agent_id):
    """Find the last completed step for resumption."""
    last_step = 0
    for event in client.replay(agent_id=agent_id):
        for op in event.operations:
            if op.key.startswith("step:"):
                step_num = int(op.key.split(":")[1])
                last_step = max(last_step, step_num)
    return last_step
```

## Namespace Override

```python
for event in client.replay(agent_id="agent", namespace="production"):
    print(event)
```

## Determinism Guarantee

Replay is deterministic: given the same agent_id and time range, you will always receive the same events in the same order. This is fundamental to Statehouse's design.
