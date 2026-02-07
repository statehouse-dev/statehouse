#!/bin/bash
#
# Run the research agent example
#
# Usage:
#   ./run.sh                    # Start interactive mode
#   ./run.sh "your question"    # Ask a question directly
#

set -e

# Configuration
AGENT_ID="${AGENT_ID:-agent-research-1}"
STATEHOUSE_ADDR="${STATEHOUSE_ADDR:-localhost:50051}"
PYTHON="${PYTHON:-python3}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Statehouse Research Agent${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Check if daemon is running
echo -e "${YELLOW}Checking Statehouse daemon...${NC}"
if ! pgrep -f statehoused > /dev/null; then
    echo -e "${RED}ERROR: Statehouse daemon is not running!${NC}"
    echo ""
    echo "Please start the daemon first (from the repo root):"
    echo "  cargo build --release && ./target/release/statehoused"
    echo ""
    echo "Or with in-memory storage:"
    echo "  STATEHOUSE_USE_MEMORY=1 ./target/release/statehoused"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓ Daemon is running${NC}"
echo ""

# Check Python dependencies
echo -e "${YELLOW}Checking Python dependencies...${NC}"
if ! $PYTHON -c "import grpc" 2>/dev/null; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    $PYTHON -m pip install grpcio grpcio-tools protobuf --quiet --user
fi

# Install statehouse package
if ! $PYTHON -c "import statehouse" 2>/dev/null; then
    echo -e "${YELLOW}Installing Statehouse Python SDK...${NC}"
    cd ../../python
    $PYTHON -m pip install -e . --quiet --user
    cd - > /dev/null
fi
echo -e "${GREEN}✓ Dependencies ready${NC}"
echo ""

# Set environment variables
export AGENT_ID="$AGENT_ID"
export STATEHOUSE_ADDR="$STATEHOUSE_ADDR"
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../../python"

# Run the agent
echo -e "${GREEN}Starting agent (ID: $AGENT_ID)${NC}"
echo ""

if [ $# -eq 0 ]; then
    # Interactive mode
    exec $PYTHON agent.py
else
    # Direct question mode: pipe "n", "ask <question>", "quit" into the agent
    printf 'n\nask %s\nquit\n' "$*" | $PYTHON agent.py
fi
