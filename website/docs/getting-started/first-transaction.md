# First Transaction

Write your first state transaction with Statehouse.

## Prerequisites

- Daemon running (see [Running statehoused](running-statehoused))
- Python SDK installed (see [Installation](installation))

## Basic Transaction

```python
from statehouse import Statehouse

# Connect to daemon
client = Statehouse(url="localhost:50051")

# Begin a transaction
with client.begin_transaction() as tx:
    tx.write(
        agent_id="my-agent",
        key="greeting",
        value={"message": "Hello, Statehouse!"}
    )
# Transaction auto-commits when exiting the block
```

## Read the State

```python
# Read the state we just wrote
result = client.get_state(agent_id="my-agent", key="greeting")
print(result.value)  # {"message": "Hello, Statehouse!"}
print(result.version)  # 1
print(result.exists)  # True
```

## Multiple Operations

A transaction can contain multiple operations:

```python
with client.begin_transaction() as tx:
    # Write multiple keys
    tx.write(agent_id="my-agent", key="step1", value={"status": "started"})
    tx.write(agent_id="my-agent", key="step2", value={"status": "pending"})
    tx.write(agent_id="my-agent", key="config", value={"mode": "production"})
    
    # Delete a key
    tx.delete(agent_id="my-agent", key="temp-data")

# All operations commit atomically
```

## Error Handling

```python
from statehouse import Statehouse, TransactionError

try:
    with client.begin_transaction() as tx:
        tx.write(agent_id="my-agent", key="data", value={"x": 1})
        # If commit fails, TransactionError is raised
except TransactionError as e:
    print(f"Transaction failed: {e}")
```

## Manual Commit

You can also commit manually:

```python
tx = client.begin_transaction()
tx.write(agent_id="my-agent", key="data", value={"x": 1})
tx.commit()  # Explicit commit

# Or abort
tx = client.begin_transaction()
tx.write(agent_id="my-agent", key="data", value={"x": 1})
tx.abort()  # Discard the transaction
```

## Next Steps

- [First Replay](first-replay) - Replay your transaction history
- [Python SDK: Transactions](../python-sdk/transactions) - Learn more about transactions
