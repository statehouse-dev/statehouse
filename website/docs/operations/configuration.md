# Configuration

Statehouse daemon is configured through environment variables and configuration files.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STATEHOUSE_LISTEN_ADDR` | `0.0.0.0:50051` | gRPC listen address |
| `STATEHOUSE_DATA_DIR` | `./statehouse-data` | Data directory path |
| `STATEHOUSE_USE_MEMORY` | `0` | Use in-memory storage (testing only) |
| `STATEHOUSE_FSYNC_ON_COMMIT` | `1` | Fsync after each commit |
| `STATEHOUSE_SNAPSHOT_INTERVAL` | `1000` | Commits between snapshots |
| `STATEHOUSE_MAX_LOG_SIZE` | `104857600` | Max log size in bytes (100MB) |
| `STATEHOUSE_TX_TIMEOUT_MS` | `30000` | Default transaction timeout |
| `RUST_LOG` | `info` | Log level |

## Configuration File

Create `statehouse.conf` or use the example:

```bash
cp statehouse.conf.example statehouse.conf
```

Example configuration:

```ini
# Network
STATEHOUSE_LISTEN_ADDR=0.0.0.0:50051

# Storage
STATEHOUSE_DATA_DIR=/var/lib/statehouse
STATEHOUSE_FSYNC_ON_COMMIT=1

# Snapshots
STATEHOUSE_SNAPSHOT_INTERVAL=1000

# Logging
RUST_LOG=info
```

## Loading Configuration

```bash
# From environment
export STATEHOUSE_LISTEN_ADDR=0.0.0.0:50051
./statehoused

# From file
source statehouse.conf && ./statehoused

# With systemd
# EnvironmentFile=/etc/statehouse/statehouse.conf
```

## Production Settings

Recommended production configuration:

```ini
# Persistent storage with fsync
STATEHOUSE_DATA_DIR=/var/lib/statehouse
STATEHOUSE_FSYNC_ON_COMMIT=1

# Regular snapshots for faster recovery
STATEHOUSE_SNAPSHOT_INTERVAL=500

# Appropriate log level
RUST_LOG=info

# Listen on all interfaces
STATEHOUSE_LISTEN_ADDR=0.0.0.0:50051
```

## Development Settings

For local development:

```ini
# Local data directory
STATEHOUSE_DATA_DIR=./data

# Fast commits (no fsync)
STATEHOUSE_FSYNC_ON_COMMIT=0

# Debug logging
RUST_LOG=debug

# Localhost only
STATEHOUSE_LISTEN_ADDR=127.0.0.1:50051
```

## In-Memory Mode

For testing only:

```bash
STATEHOUSE_USE_MEMORY=1 ./statehoused
```

Data is lost on restart. Do not use in production.

## Log Levels

Control verbosity with `RUST_LOG`:

| Level | Description |
|-------|-------------|
| `error` | Only errors |
| `warn` | Warnings and errors |
| `info` | Normal operation (recommended) |
| `debug` | Detailed operation logs |
| `trace` | Very verbose (development only) |

Targeted logging:

```bash
# Debug only for state machine
RUST_LOG=statehouse_core::state_machine=debug,info

# Trace gRPC calls
RUST_LOG=tonic=trace,info
```

## Security Considerations

In production:

- Run as non-root user
- Protect data directory permissions
- Use firewall to restrict access to gRPC port
- Consider TLS termination via reverse proxy

Note: Statehouse MVP does not include authentication or encryption at rest. See [non-goals](../introduction/when-not-to-use) for details.
