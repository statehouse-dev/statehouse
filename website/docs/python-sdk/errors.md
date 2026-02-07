# Error Handling

The SDK defines a hierarchy of exceptions for different error conditions.

## Exception Hierarchy

```
StatehouseError
├── TransactionError
├── NotFoundError
└── ConnectionError
```

## StatehouseError

Base exception for all SDK errors.

```python
from statehouse import StatehouseError

try:
    result = client.get_state(agent_id="agent", key="key")
except StatehouseError as e:
    print(f"Statehouse error: {e}")
```

## TransactionError

Raised for transaction lifecycle errors.

```python
from statehouse import TransactionError

try:
    with client.begin_transaction() as tx:
        tx.write(agent_id="agent", key="key", value={"x": 1})
        tx.commit()
        tx.commit()  # Raises TransactionError
except TransactionError as e:
    print(f"Transaction error: {e}")
```

Common causes:

- Attempting to write after commit
- Attempting to commit after abort
- Transaction timeout
- Server rejected the transaction

## NotFoundError

Raised when a requested resource doesn't exist.

```python
from statehouse import NotFoundError

try:
    result = client.get_state_at_version(
        agent_id="agent",
        key="key",
        version=999,
    )
except NotFoundError:
    print("Version not found")
```

## ConnectionError

Raised when the client cannot connect to the daemon.

```python
from statehouse import ConnectionError

try:
    client = Statehouse(url="localhost:99999")
    client.health()
except ConnectionError as e:
    print(f"Cannot connect: {e}")
```

Note: This is `statehouse.ConnectionError`, not the built-in `ConnectionError`.

## Best Practices

### Catch Specific Exceptions

```python
from statehouse import (
    StatehouseError,
    TransactionError,
    NotFoundError,
    ConnectionError,
)

try:
    with client.begin_transaction() as tx:
        tx.write(agent_id="agent", key="key", value={"x": 1})
except ConnectionError:
    # Handle connection issues (retry, failover)
    pass
except TransactionError:
    # Handle transaction failures (retry, log)
    pass
except StatehouseError:
    # Handle other errors
    pass
```

### Retry Logic

```python
import time
from statehouse import ConnectionError, TransactionError

def write_with_retry(client, agent_id, key, value, max_retries=3):
    for attempt in range(max_retries):
        try:
            with client.begin_transaction() as tx:
                tx.write(agent_id=agent_id, key=key, value=value)
            return
        except (ConnectionError, TransactionError) as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

### Logging Errors

```python
import logging
from statehouse import StatehouseError

logger = logging.getLogger(__name__)

try:
    result = client.get_state(agent_id="agent", key="key")
except StatehouseError as e:
    logger.error(f"Statehouse operation failed: {e}", exc_info=True)
    raise
```

## gRPC Error Mapping

The SDK maps gRPC status codes to Python exceptions:

| gRPC Status | Python Exception |
|-------------|------------------|
| `UNAVAILABLE` | `ConnectionError` |
| `NOT_FOUND` | `NotFoundError` |
| `ABORTED` | `TransactionError` |
| `DEADLINE_EXCEEDED` | `TransactionError` |
| Other | `StatehouseError` |
