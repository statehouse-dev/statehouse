#!/bin/bash
#
# Convenience script for running the research agent tutorial
#

set -e

# Check if daemon is running
if ! python3 -m statehouse.cli health > /dev/null 2>&1; then
    echo "❌ Statehouse daemon is not running"
    echo ""
    echo "Start the daemon first:"
    echo "  STATEHOUSE_USE_MEMORY=1 cargo run --bin statehouse-daemon"
    echo ""
    exit 1
fi

# Run the agent
python3 agent.py "$@"
