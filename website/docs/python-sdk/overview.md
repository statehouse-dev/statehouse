# Python SDK Overview

The Statehouse Python SDK provides a clean, Pythonic interface for interacting with the Statehouse daemon. All gRPC and protobuf details are hidden from users.

## Installation

```bash
pip install statehouse
```

Or install from source:

```bash
cd python
pip install -e .
```

## Quick Start

```python
from statehouse import Statehouse

# Connect to the daemon
client = Statehouse(url="localhost:50051")

# Write state in a transaction
with client.begin_transaction() as tx:
    tx.write(
        agent_id="my-agent",
        key="memory",
        value={"fact": "Paris is the capital of France"},
    )

# Read state
result = client.get_state(agent_id="my-agent", key="memory")
print(result.value)  # {"fact": "Paris is the capital of France"}
```

## Design Principles

The SDK follows these principles:

1. **No gRPC exposure**: Users never see protobufs, stubs, or gRPC types
2. **Pythonic API**: Uses dataclasses, context managers, and iterators
3. **Type safety**: Full type hints for IDE support and static analysis
4. **Minimal dependencies**: Only requires `grpcio` and `protobuf`

## Core Classes

| Class | Purpose |
|-------|---------|
| `Statehouse` | Main client for connecting to the daemon |
| `Transaction` | Context for staging writes and deletes |
| `StateResult` | Result of read operations |
| `ReplayEvent` | Event from the replay stream |

## Exceptions

All SDK exceptions inherit from `StatehouseError`:

| Exception | When raised |
|-----------|-------------|
| `StatehouseError` | Base exception for all SDK errors |
| `TransactionError` | Transaction lifecycle errors |
| `NotFoundError` | Requested resource not found |
| `ConnectionError` | Cannot connect to daemon |

## Next Steps

- [Client reference](./client.md): Detailed client API
- [Transactions](./transactions.md): Writing and deleting state
- [Reads](./reads.md): Reading state
- [Replay](./replay.md): Replaying events
- [Errors](./errors.md): Error handling
