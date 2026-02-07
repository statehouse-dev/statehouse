# statehousectl CLI Documentation

Command-line interface for interacting with Statehouse daemon.

## Installation

Install the Statehouse Python SDK with CLI tools:

```bash
cd python
pip install -e .
```

Or install CLI dependencies explicitly:

```bash
pip install click tabulate
```

## Usage

```bash
statehousectl [OPTIONS] COMMAND [ARGS]...
```

### Global Options

- `--address TEXT` - Statehouse daemon address (default: `localhost:50051`)

### Commands

#### health

Check daemon health status.

```bash
statehousectl health
```

**Example:**
```bash
$ statehousectl health
✓ Daemon is healthy
```

#### get

Get state value for an agent and key.

```bash
statehousectl get [OPTIONS] AGENT_ID KEY
```

**Options:**
- `--namespace TEXT` - Namespace (default: `default`)
- `--version INTEGER` - Get specific version
- `--json` - Output as JSON

**Examples:**

Get latest value:
```bash
$ statehousectl get agent-1 config
Namespace: default
Agent ID:  agent-1
Key:       config
Version:   5

Value:
{
  "enabled": true,
  "max_retries": 3
}
```

Get specific version:
```bash
$ statehousectl get agent-1 config --version 3
```

JSON output:
```bash
$ statehousectl get agent-1 config --json
{
  "namespace": "default",
  "agent_id": "agent-1",
  "key": "config",
  "version": 5,
  "value": {
    "enabled": true,
    "max_retries": 3
  }
}
```

#### keys

List all keys for an agent.

```bash
statehousectl keys [OPTIONS] AGENT_ID
```

**Options:**
- `--namespace TEXT` - Namespace (default: `default`)
- `--prefix TEXT` - Filter keys by prefix
- `--json` - Output as JSON

**Examples:**

List all keys:
```bash
$ statehousectl keys agent-research-1
Keys for agent 'agent-research-1' in namespace 'default':

    1. session:session-1234
    2. session:session-1234:answer
    3. session:session-1234:question
    4. session:session-1234:step:0001
    5. session:session-1234:step:0002

Total: 5 keys
```

Filter by prefix:
```bash
$ statehousectl keys agent-research-1 --prefix "session:session-1234:step"
Keys for agent 'agent-research-1' in namespace 'default':
(filtered by prefix: 'session:session-1234:step')

    1. session:session-1234:step:0001
    2. session:session-1234:step:0002

Total: 2 keys
```

JSON output:
```bash
$ statehousectl keys agent-1 --json
{
  "namespace": "default",
  "agent_id": "agent-1",
  "count": 5,
  "keys": [
    "config",
    "state",
    "memory",
    "checkpoint",
    "metrics"
  ]
}
```

#### replay

Replay event history for an agent.

```bash
statehousectl replay [OPTIONS] AGENT_ID
```

**Options:**
- `--namespace TEXT` - Namespace (default: `default`)
- `--from-ts TEXT` - Start timestamp (ISO format)
- `--to-ts TEXT` - End timestamp (ISO format)
- `--limit INTEGER` - Limit number of events
- `--json` - Output as JSON

**Examples:**

Replay all events:
```bash
$ statehousectl replay agent-research-1
Replay for agent 'agent-research-1' in namespace 'default':

  1. [12:13:45] WRITE    session:session-1234
     Version: 1
     Value: {"session_id": "session-1234", "created_at": "2026-02-07T12:13:45Z"}

  2. [12:13:46] WRITE    session:session-1234:question
     Version: 2
     Value: {"question": "What is the capital of France?"}

  3. [12:13:50] WRITE    session:session-1234:answer
     Version: 3
     Value: {"text": "Paris is the capital of France", "confidence": 0.95}

Total: 3 events
```

With time range:
```bash
$ statehousectl replay agent-1 --from-ts "2026-02-07T12:00:00Z" --to-ts "2026-02-07T13:00:00Z"
```

Limited events:
```bash
$ statehousectl replay agent-1 --limit 10
```

JSON output:
```bash
$ statehousectl replay agent-1 --json | jq .
{
  "namespace": "default",
  "agent_id": "agent-1",
  "count": 3,
  "events": [
    {
      "timestamp": "2026-02-07T12:13:45Z",
      "operation": "WRITE",
      "key": "session:session-1234",
      "version": 1,
      "value": {...}
    },
    ...
  ]
}
```

#### tail

Show recent events (like `tail -f`).

```bash
statehousectl tail [OPTIONS] AGENT_ID
```

**Options:**
- `--namespace TEXT` - Namespace (default: `default`)
- `--lines INTEGER` - Number of recent events to show (default: 10)
- `--follow` / `-f` - Follow mode (show new events)

**Examples:**

Show last 10 events:
```bash
$ statehousectl tail agent-1
Recent events for agent 'agent-1':

[12:13:45] WRITE    session:session-1234 (v1)
[12:13:46] WRITE    session:session-1234:question (v2)
[12:13:50] WRITE    session:session-1234:answer (v3)
```

Show last 20 events:
```bash
$ statehousectl tail agent-1 --lines 20
```

Follow mode (wait for new events):
```bash
$ statehousectl tail agent-1 --follow
Recent events for agent 'agent-1':

[12:13:45] WRITE    session:session-1234 (v1)
[12:13:46] WRITE    session:session-1234:question (v2)

Waiting for new events (Ctrl+C to stop)...
[12:15:30] WRITE    session:session-1234:step:0001 (v4)
[12:15:31] WRITE    session:session-1234:step:0002 (v5)
```

#### dump

Dump all state for an agent as JSON.

```bash
statehousectl dump [OPTIONS] AGENT_ID
```

**Options:**
- `--namespace TEXT` - Namespace (default: `default`)
- `--output FILE` / `-o FILE` - Output file (default: stdout)

**Examples:**

Dump to stdout:
```bash
$ statehousectl dump agent-1
{
  "namespace": "default",
  "agent_id": "agent-1",
  "timestamp": "2026-02-07T12:20:00.123456",
  "key_count": 5,
  "state": {
    "config": {
      "version": 5,
      "value": {
        "enabled": true,
        "max_retries": 3
      }
    },
    "state": {
      "version": 12,
      "value": {
        "status": "active",
        "step": 5
      }
    },
    ...
  }
}
```

Dump to file:
```bash
$ statehousectl dump agent-1 -o agent-1-backup.json
✓ Dumped 5 keys to agent-1-backup.json
```

Pipe to jq:
```bash
$ statehousectl dump agent-1 | jq '.state.config.value'
{
  "enabled": true,
  "max_retries": 3
}
```

## Common Workflows

### Debugging an Agent

1. Check what keys the agent has:
   ```bash
   statehousectl keys agent-1
   ```

2. Get specific state:
   ```bash
   statehousectl get agent-1 current_step
   ```

3. Replay to see what happened:
   ```bash
   statehousectl replay agent-1 --limit 20
   ```

### Monitoring an Agent

Watch for new events in real-time:
```bash
statehousectl tail agent-1 --follow
```

### Backing Up Agent State

Dump entire state to a file:
```bash
statehousectl dump agent-1 -o backups/agent-1-$(date +%Y%m%d).json
```

### Inspecting Session History

For agents using session-based state:

1. List all sessions:
   ```bash
   statehousectl keys agent-research-1 --prefix "session:"
   ```

2. Get specific session data:
   ```bash
   statehousectl get agent-research-1 "session:session-1234:question"
   statehousectl get agent-research-1 "session:session-1234:answer"
   ```

3. Replay session events:
   ```bash
   statehousectl replay agent-research-1 | grep "session-1234"
   ```

### Remote Daemon

Connect to a remote daemon:
```bash
statehousectl --address prod.example.com:50051 health
statehousectl --address prod.example.com:50051 keys agent-1
```

## Output Formats

### Human-Readable (default)

Formatted for terminal viewing with colors and structure.

### JSON

Use `--json` flag for machine-readable output:
- Easy to pipe to `jq`
- Easy to parse in scripts
- Consistent structure

Example with jq:
```bash
# Get all keys starting with "config"
statehousectl keys agent-1 --json | jq -r '.keys[] | select(startswith("config"))'

# Count events
statehousectl replay agent-1 --json | jq '.count'

# Extract specific field from state
statehousectl get agent-1 config --json | jq '.value.max_retries'
```

## Environment Variables

- `STATEHOUSE_ADDR` - Default daemon address (overridden by `--address`)

Example:
```bash
export STATEHOUSE_ADDR="prod.example.com:50051"
statehousectl health
```

## Exit Codes

- `0` - Success
- `1` - Error (connection failed, key not found, etc.)

## Tips

1. **Use tab completion**: If your shell supports it, enable bash/zsh completion for `statehousectl`

2. **Alias common commands**:
   ```bash
   alias shctl="statehousectl"
   alias sh-health="statehousectl health"
   ```

3. **Combine with other tools**:
   ```bash
   # Watch for changes
   watch -n 1 'statehousectl keys agent-1'
   
   # Count keys
   statehousectl keys agent-1 --json | jq '.count'
   
   # Extract specific data
   statehousectl dump agent-1 | jq '.state | keys'
   ```

4. **Use in scripts**:
   ```bash
   #!/bin/bash
   if statehousectl health > /dev/null 2>&1; then
       echo "Daemon is healthy"
       statehousectl keys agent-1
   else
       echo "Daemon is down!"
       exit 1
   fi
   ```

## See Also

- Main documentation: `../../docs/`
- Python SDK: `../README.md`
- Agent examples: `../../examples/agent_research/`
