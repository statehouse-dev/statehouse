# CLI Operations Guide

This guide covers operational aspects of the `statehousectl` CLI tool.

## Installation

The CLI is bundled with the Python SDK:

```bash
cd python
pip install -e .
```

Verify installation:

```bash
statehousectl --help
statehousectl health
```

**Example output:**

```
✓ Daemon is healthy
```

## Connection

By default, the CLI connects to `localhost:50051`. Override with:

```bash
statehousectl --address <host>:<port> <command>
```

Or set an environment variable:

```bash
export STATEHOUSE_ADDRESS=production-host:50051
statehousectl health
```

## Output Modes

The CLI supports multiple output modes for different use cases:

### Pretty Format (Default)

Human-readable, one-line-per-operation format:

```bash
statehousectl replay cli-demo-agent
```

**Real output:**
```
00:00:34Z  agent=cli-demo-agent  WRITE  key=context               v=1  {"phase":"research","topic":"databases"}
00:00:35Z  agent=cli-demo-agent  TOOL   key=tool/search           v=1  {"query":"raft vs paxos","results":8.0}
00:00:36Z  agent=cli-demo-agent  WRITE  key=draft                 v=1  {"content":"Raft and Paxos are both consensus algorithms...","version":1.0}
00:00:37Z  agent=cli-demo-agent  FINAL  key=final/answer          v=1  {"conclusion":"Raft is simpler to implement","confidence":0.9}
```

### Verbose Format

Full details including transaction IDs and complete payloads:

```bash
statehousectl replay agent-1 --verbose
```

Output:
```
12:31:04Z  agent=research-1  WRITE  key=context  v=3  txn=a3f7b2d1  event=0
  payload: {"topic":"distributed databases","sources":["paper1.pdf"]}
```

### JSON Format

Machine-readable JSONL for parsing:

```bash
statehousectl replay agent-1 --json
```

Output:
```json
{"txn_id":"a3f7b2d1","commit_ts":1770488464,"operations":[...]}
```

## Common Workflows

### Agent Inspection

Quick overview of agent state and activity:

```bash
statehousectl inspect cli-demo-agent
```

**Real output:**
```
=== Agent Inspect: cli-demo-agent ===
Namespace: default

Total Keys: 4

Keys (showing first 10):
  • draft
  • final/answer
  • tool/search
  • context

Total Events: 4

Recent Activity (last 4 events):
  00:00:34Z  agent=cli-demo-agent  WRITE  key=context               v=1  {"topic":"databases","phase":"research"}
  00:00:35Z  agent=cli-demo-agent  TOOL   key=tool/search           v=1  {"query":"raft vs paxos","results":8.0}
  00:00:36Z  agent=cli-demo-agent  WRITE  key=draft                 v=1  {"content":"Raft and Paxos are both consensus algorithms...","version":1.0}
  00:00:37Z  agent=cli-demo-agent  FINAL  key=final/answer          v=1  {"conclusion":"Raft is simpler to implement","confidence":0.9}
```

Shows:
- Total key count
- Key list (first 10)
- Total event count
- Recent activity (last events in pretty format)

### Live Monitoring

Monitor agent activity in real-time:

```bash
# Show last 20 operations
statehousectl tail my-agent -n 20

# Follow new events (coming soon)
statehousectl tail my-agent --follow
```

### Debugging Failures

When an agent fails, inspect its state:

```bash
# Check latest state
statehousectl get my-agent last_error --pretty

# Review recent activity
statehousectl tail my-agent -n 50

# Full replay to find failure point
statehousectl replay my-agent --verbose
```

### Data Export

Export agent state for backup or analysis:

```bash
# Snapshot current state
statehousectl dump my-agent -o backup.json

# Export full event history
statehousectl replay my-agent --json > events.jsonl

# Export specific time range
statehousectl replay my-agent --start-ts 1770488000 --json > recent.jsonl
```

### Multi-Agent Systems

Inspect multiple agents:

```bash
# List agents (requires listing all keys first)
statehousectl keys global agent-registry

# Inspect each agent
for agent in agent-1 agent-2 agent-3; do
  echo "=== $agent ==="
  statehousectl inspect $agent
done
```

### Pipeline Processing

Use CLI in data pipelines:

```bash
# Extract all keys modified today
statehousectl replay agent-1 --json | \
  jq -r '.operations[].key' | \
  sort | uniq

# Count operations by type
statehousectl replay agent-1 --json | \
  jq -r '.operations[].key | split("/")[0]' | \
  sort | uniq -c

# Extract final answers
statehousectl replay agent-1 --json | \
  jq 'select(.operations[].key | startswith("final/"))'
```

## Performance Considerations

### Large Replays

For agents with many events:

```bash
# Use --limit to reduce output
statehousectl replay busy-agent --limit 100

# Use time ranges to filter
statehousectl replay busy-agent --start-ts 1770488000

# Export to file instead of terminal
statehousectl replay busy-agent --json > events.jsonl
```

### JSON Streaming

JSONL format is designed for streaming:

```bash
# Process events one at a time
statehousectl replay agent-1 --json | while read event; do
  echo "$event" | jq '.commit_ts'
done
```

### Parallel Operations

CLI operations are safe to run in parallel:

```bash
# Inspect multiple agents concurrently
parallel statehousectl inspect {} ::: agent-1 agent-2 agent-3
```

## Error Handling

The CLI uses standard exit codes:

```bash
statehousectl health
if [ $? -eq 0 ]; then
  echo "Daemon is healthy"
else
  echo "Daemon unreachable"
  exit 1
fi
```

Handle missing keys gracefully:

```bash
if statehousectl get agent-1 optional-key 2>/dev/null; then
  echo "Key exists"
else
  echo "Key not found, using default"
fi
```

## Scripting Examples

### Health Check Script

```bash
#!/bin/bash
set -e

echo "Checking Statehouse daemon..."

if ! statehousectl health > /dev/null 2>&1; then
  echo "ERROR: Daemon not responding"
  exit 1
fi

version=$(statehousectl version | grep "Version:" | cut -d' ' -f2)
echo "OK: Daemon running (version $version)"
```

### Agent Status Script

```bash
#!/bin/bash

AGENT_ID="$1"

if [ -z "$AGENT_ID" ]; then
  echo "Usage: $0 <agent_id>"
  exit 1
fi

echo "=== Agent Status: $AGENT_ID ==="
echo

# Check if agent has any data
key_count=$(statehousectl keys "$AGENT_ID" 2>/dev/null | grep "Total:" | awk '{print $2}')

if [ -z "$key_count" ] || [ "$key_count" -eq 0 ]; then
  echo "Status: No data"
  exit 0
fi

echo "Keys: $key_count"

# Get task if present
if statehousectl get "$AGENT_ID" task --pretty 2>/dev/null; then
  echo
fi

# Show recent activity
echo "Recent activity:"
statehousectl tail "$AGENT_ID" -n 5
```

### Backup Script

```bash
#!/bin/bash
set -e

BACKUP_DIR="./backups/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

echo "Backing up agent data to $BACKUP_DIR"

# Get list of all agents (assuming they're tracked)
AGENTS=$(statehousectl keys _system agent-list 2>/dev/null | grep "  - " | awk '{print $2}')

for agent in $AGENTS; do
  echo "  Backing up $agent..."
  statehousectl dump "$agent" -o "$BACKUP_DIR/$agent-state.json"
  statehousectl replay "$agent" --json > "$BACKUP_DIR/$agent-events.jsonl"
done

echo "Backup complete: $(ls $BACKUP_DIR | wc -l) files"
```

## Troubleshooting

### Connection Issues

```bash
# Check daemon is running
statehousectl health

# Check network connectivity
nc -zv localhost 50051

# Try explicit address
statehousectl --address localhost:50051 health
```

### Empty Output

If commands return no data:

```bash
# Verify agent exists
statehousectl keys my-agent

# Check namespace
statehousectl --namespace production keys my-agent

# Check daemon version
statehousectl version
```

### Performance Issues

If CLI is slow:

```bash
# Use --limit to reduce data transfer
statehousectl replay agent-1 --limit 10

# Use time ranges
statehousectl replay agent-1 --start-ts $(date -d '1 hour ago' +%s)

# Output directly to file
statehousectl dump agent-1 > /dev/null
```

## Integration Testing

Use CLI in integration tests:

```bash
#!/bin/bash
# test_agent.sh

set -e

# Setup
AGENT_ID="test-agent-$$"

# Run test
python my_agent.py --agent-id "$AGENT_ID"

# Verify results
result=$(statehousectl get "$AGENT_ID" final_answer --json | jq -r '.value.answer')

if [ "$result" = "expected answer" ]; then
  echo "TEST PASSED"
  exit 0
else
  echo "TEST FAILED: got $result"
  statehousectl replay "$AGENT_ID" --verbose
  exit 1
fi
```

## Best Practices

1. **Use pretty format for humans**: Default output is optimized for terminal viewing
2. **Use JSON for machines**: Always use `--json` when parsing programmatically
3. **Limit output size**: Use `--limit` and `--start-ts` for large replays
4. **Handle errors**: Check exit codes in scripts
5. **Use inspect first**: Quick overview before deep diving
6. **Export before debugging**: Save state before making changes

## See Also

- [Output Format Specification](./output-format.md) - Pretty format details
- [Python SDK CLI Module](../../python/docs/CLI.md) - Full command reference
- [Replay Semantics](../replay_semantics.md) - How replay ordering works
