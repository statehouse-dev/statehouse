#!/bin/bash
#
# Python test script for Statehouse project
#
# Runs pytest on Python SDK and tutorials.
#

set -e

echo "=== Python Test Suite ==="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest is not installed"
    echo ""
    echo "Install with:"
    echo "  pip install pytest"
    echo ""
    exit 1
fi

# Check if daemon is running
echo "Checking for running Statehouse daemon..."
if python3 -m statehouse.cli health > /dev/null 2>&1; then
    echo "✓ Daemon is running"
else
    echo "⚠ Daemon is not running - some tests may fail"
    echo ""
    echo "Start daemon with:"
    echo "  STATEHOUSE_USE_MEMORY=1 cargo run --bin statehouse-daemon"
    echo ""
fi

echo ""

# Run Python SDK tests
echo "Running Python SDK tests..."
cd python
if pytest tests/ -v; then
    echo "✓ SDK tests passed"
else
    echo "❌ SDK tests failed"
    cd ..
    exit 1
fi
cd ..

echo ""
echo "✓ All Python tests passed"
