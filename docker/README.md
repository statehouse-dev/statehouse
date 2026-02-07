# Statehouse Daemon

Docker image for the **Statehouse daemon** (`statehoused`): a strongly consistent state and memory engine for AI agents and workflows.

- **Docs:** [statehouse.dev](https://statehouse.dev)
- **Source:** [github.com/statehouse-dev/statehouse](https://github.com/statehouse-dev/statehouse)

## Quick start

```bash
# Run with in-memory storage (default; good for try-it and CI)
docker run -d -p 50051:50051 --name statehouse rtacconi/statehouse:latest
```

Connect your client to `localhost:50051` (gRPC). For example with the Python SDK:

```python
from statehouse import Statehouse
client = Statehouse(url="localhost:50051")
```

## Options

| Variable | Default | Description |
|----------|---------|-------------|
| `STATEHOUSE_ADDR` | `0.0.0.0:50051` | Listen address |
| `STATEHOUSE_USE_MEMORY` | `1` | In-memory storage (set to empty for persistent storage) |
| `RUST_LOG` | `info` | Log level (`debug`, `info`, `warn`, `error`) |

**Persistent storage:** use a volume and disable in-memory mode:

```bash
docker run -d -p 50051:50051 -v statehouse-data:/data -e STATEHOUSE_USE_MEMORY= --name statehouse rtacconi/statehouse:latest
```

Data is stored in `/data` inside the container.

## Tags

- `latest` – current release
- `sha-<commit>` – build from a specific Git commit (CI)
- `<version>` – e.g. `v0.1.0` (on releases)

## License

Same as the [Statehouse project](https://github.com/statehouse-dev/statehouse) (see repository LICENSE).
