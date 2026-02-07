# Partial Writes

This document explains how Statehouse prevents partial writes from being visible.

## The Problem

Partial writes occur when:
- Transaction has multiple operations
- Some operations succeed, others fail
- System would be in inconsistent state

Example: transferring money between accounts:

```python
with client.begin_transaction() as tx:
    tx.write(agent_id="bank", key="account:A", value={"balance": 50})
    # Crash here would leave account B unchanged
    tx.write(agent_id="bank", key="account:B", value={"balance": 150})
```

## The Guarantee

Statehouse guarantees **atomic transactions**:

- All operations succeed together
- Or none of them take effect

This is the "no partial transactions visible" invariant.

## How It Works

1. **Staging**: Operations are staged in memory
2. **Commit**: All operations written atomically
3. **Acknowledgment**: Only after all durable

```
Begin → Write A → Write B → Write C → Commit
                    ↓
            [All staged in memory]
                    ↓
            [Atomic commit to storage]
                    ↓
            [All visible simultaneously]
```

## Failure Scenarios

### Crash Before Commit

```python
with client.begin_transaction() as tx:
    tx.write(agent_id="a", key="x", value={"v": 1})
    tx.write(agent_id="a", key="y", value={"v": 2})
    # CRASH - transaction lost
```

Result: Neither write visible. Correct behavior.

### Crash During Commit

```python
with client.begin_transaction() as tx:
    tx.write(agent_id="a", key="x", value={"v": 1})
    tx.write(agent_id="a", key="y", value={"v": 2})
tx.commit()  # CRASH during this
```

Result: Either both visible or neither. Never partial.

### Crash After Commit

```python
with client.begin_transaction() as tx:
    tx.write(agent_id="a", key="x", value={"v": 1})
    tx.write(agent_id="a", key="y", value={"v": 2})
commit_ts = tx.commit()  # Returns successfully
# CRASH here
```

Result: Both writes durable and visible after recovery.

## Implementation

Atomicity is achieved through:

1. **RocksDB WriteBatch**: Groups operations
2. **Single writer**: No concurrent commits
3. **Fsync**: Ensures durability

```rust
// Simplified internal logic
let batch = WriteBatch::new();
for op in transaction.operations {
    batch.put(op.key, op.value);
}
db.write(batch)?;  // Atomic
```

## Verification

Verify atomicity in tests:

```python
# Write multiple keys
with client.begin_transaction() as tx:
    tx.write(agent_id="test", key="a", value={"v": 1})
    tx.write(agent_id="test", key="b", value={"v": 2})
    tx.write(agent_id="test", key="c", value={"v": 3})

# Read all or none
a = client.get_state(agent_id="test", key="a")
b = client.get_state(agent_id="test", key="b")
c = client.get_state(agent_id="test", key="c")

# All exist, or none exist
assert a.exists == b.exists == c.exists
```

## Implications

Because of atomic transactions:

- Safe to update related keys together
- No need for application-level locking
- Simpler error handling
- Reliable state for agents
