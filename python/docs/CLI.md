# statehousectl - Statehouse Command-Line Interface

A command-line tool for interacting with the Statehouse daemon.

**Default Output**: All replay commands use human-readable "pretty" format by default. See [Output Format](../../docs/operations/output-format.md) for details.

## Installation

The CLI is installed automatically with the Statehouse Python SDK:

```bash
cd python
pip install -e .
```

After installation, the `statehousectl` command will be available in your PATH.

## Usage

```bash
statehousectl [--address ADDRESS] COMMAND [OPTIONS]
```

### Global Options

- `--address ADDRESS` - Statehouse daemon address (default: localhost:50051)

## Commands

### health

Check daemon health status.

```bash
statehousectl health
```

Example output:
```
✓ Daemon is healthy
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
statehousectl get AGENT_ID KEY [OPTIONS]
```

Options:
- `--namespace NAMESPACE` - Namespace (default: default)
- `--json-output` - Output as JSON
- `--pretty` - Pretty-print with value summary

Examples:
```bash
# Get a specific key
statehousectl get agent-1 task

# Get with pretty formatting
statehousectl get agent-1 context --pretty

# Get from different namespace
statehousectl --address localhost:50051 get agent-1 config --namespace production
```

Example output (default):
```
Key:       task
Version:   1
Commit TS: 1770488464

Value:
{
  "description": "Research the history of computing",
  "started_at": "2024-01-01T12:00:00Z"
}
```

Example output (--pretty):
```
Key:       context
Version:   3
Timestamp: 12:31:04Z

Value: {"topic":"distributed databases","sources":2}
```

### keys

List all keys for an agent.

```bash
statehousectl keys AGENT_ID [OPTIONS]
```

Options:
- `--namespace NAMESPACE` - Namespace (default: default)
- `--prefix PREFIX` - Filter keys by prefix

Examples:
```bash
# List all keys
statehousectl keys agent-1

# List keys with prefix
statehousectl keys agent-1 --prefix "step/"
```

Example output:
```
Keys for agent 'agent-1' (namespace: default):
  - answer
  - step/0000
  - step/0001
  - step/0002
  - task

Total: 5
```

### replay

Replay all events for an agent with **pretty output by default**.

```bash
statehousectl replay AGENT_ID [OPTIONS]
```

Options:
- `--namespace NAMESPACE` - Namespace (default: default)
- `--start-ts TS` - Start timestamp (optional)
- `--end-ts TS` - End timestamp (optional)
- `--limit N` - Limit number of operations shown
- `--verbose` - Show full details (txn_id, event_id, payload)
- `--json` - Output as JSON lines (machine-readable)

Examples:
```bash
# Replay all events (pretty format)
statehousectl replay agent-1

# Replay with time range
statehousectl replay agent-1 --start-ts 1770488000 --end-ts 1770489000

# Replay first 10 operations
statehousectl replay agent-1 --limit 10

# Verbose output with full details
statehousectl replay agent-1 --verbose

# JSON output for parsing
statehousectl replay agent-1 --json
```

Example output (default pretty format):
```
12:31:04Z  agent=research-1  WRITE  key=context           v=3  {"topic":"distributed db", "sources":2}
12:31:06Z  agent=research-1  TOOL   key=search            v=4  query="raft vs paxos"  results=8
12:31:10Z  agent=research-1  WRITE  key=draft             v=5  "First draft: ..."
12:31:11Z  agent=research-1  FINAL  key=answer            v=6  "Conclusion: ..."
```

Example output (--verbose):
```
12:31:04Z  agent=research-1  WRITE  key=context  v=3  txn=a3f7b2d1-4c8e  event=0
  payload: {"topic":"distributed databases","sources":["paper1.pdf","paper2.pdf"],"confidence":0.85}

12:31:06Z  agent=research-1  TOOL  key=search  v=4  txn=b4e8c3f2-5d9f  event=0
  payload: {"tool":"search","query":"raft vs paxos","results":8,"duration_ms":120}
```

Example output (--json):
```json
{"txn_id":"a3f7b2d1-4c8e","commit_ts":1770488464,"namespace":"default","agent_id":"research-1","operations":[{"key":"context","value":{"topic":"distributed databases"},"version":3}]}
{"txn_id":"b4e8c3f2-5d9f","commit_ts":1770488466,"namespace":"default","agent_id":"research-1","operations":[{"key":"search","value":{"tool":"search","query":"raft vs paxos"},"version":4}]}
```

### tail

Show the last N operations using **pretty replay format**.

```bash
statehousectl tail AGENT_ID [OPTIONS]
```

Options:
- `--namespace NAMESPACE` - Namespace (default: default)
- `--lines N` / `-n N` - Number of recent operations to show (default: 10)
- `--follow` / `-f` - Follow mode (not yet implemented)

Examples:
```bash
# Show last 10 operations (default)
statehousectl tail agent-1

# Show last 5 operations
statehousectl tail agent-1 -n 5

# Show last 20
statehousectl tail agent-1 --lines 20
```

Example output:
```
12:35:22Z  agent=research-2  WRITE  key=task              v=1  {"objective":"analyze tradeoffs"}
12:35:24Z  agent=research-2  NOTE   key=checkpoint        v=2  "Starting analysis phase"
12:35:30Z  agent=research-2  TOOL   key=calculator        v=3  compute="42 * 137"  result=5754
12:35:35Z  agent=research-2  DEL    key=draft             v=4  reason="superseded"
12:35:40Z  agent=research-2  FINAL  key=answer            v=5  "Analysis complete"
```

### inspect

Show agent summary with keys, stats, and recent activity.

```bash
statehousectl inspect AGENT_ID [OPTIONS]
```

Options:
- `--namespace NAMESPACE` - Namespace (default: default)

Example:
```bash
statehousectl inspect research-1
```

Example output:
```
=== Agent Inspect: research-1 ===
Namespace: default

Total Keys: 12

Keys (showing first 10):
  • context
  • search
  • draft
  • answer
  • task
  • step/001
  • step/002
  • checkpoint/start
  • checkpoint/middle
  • final/result

Total Events: 24

Recent Activity (last 5 events):
  12:35:30Z  agent=research-1  TOOL   key=calculator        v=3  compute="42 * 137"
  12:35:35Z  agent=research-1  DEL    key=draft             v=4  reason="superseded"
  12:35:40Z  agent=research-1  WRITE  key=summary           v=5  "Analysis complete"
  12:35:42Z  agent=research-1  NOTE   key=checkpoint        v=6  "Finalizing"
  12:35:45Z  agent=research-1  FINAL  key=answer            v=7  "Conclusion reached"
```

### dump

Dump all state for an agent to JSON.

```bash
statehousectl dump AGENT_ID [OPTIONS]
```

Options:
- `--namespace NAMESPACE` - Namespace (default: default)
- `--output FILE` / `-o FILE` - Output file (default: stdout)
- `--format FORMAT` - Output format: json, text (default: json)

Examples:
```bash
# Dump to stdout
statehousectl dump agent-1

# Dump to file
statehousectl dump agent-1 --output agent-1-state.json

# Text format
statehousectl dump agent-1 --format text
```

Example output (JSON format):
```json
{
  "task": {
    "value": {
      "description": "Research question"
    },
    "version": 1,
    "commit_ts": 1770488000
  },
  "step/0000": {
    "value": {
      "type": "tool_call",
      "tool": "search",
      "result": "..."
    },
    "version": 2,
    "commit_ts": 1770488010
  },
  "answer": {
    "value": {
      "answer": "Final answer",
      "completed_at": "2024-01-01T12:01:00Z"
    },
    "version": 5,
    "commit_ts": 1770488100
  }
}
```

## Output Format

The default replay output uses a **human-readable pretty format**. See [Output Format Specification](../../docs/operations/output-format.md) for full details.

Key features:
- One operation per line
- Timestamp in HH:MM:SSZ format (UTC)
- Operation type (WRITE, DEL, TOOL, NOTE, FINAL)
- Compact value summaries
- Stable column alignment

## Use Cases

### Debugging Agents

```bash
# Quick agent inspection
statehousectl inspect agent-1

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

# Watch specific agent in real-time
statehousectl tail agent-1 --follow  # (coming soon)
```

### Data Export

```bash
# Export agent state for analysis
statehousectl dump agent-1 --output backup.json

# Export replay as JSON for processing
statehousectl replay agent-1 --json > events.jsonl

# Export from production
statehousectl --address prod-host:50051 dump agent-1 --output prod-backup.json
```

### Troubleshooting

```bash
# Check if daemon is running
statehousectl health

# Verify agent has data
statehousectl keys agent-1

# Check specific step
statehousectl get agent-1 "step/0005"

# See recent errors (if stored as events)
statehousectl tail agent-1 --lines 50 | grep -i error
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

# Export replay events
statehousectl replay my-agent --json | jq '.operations[].key' | sort | uniq
```

## Exit Codes

- `0` - Success
- `1` - Error or key not found
- `130` - Interrupted (Ctrl+C)

## Notes

- **Pretty format is the default** for all replay commands
- Use `--json` when you need machine-readable output
- All commands support the `--namespace` option for multi-tenant setups
- JSON output is valid JSONL (one event per line) for streaming processing
- Use `--help` on any command for detailed options

## Examples

See the `examples/` directory for complete usage examples:
- `examples/agent_research/` - Agent using Statehouse
- `tutorials/01-resumable-research-agent/` - Full agent tutorial with CLI usage
