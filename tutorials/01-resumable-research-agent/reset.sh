#!/bin/bash
#
# Reset tutorial state by removing all tutorial agent data
#

set -e

# Check if daemon is running
if ! python3 -m statehouse.cli health > /dev/null 2>&1; then
    echo "❌ Statehouse daemon is not running"
    echo ""
    echo "Start the daemon first:"
    echo "  STATEHOUSE_USE_MEMORY=1 statehoused"
    echo ""
    exit 1
fi

# Run the agent with --reset flag
python3 agent.py --reset
