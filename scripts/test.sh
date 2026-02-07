#!/usr/bin/env bash
set -euo pipefail

# Statehouse test runner
# Runs all tests (Rust + Python)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "🧪 Statehouse Test Suite"
echo "========================="
echo ""

EXIT_CODE=0

# Rust tests
if command -v cargo &> /dev/null; then
    echo "🦀 Running Rust tests..."
    if cargo test --workspace; then
        echo "✅ Rust tests passed"
    else
        echo "❌ Rust tests failed"
        EXIT_CODE=1
    fi
    echo ""
else
    echo "⚠️  Skipping Rust tests (cargo not found)"
    echo ""
fi

# Python tests
if command -v python3 &> /dev/null && [ -d "python" ]; then
    echo "🐍 Running Python tests..."
    cd python
    if [ -f "pyproject.toml" ]; then
        if command -v pytest &> /dev/null; then
            if pytest; then
                echo "✅ Python tests passed"
            else
                echo "❌ Python tests failed"
                EXIT_CODE=1
            fi
        else
            echo "⚠️  pytest not installed, skipping Python tests"
            echo "   Run: pip install pytest"
        fi
    else
        echo "⚠️  Python package not set up yet"
    fi
    cd "$PROJECT_ROOT"
    echo ""
else
    echo "⚠️  Skipping Python tests (python3 or python/ dir not found)"
    echo ""
fi

# Summary
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed"
fi

exit $EXIT_CODE
