# Statehouse Client

The `Statehouse` class is the main entry point for interacting with the daemon.

## Constructor

```python
from statehouse import Statehouse

client = Statehouse(
    url="localhost:50051",  # Daemon address
    namespace="default",     # Default namespace
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | `"localhost:50051"` | Daemon address (host:port) |
| `namespace` | `str` | `"default"` | Default namespace for operations |

## Connection Management

### Context Manager

The client supports context manager protocol for automatic cleanup:

```python
with Statehouse(url="localhost:50051") as client:
    # Use client
    result = client.get_state(agent_id="agent", key="state")
# Connection automatically closed
```

### Manual Close

```python
client = Statehouse()
try:
    # Use client
    pass
finally:
    client.close()
```

## Health Check

```python
status = client.health()
print(status)  # "ok"
```

Returns `"ok"` if the daemon is healthy.

## Version

```python
version, git_sha = client.version()
print(f"Version: {version}, SHA: {git_sha}")
```

Returns a tuple of (version string, git SHA).

## Namespaces

Namespaces partition state. The default namespace is `"default"`.

```python
# Use default namespace
client = Statehouse(namespace="default")

# Override namespace per-operation
result = client.get_state(
    agent_id="agent",
    key="state",
    namespace="production",
)
```

## Thread Safety

The client is **not** thread-safe. Create one client per thread, or use external synchronization.

For async workloads, the SDK provides an async client (see [async usage](#async-usage)).

## Async Usage

For async/await support:

```python
import asyncio
from statehouse import AsyncStatehouse

async def main():
    async with AsyncStatehouse(url="localhost:50051") as client:
        async with client.begin_transaction() as tx:
            await tx.write(agent_id="agent", key="state", value={"key": "value"})

asyncio.run(main())
```

Note: The async client uses `grpc.aio` internally.
