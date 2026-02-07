# Versions

Every write to a key creates a new **version**. Versions are monotonic counters that enable time-travel queries and versioned reads.

## Version Semantics

### Per-Key Versioning

Each `(namespace, agent_id, key)` tuple has its own version counter:

```python
# First write to key "counter"
with client.begin_transaction() as tx:
    tx.write(agent_id="agent-1", key="counter", value={"count": 0})
# Version = 1

# Second write to same key
with client.begin_transaction() as tx:
    tx.write(agent_id="agent-1", key="counter", value={"count": 1})
# Version = 2

# Write to different key
with client.begin_transaction() as tx:
    tx.write(agent_id="agent-1", key="other", value={"x": 42})
# Version = 1 (independent counter)
```

### Monotonic Increment

Versions always increase:
- Never decrease
- Never skip values
- Increment exactly once per write

### Version Assignment

Versions are assigned:
- At commit time
- Atomically with the transaction
- In commit timestamp order

## Reading at Specific Versions

You can read state at a specific version:

```python
# Get latest version
result = client.get_state(agent_id="agent-1", key="counter")
print(result.version)  # e.g., 5

# Read at specific version
result_v3 = client.get_state_at_version(
    agent_id="agent-1",
    key="counter",
    version=3
)
# Returns state as it was at version 3
```

## Version and Commit Timestamp

Each version has an associated `commit_ts`:

```python
result = client.get_state(agent_id="agent-1", key="counter")
print(result.version)      # 5
print(result.commit_ts)    # 42 (logical timestamp)
```

Versions and commit timestamps are related but distinct:
- **Version**: Per-key counter
- **CommitTs**: Global ordering timestamp

## Use Cases

### Time-Travel Queries

```python
# What was the state at version 3?
state_v3 = client.get_state_at_version(
    agent_id="agent-1",
    key="counter",
    version=3
)
```

### Change Detection

```python
current = client.get_state(agent_id="agent-1", key="config")
if current.version > last_seen_version:
    # State has changed
    process_update(current.value)
```

### Audit Trails

Versions enable complete audit trails:
- Every change is versioned
- Can reconstruct state at any version
- Can see version history via replay

## Deletes and Versions

Deletes also create versions:

```python
# Write version 1
with client.begin_transaction() as tx:
    tx.write(agent_id="agent-1", key="temp", value={"x": 1})

# Delete creates version 2
with client.begin_transaction() as tx:
    tx.delete(agent_id="agent-1", key="temp")

# Reading returns exists=False, but version=2
result = client.get_state(agent_id="agent-1", key="temp")
print(result.exists)   # False
print(result.version)  # 2
```

## Next Steps

- [State and Events](state-and-events) - Understand the state model
- [Replay](replay) - See how versions appear in replay
