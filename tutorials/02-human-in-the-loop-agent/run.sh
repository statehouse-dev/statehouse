#!/bin/bash
#
# Run the human-in-the-loop approval agent tutorial.
#
# Usage:
#   ./run.sh --refund 150.00          # Process a refund request
#   ./run.sh --access database-admin  # Process an access request
#   ./run.sh --resume                 # Resume after crash
#   ./run.sh --explain                # Explain the decision
#   ./run.sh --replay                 # View event history
#   ./run.sh --reset                  # Clear state

set -e

# Navigate to tutorial directory
cd "$(dirname "$0")"

# Check if daemon is running
if ! command -v statehousectl &> /dev/null; then
    echo "Warning: statehousectl not found. Make sure the daemon is running."
fi

# Run the agent
python3 agent.py "$@"
