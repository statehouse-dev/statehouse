#!/usr/bin/env bash
# Package Statehouse daemon for distribution

set -e

VERSION=${1:-$(git describe --tags --always --dirty)}
PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)
PACKAGE_NAME="statehouse-${VERSION}-${PLATFORM}-${ARCH}"
PACKAGE_DIR="dist/${PACKAGE_NAME}"

echo "📦 Packaging Statehouse daemon"
echo "Version: ${VERSION}"
echo "Platform: ${PLATFORM}-${ARCH}"
echo ""

# Clean previous build
echo "🧹 Cleaning previous builds..."
rm -rf dist/
mkdir -p "${PACKAGE_DIR}"

# Build release binary
echo "🔨 Building release binary..."
cargo build --release

# Copy binary
echo "📋 Copying binary..."
cp target/release/statehoused "${PACKAGE_DIR}/"
strip "${PACKAGE_DIR}/statehoused" 2>/dev/null || true  # Strip debug symbols

# Copy configuration
echo "📋 Copying configuration..."
cp statehouse.config.example "${PACKAGE_DIR}/"

# Create README
echo "📋 Creating README..."
cat > "${PACKAGE_DIR}/README.txt" << 'EOF'
# Statehouse Daemon Distribution

## Contents

- `statehoused`: The Statehouse daemon binary
- `statehouse.config.example`: Sample configuration file

## Quick Start

1. Start the daemon:
   ```bash
   ./statehoused
   ```

2. The daemon will start on `localhost:50051` by default.

3. Install the Python SDK to interact with the daemon:
   ```bash
   pip install statehouse
   ```

## Configuration

Configuration is done via environment variables. See `statehouse.config.example`
for available options.

Example:
```bash
export STATEHOUSE_ADDR=0.0.0.0:50051
export RUST_LOG=info
./statehoused
```

## Data Directory

By default, data is stored in `./statehouse_data/`. Make sure this directory
is writable.

For production deployments, back up this directory regularly.

## Logging

Set the log level with RUST_LOG:
```bash
RUST_LOG=debug ./statehoused  # Verbose logging
RUST_LOG=info ./statehoused   # Production logging (default)
```

## Documentation

Full documentation is available at:
https://statehouse.dev/docs

Or in the source repository:
https://github.com/statehouse/statehouse

## Support

- GitHub Issues: https://github.com/statehouse/statehouse/issues
- Documentation: https://statehouse.dev/docs
- FAQ: https://statehouse.dev/docs/FAQ

## License

See LICENSE.md in the source repository.
EOF

# Create tarball
echo "📦 Creating tarball..."
cd dist
tar -czf "${PACKAGE_NAME}.tar.gz" "${PACKAGE_NAME}"
cd ..

# Calculate checksums
echo "🔐 Calculating checksums..."
cd dist
shasum -a 256 "${PACKAGE_NAME}.tar.gz" > "${PACKAGE_NAME}.tar.gz.sha256"
cd ..

# Print summary
echo ""
echo "✅ Package created successfully!"
echo ""
echo "📦 Package: dist/${PACKAGE_NAME}.tar.gz"
echo "🔐 SHA256:  dist/${PACKAGE_NAME}.tar.gz.sha256"
echo ""
echo "Contents:"
du -sh "dist/${PACKAGE_NAME}"
echo ""
echo "Binary size:"
du -sh "dist/${PACKAGE_NAME}/statehoused"
echo ""

# Print install instructions
echo "📝 To install:"
echo "  tar -xzf dist/${PACKAGE_NAME}.tar.gz"
echo "  cd ${PACKAGE_NAME}"
echo "  ./statehoused"
