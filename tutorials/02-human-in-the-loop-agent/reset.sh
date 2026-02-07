#!/bin/bash
#
# Reset the approval agent state.
#
# Usage:
#   ./reset.sh                      # Reset default agent
#   ./reset.sh my-agent-id          # Reset specific agent

set -e

cd "$(dirname "$0")"

AGENT_ID="${1:-approval-agent-1}"

python3 agent.py --agent-id "$AGENT_ID" --reset
