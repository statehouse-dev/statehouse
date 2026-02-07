# Running statehoused

The Statehouse daemon (`statehoused`) is the core state engine. Here's how to run it.

## Basic Usage

### In-Memory Storage (Testing)

```bash
STATEHOUSE_USE_MEMORY=1 ./target/release/statehoused
```

Useful for:
- Testing and development
- Quick experiments
- CI/CD pipelines

**Note**: Data is lost when the daemon stops.

### Persistent Storage (Production)

```bash
./target/release/statehoused
```

The daemon will:
- Create a data directory (default: `./statehouse-data`)
- Use RocksDB for persistence
- Create snapshots automatically
- Recover from crashes

## Configuration

### Environment Variables

```bash
# Listen address (default: 0.0.0.0:50051)
export STATEHOUSE_LISTEN_ADDR=0.0.0.0:50051

# Data directory (default: ./statehouse-data)
export STATEHOUSE_DATA_DIR=/var/lib/statehouse

# Use in-memory storage (default: false)
export STATEHOUSE_USE_MEMORY=0

# Log level (default: info)
export RUST_LOG=debug
```

### Configuration File

Create `statehouse.conf`:

```toml
[server]
listen_addr = "0.0.0.0:50051"

[storage]
data_dir = "/var/lib/statehouse"
use_memory = false
snapshot_interval = 1000

[storage.rocksdb]
fsync_on_commit = true
```

Then run:

```bash
./target/release/statehoused --config statehouse.conf
```

## Production Deployment

### systemd Service

See `packaging/statehoused.service` for a systemd unit file example.

### Docker

Use the image from [Docker Hub](https://hub.docker.com/r/rtacconi/statehouse):

```bash
# In-memory storage (default; good for try-it and CI)
docker run -d -p 50051:50051 --name statehouse rtacconi/statehouse:latest

# Persistent storage: mount a volume and disable in-memory
docker run -d -p 50051:50051 -v statehouse-data:/data -e STATEHOUSE_USE_MEMORY= --name statehouse rtacconi/statehouse:latest
```

Environment variables:

- `STATEHOUSE_ADDR` – Listen address (default: `0.0.0.0:50051`)
- `STATEHOUSE_USE_MEMORY` – Set to any value for in-memory storage; leave unset for RocksDB in `/data`
- `RUST_LOG` – Log level (e.g. `debug`)

To build the image locally instead of pulling:

```bash
docker build -t rtacconi/statehouse:latest .
docker run -d -p 50051:50051 rtacconi/statehouse:latest
```

### Health Check

The daemon exposes a health check endpoint:

```bash
# Using curl
curl http://localhost:50051/health

# Using statehousectl
statehousectl health
```

## Logging

The daemon uses structured logging:

```bash
# Set log level
export RUST_LOG=debug

# Run daemon
./target/release/statehoused
```

Logs include:
- Transaction lifecycle events
- Commit operations
- Replay start/end
- Errors and warnings

## Next Steps

- [First Transaction](first-transaction) - Write your first state
- [Configuration](../operations/configuration) - Complete configuration reference
