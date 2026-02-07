# Output Format Specification

## Design Goals

The replay output format is designed to be **readable in a terminal by a human**.

Key principles:

1. **One logical event = one line** in pretty output
2. Events must be scannable at a glance
3. Timestamps, agents, and operations should be immediately identifiable
4. Data summaries should be compact yet informative
5. Format should be stable across versions

---

## Default Pretty Format

### Line Template

```
<HH:MM:SSZ>  agent=<agent_id>  <OP>  key=<key>  v=<version>  <summary>
```

### Field Definitions

- **Timestamp**: ISO8601 short format (UTC), hours:minutes:seconds with Z suffix
- **agent_id**: Unique agent identifier (truncated if needed)
- **OP**: Operation type (see below)
- **key**: State key (truncated to 48 chars)
- **version**: Version number (u64)
- **summary**: Context-specific data summary

---

## Operation Types

| OP     | Meaning                  | Summary Content                          |
|--------|--------------------------|------------------------------------------|
| WRITE  | State write              | Value preview or compact JSON            |
| DEL    | State deletion           | Tombstone marker or reason               |
| TOOL   | Tool invocation          | Tool name + args or result preview       |
| NOTE   | Agent annotation         | Freeform text (reasoning, checkpoint)    |
| FINAL  | Final answer/output      | Completion message or result             |

### Mapping from Internal Events

- Events with `operation_type = "write"` → `WRITE`
- Events with `operation_type = "delete"` → `DEL`
- Events with key prefix `tool/` → `TOOL`
- Events with key prefix `note/` or `annotation/` → `NOTE`
- Events with key prefix `final/` or `answer/` → `FINAL`
- Fallback: inspect event metadata or use `WRITE` as default

---

## Summary Rules

### Strings
- Truncated to **120 characters** with ellipsis (`...`)
- Newlines replaced with `\\n` for single-line display
- Control characters escaped

### JSON Objects
- **Compact JSON** for small objects (< 80 chars): `{"field":"value"}`
- **Summary format** for large objects: `{field1:…, n_fields=N}`
- Nested objects collapsed to `{...}`

### Arrays
- **Length indicator**: `len=N` for arrays
- **Preview**: First 1-2 elements shown, e.g., `["item1", "item2", ...]`
- Empty arrays: `[]`

### Keys
- Truncated to **48 characters** with ellipsis
- Path-like keys retain prefix/suffix context: `long/path/.../final_part`

### Numbers, Booleans, Null
- Displayed as-is: `42`, `true`, `null`

---

## Timestamp Format

- **Format**: `HH:MM:SSZ` (24-hour, UTC)
- **Examples**: `12:31:04Z`, `09:15:22Z`
- Optional: microseconds for high-resolution events (`HH:MM:SS.ssssssZ`)

---

## Column Ordering and Spacing

Columns are **left-aligned** and separated by **2 spaces** for readability:

```
12:31:04Z  agent=research-1  WRITE  key=context           v=3  {"topic":"distributed db", "sources":2}
12:31:06Z  agent=research-1  TOOL   key=search            v=4  query="raft vs paxos" results=8
12:31:10Z  agent=research-1  WRITE  key=draft             v=5  "First draft: ..."
12:31:11Z  agent=research-1  FINAL  key=answer            v=6  "Conclusion: ..."
```

### Field Widths (Guideline)

- Timestamp: 10 chars
- Agent: 12-20 chars (dynamic, truncated if > 20)
- Operation: 5 chars (fixed width)
- Key: 16-24 chars (dynamic, truncated if > 48)
- Version: 3-8 chars (dynamic)
- Summary: Remaining line width (up to 120 chars)

---

## Verbose Format

Enabled with `--verbose` flag.

### Additional Fields

- **txn_id**: Transaction identifier (UUID)
- **event_id**: Event sequence number
- **namespace**: Namespace (if not default)
- **full_payload**: Complete event payload (JSON)

### Verbose Line Template

```
<timestamp>  agent=<agent_id>  <OP>  key=<key>  v=<version>  txn=<txn_id>  event=<event_id>
  payload: <full_json>
```

### Example

```
12:31:04Z  agent=research-1  WRITE  key=context  v=3  txn=a3f7b2d1-...  event=42
  payload: {"topic":"distributed databases","sources":["paper1","paper2"],"confidence":0.85}
```

---

## JSON Format

Enabled with `--json` flag.

### Output Format

- **One event per line** (JSONL)
- Raw event structure with all fields preserved
- Suitable for parsing, streaming, and machine consumption

### Schema

```json
{
  "timestamp": "2026-02-07T12:31:04Z",
  "namespace": "default",
  "agent_id": "research-1",
  "key": "context",
  "version": 3,
  "operation": "write",
  "txn_id": "a3f7b2d1-4c8e-4f12-9a8b-3d7e5c2f8a4b",
  "event_id": 42,
  "value": {
    "topic": "distributed databases",
    "sources": ["paper1", "paper2"],
    "confidence": 0.85
  }
}
```

---

## Example Output

### Default Pretty Format

```
12:31:04Z  agent=research-1  WRITE  key=context           v=3  {"topic":"distributed db", "sources":2}
12:31:06Z  agent=research-1  TOOL   key=search            v=4  query="raft vs paxos"  results=8
12:31:10Z  agent=research-1  WRITE  key=draft             v=5  "First draft: ..."
12:31:11Z  agent=research-1  FINAL  key=answer            v=6  "Conclusion: ..."
12:35:22Z  agent=research-2  WRITE  key=task              v=1  {"objective":"analyze tradeoffs"}
12:35:24Z  agent=research-2  NOTE   key=checkpoint        v=2  "Starting analysis phase"
12:35:30Z  agent=research-2  TOOL   key=calculator        v=3  compute="42 * 137"  result=5754
12:35:35Z  agent=research-2  DEL    key=draft             v=4  reason="superseded"
```

### Verbose Format

```
12:31:04Z  agent=research-1  WRITE  key=context  v=3  txn=a3f7b2d1-4c8e  event=42
  payload: {"topic":"distributed databases","sources":["paper1.pdf","paper2.pdf"],"confidence":0.85,"timestamp":"2026-02-07T12:31:04Z"}

12:31:06Z  agent=research-1  TOOL  key=search  v=4  txn=b4e8c3f2-5d9f  event=43
  payload: {"tool":"search","query":"raft vs paxos","results":8,"duration_ms":120}
```

### JSON Format

```json
{"timestamp":"2026-02-07T12:31:04Z","namespace":"default","agent_id":"research-1","key":"context","version":3,"operation":"write","txn_id":"a3f7b2d1-4c8e-4f12-9a8b-3d7e5c2f8a4b","event_id":42,"value":{"topic":"distributed databases","sources":["paper1.pdf","paper2.pdf"],"confidence":0.85}}
{"timestamp":"2026-02-07T12:31:06Z","namespace":"default","agent_id":"research-1","key":"search","version":4,"operation":"write","txn_id":"b4e8c3f2-5d9f-4a23-8b1c-2e6d4f9a3c7e","event_id":43,"value":{"tool":"search","query":"raft vs paxos","results":8,"duration_ms":120}}
```

---

## Format Stability

This format is the **default UX everywhere**:

- `statehousectl replay` uses pretty format by default
- `statehousectl tail` uses pretty format
- Python SDK `replay_pretty()` method generates this format
- Tutorial examples and documentation show this format

**Stability guarantee**: The pretty format will remain backward-compatible within major versions. Fields may be added, but existing field positions and semantics will not change.

---

## Implementation Notes

1. **Parsers should not rely on exact spacing** - field order is stable, spacing may vary
2. **Timestamps are always UTC** - no local timezone conversion in output
3. **Version numbers are always displayed** - even for v=1
4. **Agent IDs are never omitted** - essential for multi-agent scenarios
5. **Summary truncation is deterministic** - same input always produces same output
