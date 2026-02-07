# statehousectl — CLI Reference

Command-line tool for interacting with the Statehouse daemon. Installed with the Python SDK (`pip install statehouse`).

## Usage

```bash
statehousectl [--address ADDRESS] COMMAND [OPTIONS]
```

**Global option:** `--address ADDRESS` — Daemon address (default: localhost:50051)

## Commands

### health

Check daemon health.

```bash
statehousectl health
```

### version

Show daemon version and Git SHA.

```bash
statehousectl version
```

### get

Get state for an agent and key.

```bash
statehousectl get AGENT_ID KEY [--namespace NAMESPACE] [--pretty]
```

### keys

List keys for an agent.

```bash
statehousectl keys AGENT_ID [--namespace NAMESPACE] [--prefix PREFIX]
```

### replay

Replay all events for an agent (pretty format by default).

```bash
statehousectl replay AGENT_ID [--namespace NAMESPACE] [--start-ts TS] [--end-ts TS] [--limit N] [--verbose] [--json]
```

- `--verbose` — Full details (txn_id, payload)
- `--json` — JSON lines (machine-readable)

### tail

Show last N events (pretty format).

```bash
statehousectl tail AGENT_ID [-n N] [--namespace NAMESPACE]
```

### dump

Dump all state for an agent to JSON.

```bash
statehousectl dump AGENT_ID [--namespace NAMESPACE] [-o FILE] [--format json|text]
```

## Output format

Replay and tail use a **human-readable pretty format** by default:

- One operation per line
- Timestamp (UTC), agent, operation type (WRITE, DEL, TOOL, NOTE, FINAL), key, version, value summary
- Use `--json` for machine-readable JSONL

## See also

- [Configuration](./configuration.md) — Daemon config
- [Python SDK Overview](../python-sdk/overview.md) — Programmatic access
