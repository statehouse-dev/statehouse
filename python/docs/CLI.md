# statehousectl - Statehouse Command-Line Interface

A command-line tool for interacting with the Statehouse daemon.

## Installation

The CLI is installed automatically with the Statehouse Python SDK:

```bash
cd python
pip install -e .
```

After installation, the `statehousectl` command will be available in your PATH.

## Usage

```bash
statehousectl [--url URL] [--namespace NAMESPACE] COMMAND [OPTIONS]
```

### Global Options

- `--url URL` - Statehouse daemon URL (default: localhost:50051)
- `--namespace NAMESPACE` - Namespace to use (default: default)

## Commands

### health

Check daemon health status.

```bash
statehousectl health
```

Example output:
```
✅ Daemon is healthy: ok
```

### version

Get daemon version information.

```bash
statehousectl version
```

Example output:
```
Version: 0.1.0
Git SHA: abc123...
```

### get

Get a specific state value.

```bash
statehousectl get AGENT_ID KEY
```

Examples:
```bash
# Get a specific key
statehousectl get agent-1 task

# Get from different namespace
statehousectl --namespace production get agent-1 config
```

Example output:
```json
{
  "description": "Research the history of computing",
  "started_at": "2024-01-01T12:00:00Z"
}
```

### keys

List all keys for an agent.

```bash
statehousectl keys AGENT_ID [--prefix PREFIX]
```

Examples:
```bash
# List all keys
statehousectl keys agent-1

# List keys with prefix
statehousectl keys agent-1 --prefix "step/"
```

Example output:
```
Keys for agent 'agent-1':
  answer
  step/0000
  step/0001
  step/0002
  task

Total: 5 keys
```

### replay

Replay all events for an agent.

```bash
statehousectl replay AGENT_ID [--start-ts TS] [--end-ts TS] [--limit N]
```

Examples:
```bash
# Replay all events
statehousectl replay agent-1

# Replay with time range
statehousectl replay agent-1 --start-ts 100 --end-ts 200

# Replay first 10 events
statehousectl replay agent-1 --limit 10
```

Example output:
```
Replay for agent 'agent-1':
================================================================================

📦 Event 1
   Transaction ID: abc123...
   Commit TS: 100
   Operations: 1

   Operation 1:
     Key: task
     Version: 1
     Value: {
       "description": "Research question"
     }

================================================================================
Total: 1 events
```

### tail

Show the last N events for an agent.

```bash
statehousectl tail AGENT_ID [-n N]
```

Examples:
```bash
# Show last 10 events (default)
statehousectl tail agent-1

# Show last 5 events
statehousectl tail agent-1 -n 5
```

Example output:
```
Last 5 events for agent 'agent-1':
================================================================================
[ts=100] abc123... → task
[ts=101] def456... → step/0000
[ts=102] ghi789... → step/0001
[ts=103] jkl012... → step/0002
[ts=104] mno345... → answer
```

### dump

Dump all state for an agent to JSON.

```bash
statehousectl dump AGENT_ID [--output FILE]
```

Examples:
```bash
# Dump to stdout
statehousectl dump agent-1

# Dump to file
statehousectl dump agent-1 --output agent-1-state.json
```

Example output:
```json
{
  "agent_id": "agent-1",
  "namespace": "default",
  "key_count": 5,
  "state": {
    "task": {
      "description": "Research question"
    },
    "step/0000": {
      "type": "tool_call",
      "tool": "search",
      "result": "..."
    },
    "answer": {
      "answer": "Final answer",
      "completed_at": "2024-01-01T12:01:00Z"
    }
  }
}
```

## Use Cases

### Debugging Agents

```bash
# Check what the agent is working on
statehousectl get agent-1 task

# See all reasoning steps
statehousectl keys agent-1 --prefix "step/"

# View complete execution history
statehousectl replay agent-1
```

### Monitoring

```bash
# Check daemon health
statehousectl health

# Monitor recent activity
statehousectl tail agent-1 -n 20
```

### Data Export

```bash
# Export agent state for analysis
statehousectl dump agent-1 --output backup.json

# Export from production
statehousectl --namespace production dump agent-1 --output prod-backup.json
```

### Troubleshooting

```bash
# Check if daemon is running
statehousectl health

# Verify agent has data
statehousectl keys agent-1

# Check specific step
statehousectl get agent-1 "step/0005"
```

## Integration with Scripts

The CLI is designed to work well in shell scripts:

```bash
#!/bin/bash

# Check health before proceeding
if ! statehousectl health > /dev/null 2>&1; then
    echo "Daemon not running"
    exit 1
fi

# Get all agent state
statehousectl dump my-agent --output state.json

# Process with jq
cat state.json | jq '.state | keys'
```

## Python API

You can also use the CLI functionality from Python:

```python
from statehouse.cli import StatehouseCLI

cli = StatehouseCLI(url="localhost:50051")

# Check health
cli.health()

# Get state
cli.get("agent-1", "task")

# Replay events
cli.replay("agent-1")
```

## Exit Codes

- `0` - Success
- `1` - Error or key not found
- `130` - Interrupted (Ctrl+C)

## Environment Variables

- `STATEHOUSE_URL` - Default daemon URL (overridden by `--url`)

## Notes

- All JSON output is pretty-printed for readability
- The CLI uses the same Python SDK as agent code
- All commands support the `--namespace` flag for multi-tenant setups
- Use `--help` on any command for detailed options

## Examples

See the `examples/` directory for complete usage examples:
- `examples/agent_research/` - Agent using Statehouse
- `examples/cli_scripts/` - Shell scripts using statehousectl
