# Transactions

All writes in Statehouse are **transactional**. Either a state transition happened, or it did not.

## Transaction Lifecycle

### 1. Begin Transaction

```python
tx = client.begin_transaction()
# Returns a Transaction object with a unique txn_id
```

The server assigns a unique `txn_id` and starts tracking the transaction.

### 2. Stage Operations

```python
tx.write(agent_id="agent-1", key="key1", value={"x": 1})
tx.write(agent_id="agent-1", key="key2", value={"y": 2})
tx.delete(agent_id="agent-1", key="key3")
```

Operations are staged in memory. They are **not visible** to other transactions until commit.

### 3. Commit or Abort

```python
# Commit: make all operations visible atomically
tx.commit()

# Abort: discard all operations
tx.abort()
```

## Atomicity Guarantee

**All operations in a transaction succeed or fail together.**

```python
with client.begin_transaction() as tx:
    tx.write(agent_id="agent-1", key="a", value={"x": 1})
    tx.write(agent_id="agent-1", key="b", value={"y": 2})
    # Both writes commit atomically, or neither does
```

If commit fails, **no operations** are applied.

## Isolation

Transactions are isolated:
- Staged operations are not visible to other transactions
- Reads see committed state only
- No dirty reads, no phantom reads

## Context Manager Support

Use Python's `with` statement for automatic commit:

```python
# Auto-commits on success, auto-aborts on exception
with client.begin_transaction() as tx:
    tx.write(agent_id="agent-1", key="data", value={"x": 1})
    # Transaction commits automatically when exiting the block
```

## Transaction Timeouts

Transactions have a configurable timeout (default: 30 seconds). If a transaction is not committed or aborted within the timeout, it is automatically aborted.

## Error Handling

```python
try:
    with client.begin_transaction() as tx:
        tx.write(agent_id="agent-1", key="data", value={"x": 1})
        # If commit fails, TransactionError is raised
except TransactionError as e:
    print(f"Transaction failed: {e}")
```

## Aborted Transactions

Aborted transactions:
- Do not appear in replay
- Do not affect state
- Are completely discarded

```python
tx = client.begin_transaction()
tx.write(agent_id="agent-1", key="temp", value={"x": 1})
tx.abort()  # This write never happened

# Replay will not include this transaction
events = list(client.replay(agent_id="agent-1"))
# No events from the aborted transaction
```

## Next Steps

- [Versions](versions) - Learn how versions work with transactions
- [Replay](replay) - See how transactions appear in replay
