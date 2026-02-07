#!/usr/bin/env bash
#
# Build and publish the Statehouse Python package to PyPI.
#
# Prerequisites:
#   - pip install build twine
#   - PyPI account and token (https://pypi.org/manage/account/token/)
#
# Usage:
#   ./scripts/publish_python.sh           # Build only (no upload)
#   ./scripts/publish_python.sh --upload   # Build and upload to PyPI
#   ./scripts/publish_python.sh --test     # Build and upload to Test PyPI
#
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_DIR="$PROJECT_ROOT/python"

echo "📦 Building Statehouse Python package..."
echo ""

# Ensure build and twine are available
if ! python3 -c "import build" 2>/dev/null; then
    echo "Installing build..."
    python3 -m pip install build
fi

# Clean previous dist; run build from PROJECT_ROOT so python/build/ doesn't shadow the build package
rm -rf "$PYTHON_DIR/dist" "$PYTHON_DIR/build" "$PYTHON_DIR"/*.egg-info
cd "$PROJECT_ROOT"
python3 -m build --outdir python/dist python

echo ""
echo "✅ Build complete: $PYTHON_DIR/dist/"
ls -la "$PYTHON_DIR/dist/"
echo ""

cd "$PYTHON_DIR"
if [[ "${1:-}" == "--upload" ]]; then
    if ! python3 -c "import twine" 2>/dev/null; then
        echo "Installing twine..."
        python3 -m pip install twine
    fi
    echo "📤 Uploading to PyPI (pypi.org)..."
    python3 -m twine upload dist/*
    echo "✅ Published to PyPI. Install with: pip install statehouse"
elif [[ "${1:-}" == "--test" ]]; then
    if ! python3 -c "import twine" 2>/dev/null; then
        echo "Installing twine..."
        python3 -m pip install twine
    fi
    echo "📤 Uploading to Test PyPI (test.pypi.org)..."
    python3 -m twine upload --repository testpypi dist/*
    echo "✅ Published to Test PyPI. Install with: pip install -i https://test.pypi.org/simple/ statehouse"
else
    echo "To upload to PyPI:"
    echo "  1. Create a token at https://pypi.org/manage/account/token/"
    echo "  2. Run: ./scripts/publish_python.sh --upload"
    echo "  3. When prompted, use __token__ as username and your token as password"
    echo ""
    echo "To upload to Test PyPI first: ./scripts/publish_python.sh --test"
fi
