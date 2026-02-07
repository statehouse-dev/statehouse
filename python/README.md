# Statehouse Python SDK

Python client library for Statehouse - a strongly consistent state and memory engine for AI agents.

## Installation

```bash
pip install statehouse
```

## Quick Start

```python
from statehouse import Statehouse

# Connect to daemon
client = Statehouse(url="localhost:50051")

# Write state
tx = client.begin_transaction()
tx.write(agent_id="agent-1", key="memory", value={"fact": "sky is blue"})
tx.commit()

# Read state
state = client.get_state(agent_id="agent-1", key="memory")
print(state.value)  # {"fact": "sky is blue"}

# Replay events
for event in client.replay(agent_id="agent-1"):
    print(f"[{event.commit_ts}] {len(event.operations)} operations")
```

## Features

- **Clean API**: No gRPC or protobuf visible to users
- **Type-safe**: Full type hints
- **Async & Sync**: Both interfaces supported
- **Pythonic**: Context managers, exceptions, iterators

## Documentation

See [../docs/](../docs/) for project documentation (architecture, API contract, troubleshooting). For the CLI: [docs/CLI.md](docs/CLI.md).
