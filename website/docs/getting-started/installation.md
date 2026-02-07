# Installation

Install Statehouse daemon and Python SDK.

## Prerequisites

- **Rust** (for building the daemon): `rustc` 1.70+ and `cargo`
- **Python** (for SDK): Python 3.9+
- **Storage**: Disk space for RocksDB data directory (default: `./statehouse-data/`)

## Install the Daemon

### Option 1: Build from Source (Recommended)

```bash
git clone https://github.com/statehouse-dev/statehouse.git
cd statehouse
cargo build --release
```

The daemon binary will be at `target/release/statehoused`.

### Option 2: Use Pre-built Binary

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

1. **Start the daemon:**

```bash
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
