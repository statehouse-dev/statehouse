# Transactions

Transactions group multiple writes and deletes into an atomic unit. Either all operations succeed, or none do.

## Beginning a Transaction

```python
tx = client.begin_transaction()
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeout_ms` | `int \| None` | `30000` | Transaction timeout in milliseconds |
| `namespace` | `str \| None` | Client default | Namespace for this transaction |

## Writing State

```python
tx.write(
    agent_id="my-agent",
    key="memory",
    value={"fact": "Some information"},
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | `str` | Agent identifier |
| `key` | `str` | State key |
| `value` | `Dict[str, Any]` | JSON-compatible dictionary |

The value must be a dictionary. Nested structures, lists, and primitive types are supported.

## Deleting State

```python
tx.delete(agent_id="my-agent", key="memory")
```

Deletes create a tombstone record. The key will no longer exist, but the delete event is recorded in the log.

## Committing

```python
commit_ts = tx.commit()
print(f"Committed at timestamp {commit_ts}")
```

Returns the commit timestamp (monotonic integer).

## Aborting

```python
tx.abort()
```

Aborts discard all staged operations. No state changes occur.

## Context Manager (Recommended)

The recommended pattern uses a context manager:

```python
with client.begin_transaction() as tx:
    tx.write(agent_id="agent", key="key1", value={"a": 1})
    tx.write(agent_id="agent", key="key2", value={"b": 2})
    # Commits automatically on exit
```

If an exception occurs, the transaction is automatically aborted:

```python
with client.begin_transaction() as tx:
    tx.write(agent_id="agent", key="key", value={"x": 1})
    raise ValueError("Something went wrong")
    # Transaction is aborted, state unchanged
```

## Multiple Operations

A single transaction can contain multiple writes and deletes:

```python
with client.begin_transaction() as tx:
    tx.write(agent_id="agent", key="step:1", value={"action": "start"})
    tx.write(agent_id="agent", key="step:2", value={"action": "process"})
    tx.delete(agent_id="agent", key="temp:scratch")
    tx.write(agent_id="agent", key="step:3", value={"action": "finish"})
```

All operations are applied atomically at commit.

## Transaction Timeouts

Transactions have a server-side timeout. If not committed within the timeout, the transaction is automatically aborted.

```python
# 5 second timeout
tx = client.begin_transaction(timeout_ms=5000)
```

## Error Handling

```python
from statehouse import TransactionError

try:
    with client.begin_transaction() as tx:
        tx.write(agent_id="agent", key="key", value={"x": 1})
except TransactionError as e:
    print(f"Transaction failed: {e}")
```

Common errors:

- **Transaction already committed**: Cannot modify after commit
- **Transaction already aborted**: Cannot modify after abort
- **Transaction timeout**: Server aborted due to timeout
