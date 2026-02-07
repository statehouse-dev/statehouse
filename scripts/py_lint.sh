#!/bin/bash
#
# Python linting script for Statehouse project
#
# Runs ruff format check and ruff linting on Python code.
#

set -e

echo "=== Python Code Quality Check ==="
echo ""

# Check if ruff is installed
if ! command -v ruff &> /dev/null; then
    echo "❌ ruff is not installed"
    echo ""
    echo "Install with:"
    echo "  pip install ruff"
    echo ""
    exit 1
fi

# Format check
echo "Checking code formatting..."
if ruff format --check python/ tutorials/; then
    echo "✓ Code is properly formatted"
else
    echo "❌ Code formatting issues found"
    echo ""
    echo "Fix with:"
    echo "  ruff format python/ tutorials/"
    echo ""
    exit 1
fi

echo ""

# Linting
echo "Running linter..."
if ruff check python/ tutorials/; then
    echo "✓ No linting issues found"
else
    echo "❌ Linting issues found"
    echo ""
    echo "Fix with:"
    echo "  ruff check --fix python/ tutorials/"
    echo ""
    exit 1
fi

echo ""
echo "✓ All Python code quality checks passed"
