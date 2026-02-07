# Installation

Install Statehouse daemon and Python SDK.

## Prerequisites

- **Daemon**: Run via [Docker](https://hub.docker.com/r/rtacconi/statehouse) (no Rust) or build from source (Rust 1.70+, `cargo`)
- **Python** (for SDK): Python 3.9+
- **Storage**: Only if not using Docker in-memory mode; otherwise disk for RocksDB data directory

## Install the Daemon

### Option 1: Docker (no Rust required)

Run the daemon in a container:

```bash
docker run -d -p 50051:50051 --name statehouse rtacconi/statehouse:latest
```

See [Running the Daemon](./running-statehoused#docker) for in-memory vs persistent storage.

### Option 2: Build from Source

```bash
git clone https://github.com/statehouse-dev/statehouse.git
cd statehouse
cargo build --release
```

The daemon binary will be at `target/release/statehoused`.

### Option 3: Use Pre-built Binary

Download a release tarball from GitHub releases and extract:

```bash
tar -xzf statehouse-*.tar.gz
cd statehouse-*/
./install.sh  # Optional: installs to /usr/local/bin
```

## Install the Python SDK

### From Source

```bash
cd statehouse/python
pip install -e .
```

### From PyPI (when available)

```bash
pip install statehouse
```

## Verify Installation

1. **Start the daemon** (if not already running):

```bash
# With Docker:
docker run -d -p 50051:50051 --name statehouse rtacconi/statehouse:latest

# Or from source:
./target/release/statehoused
# or if installed: statehoused
```

You should see:
```
🚀 Statehouse daemon v0.1.1 (commit: abc1234)
📦 Storage: RocksDB
🌐 Listening on: 0.0.0.0:50051
```

2. **Test the Python SDK:**

```python
from statehouse import Statehouse

client = Statehouse(url="localhost:50051")
print(client.health())  # Should print: "healthy"
```

## Development Setup

For development, use Devbox (recommended):

```bash
# Install Devbox: https://www.jetify.com/docs/devbox/installing-devbox
devbox shell
cd python
pip install -e .
```

This provides pinned Rust and Python toolchains without system-wide installation.

## Next Steps

- [Running the Daemon](./running-statehoused.md)
- [Your First Transaction](./first-transaction.md)
