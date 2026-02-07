# Long-Running Transactions

This document describes behavior with long-running transactions and timeouts.

## Transaction Timeouts

Transactions have a server-side timeout:

```python
# Default: 30 seconds
tx = client.begin_transaction()

# Custom timeout
tx = client.begin_transaction(timeout_ms=60000)  # 60 seconds
```

## What Happens on Timeout

When a transaction exceeds its timeout:

1. Server marks transaction as expired
2. Subsequent operations (write, commit) fail
3. All staged operations discarded
4. Transaction ID invalid

```python
tx = client.begin_transaction(timeout_ms=5000)
tx.write(agent_id="a", key="k", value={"v": 1})

time.sleep(10)  # Exceeds timeout

try:
    tx.commit()  # Fails
except TransactionError as e:
    # "Transaction expired"
    pass
```

## Why Timeouts Exist

Timeouts prevent:

- Resource leaks from abandoned transactions
- Unbounded memory usage for staged operations
- Blocked resources from hung clients

## Appropriate Timeout Values

| Use Case | Recommended Timeout |
|----------|---------------------|
| Simple write | 5-10 seconds |
| Batch operations | 30-60 seconds |
| Complex workflows | 60-120 seconds |

Default (30s) is suitable for most cases.

## Avoiding Timeouts

### Keep Transactions Short

```python
# Good: Short transaction
with client.begin_transaction() as tx:
    tx.write(agent_id="a", key="k", value=data)
# Done quickly

# Bad: Long computation in transaction
with client.begin_transaction() as tx:
    result = slow_computation()  # Minutes
    tx.write(agent_id="a", key="k", value=result)  # May timeout
```

### Compute First, Then Write

```python
# Better pattern
result = slow_computation()  # Outside transaction

with client.begin_transaction() as tx:
    tx.write(agent_id="a", key="k", value=result)  # Fast
```

### Increase Timeout When Necessary

```python
# For batch operations
with client.begin_transaction(timeout_ms=120000) as tx:
    for i in range(1000):
        tx.write(agent_id="a", key=f"item:{i}", value=data[i])
```

## Detecting Timeout

Check for timeout errors:

```python
from statehouse import TransactionError

try:
    with client.begin_transaction(timeout_ms=5000) as tx:
        tx.write(...)
except TransactionError as e:
    if "expired" in str(e).lower():
        # Transaction timed out
        pass
```

## Server-Side Cleanup

The server periodically cleans expired transactions:

- Frees staged operations memory
- Logs expiry events
- No action required from clients

```
DEBUG Transaction expired: txn_id=abc123
```

## Client Reconnection

If a client reconnects after timeout:

- Old transaction ID is invalid
- Start a new transaction
- Previous operations were not committed

```python
# After reconnect
try:
    tx.commit()  # Old transaction
except TransactionError:
    # Start fresh
    with client.begin_transaction() as tx:
        tx.write(...)  # Retry operations
```

## Monitoring

Watch for timeout patterns:

- Frequent timeouts may indicate client issues
- Increase timeout or optimize client code
- Log analysis for patterns

```bash
grep "expired" /var/log/statehouse.log | wc -l
```
