#!/usr/bin/env bash
set -euo pipefail

# Statehouse development script
# Runs the daemon in development mode with hot-reload (future: cargo watch)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "🔧 Statehouse Development Mode"
echo "================================"

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo "❌ Error: Rust/Cargo not found. Install from https://rustup.rs/"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 not found."
    exit 1
fi

echo "✅ Rust version: $(rustc --version)"
echo "✅ Python version: $(python3 --version)"
echo ""

# Build Rust daemon (debug mode)
echo "📦 Building statehoused..."
cargo build --bin statehoused
echo ""

# Run daemon
echo "🚀 Starting statehoused..."
RUST_LOG=info cargo run --bin statehoused
