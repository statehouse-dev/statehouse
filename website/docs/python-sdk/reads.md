# Reading State

Statehouse provides several methods for reading state.

## Get State

Read the latest value for a key:

```python
result = client.get_state(agent_id="my-agent", key="memory")

if result.exists:
    print(result.value)     # The stored dict
    print(result.version)   # Version number (monotonic)
    print(result.commit_ts) # Commit timestamp
else:
    print("Key not found")
```

### StateResult

| Field | Type | Description |
|-------|------|-------------|
| `value` | `Dict[str, Any] \| None` | Stored value, or None if deleted |
| `version` | `int` | Version number |
| `commit_ts` | `int` | Commit timestamp |
| `exists` | `bool` | Whether the key exists |

## Get State at Version

Read a specific historical version:

```python
result = client.get_state_at_version(
    agent_id="my-agent",
    key="memory",
    version=5,
)
```

Returns the value as it was at version 5. Useful for debugging or auditing.

## List Keys

List all keys for an agent:

```python
keys = client.list_keys(agent_id="my-agent")
for key in keys:
    print(key)
```

Returns a list of key strings.

## Scan Prefix

Scan keys matching a prefix:

```python
results = client.scan_prefix(agent_id="my-agent", prefix="step:")

for result in results:
    print(f"{result.version}: {result.value}")
```

Returns a list of `StateResult` objects for all matching keys.

### Common Prefix Patterns

```python
# Steps in a workflow
results = client.scan_prefix(agent_id="agent", prefix="step:")

# Tool calls
results = client.scan_prefix(agent_id="agent", prefix="tool:")

# Memory entries
results = client.scan_prefix(agent_id="agent", prefix="memory:")
```

## Read Consistency

All reads see committed state only. You will never read:

- Uncommitted transaction data
- Partially committed transactions
- Stale data (reads always return latest)

This is the "committed write is immediately readable" invariant.

## Namespace Override

All read methods accept an optional `namespace` parameter:

```python
result = client.get_state(
    agent_id="my-agent",
    key="memory",
    namespace="production",
)
```

If not specified, uses the client's default namespace.

## Error Handling

```python
from statehouse import StatehouseError, NotFoundError

try:
    result = client.get_state(agent_id="agent", key="key")
except NotFoundError:
    print("Agent or key not found")
except StatehouseError as e:
    print(f"Read failed: {e}")
```
