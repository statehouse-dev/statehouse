# Audit and Replay

This example demonstrates using Statehouse for auditing and debugging agent behavior.

## Why Audit?

AI agents make decisions that affect real systems:

- What decisions did the agent make?
- Why did it choose a particular action?
- When did something go wrong?
- Can we reproduce the issue?

Statehouse's event log enables complete audit trails.

## Basic Audit Trail

Print all events for an agent:

```python
from statehouse import Statehouse

def audit_agent(agent_id: str):
    client = Statehouse()
    
    print(f"Audit trail for {agent_id}")
    print("-" * 50)
    
    for event in client.replay(agent_id=agent_id):
        print(f"\n[{event.commit_ts}] Transaction {event.txn_id}")
        for op in event.operations:
            if op.value is None:
                print(f"  DELETE {op.key}")
            else:
                print(f"  WRITE {op.key}")
                for k, v in op.value.items():
                    print(f"    {k}: {v}")

# Usage
audit_agent("research-agent-001")
```

## Filtering by Time

Audit specific time windows:

```python
def audit_time_range(agent_id: str, start: int, end: int):
    client = Statehouse()
    
    for event in client.replay(
        agent_id=agent_id,
        start_ts=start,
        end_ts=end,
    ):
        print(f"[{event.commit_ts}] {event.txn_id}")
```

## State Reconstruction

Reconstruct state at any point in time:

```python
def reconstruct_state_at(agent_id: str, at_ts: int) -> dict:
    """Reconstruct state as of a specific timestamp."""
    client = Statehouse()
    state = {}
    
    for event in client.replay(agent_id=agent_id, end_ts=at_ts):
        for op in event.operations:
            if op.value is None:
                state.pop(op.key, None)
            else:
                state[op.key] = op.value
    
    return state

# What was the state at timestamp 12345?
past_state = reconstruct_state_at("agent-001", 12345)
```

## Decision Analysis

Analyze agent decisions:

```python
def analyze_decisions(agent_id: str):
    client = Statehouse()
    
    decisions = []
    for event in client.replay(agent_id=agent_id):
        for op in event.operations:
            if op.key.startswith("step:") and "tool" not in op.key:
                decisions.append({
                    "step": op.key,
                    "timestamp": event.commit_ts,
                    "action": op.value,
                })
    
    print(f"Total decisions: {len(decisions)}")
    
    # Count action types
    action_types = {}
    for d in decisions:
        action_type = d["action"].get("type", "unknown")
        action_types[action_type] = action_types.get(action_type, 0) + 1
    
    print("Action breakdown:")
    for action_type, count in action_types.items():
        print(f"  {action_type}: {count}")
```

## Tool Usage Report

Track tool usage:

```python
def tool_usage_report(agent_id: str):
    client = Statehouse()
    
    tools = {}
    for event in client.replay(agent_id=agent_id):
        for op in event.operations:
            if ":tool" in op.key and op.value:
                tool_name = op.value.get("tool", "unknown")
                if tool_name not in tools:
                    tools[tool_name] = {"count": 0, "calls": []}
                tools[tool_name]["count"] += 1
                tools[tool_name]["calls"].append({
                    "timestamp": event.commit_ts,
                    "args": op.value.get("args"),
                })
    
    print("Tool Usage Report")
    print("-" * 40)
    for tool, data in tools.items():
        print(f"\n{tool}: {data['count']} calls")
        for call in data["calls"][:3]:  # Show first 3
            print(f"  [{call['timestamp']}] {call['args']}")
```

## Error Investigation

Find when errors occurred:

```python
def find_errors(agent_id: str):
    client = Statehouse()
    
    errors = []
    for event in client.replay(agent_id=agent_id):
        for op in event.operations:
            if op.value and op.value.get("error"):
                errors.append({
                    "timestamp": event.commit_ts,
                    "key": op.key,
                    "error": op.value["error"],
                })
    
    if errors:
        print(f"Found {len(errors)} errors:")
        for e in errors:
            print(f"  [{e['timestamp']}] {e['key']}: {e['error']}")
    else:
        print("No errors found")
```

## Export to JSON

Export audit trail for external analysis:

```python
import json

def export_audit_json(agent_id: str, output_file: str):
    client = Statehouse()
    
    events = []
    for event in client.replay(agent_id=agent_id):
        events.append({
            "txn_id": event.txn_id,
            "commit_ts": event.commit_ts,
            "operations": [
                {
                    "key": op.key,
                    "value": op.value,
                    "version": op.version,
                }
                for op in event.operations
            ],
        })
    
    with open(output_file, "w") as f:
        json.dump(events, f, indent=2)
    
    print(f"Exported {len(events)} events to {output_file}")
```

## Determinism Verification

Verify replay produces same state:

```python
def verify_determinism(agent_id: str):
    client = Statehouse()
    
    # Reconstruct state via replay
    reconstructed = {}
    for event in client.replay(agent_id=agent_id):
        for op in event.operations:
            if op.value is None:
                reconstructed.pop(op.key, None)
            else:
                reconstructed[op.key] = op.value
    
    # Get current state
    current = {}
    for key in client.list_keys(agent_id=agent_id):
        state = client.get_state(agent_id=agent_id, key=key)
        if state.exists:
            current[key] = state.value
    
    # Compare
    if reconstructed == current:
        print("Determinism verified: replay matches current state")
    else:
        print("MISMATCH detected")
        print(f"Reconstructed keys: {set(reconstructed.keys())}")
        print(f"Current keys: {set(current.keys())}")
```
