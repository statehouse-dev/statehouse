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

```dockerfile
FROM rust:1.75 as builder
WORKDIR /app
COPY . .
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/target/release/statehoused /usr/local/bin/
EXPOSE 50051
CMD ["statehoused"]
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
- [Configuration](operations/configuration) - Complete configuration reference
