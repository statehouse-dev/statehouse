---
sidebar_position: 2
---

# Tutorial 01: Resumable Research Agent

Build a research agent that survives crashes and provides full audit trails.

## Overview

This tutorial teaches the foundational Statehouse pattern: an agent that persists every step of its execution, enabling crash recovery and complete auditability.

**Duration**: 15-20 minutes  
**Level**: Beginner  
**Prerequisites**: Basic Python knowledge

## What You'll Build

A research agent that:

- Accepts research questions as input
- Plans and executes tool calls (search, calculator)
- Persists state after every step
- Resumes gracefully after crashes
- Provides complete replay of execution history

## What You'll Learn

By the end of this tutorial, you'll understand:

- How to persist agent state in Statehouse
- How to implement checkpoint-based recovery
- How to use transactions for atomic updates
- How to replay execution for debugging
- How to build auditable AI systems

## Prerequisites

### 1. Start Statehouse Daemon

In a terminal window, start the daemon:

```bash
# In-memory mode (recommended for tutorials)
STATEHOUSE_USE_MEMORY=1 statehoused
```

Or, if you prefer persistence:

```bash
statehoused
```

Verify it's running:

```bash
statehousectl health
```

**Expected output:**

```
✓ Daemon is healthy
```

### 2. Install Dependencies

```bash
cd tutorials/01-resumable-research-agent

# If you haven't installed the SDK yet
cd ../../python
pip install -e .
cd -
```

## Quick Start

Run your first agent:

```bash
./run.sh --task "What is 42 * 137?"
```

**Expected output:**

```
=== Resumable Research Agent Tutorial ===

[START] New task: What is 42 * 137?

[STEP 1]
  Executing: calculator({'expression': '42 * 137'})

[STEP 2]

[ANSWER] The result is 5754

✓ Task completed: The result is 5754
```

The agent then shows a **complete replay** of its execution:

```
=== Full Replay ===

12:31:04Z  agent=tutorial-agent-1  WRITE  key=state                  v=1
12:31:04Z  agent=tutorial-agent-1  WRITE  key=step/0001/reasoning    v=2
12:31:05Z  agent=tutorial-agent-1  WRITE  key=step/0001/tool_result  v=3
12:31:05Z  agent=tutorial-agent-1  WRITE  key=state                  v=4
12:31:06Z  agent=tutorial-agent-1  WRITE  key=step/0002/reasoning    v=5
12:31:06Z  agent=tutorial-agent-1  WRITE  key=step/0002/final_answer v=6
12:31:06Z  agent=tutorial-agent-1  WRITE  key=state                  v=7
```

Every step is recorded with:
- Timestamp
- Agent ID
- Operation type
- Key being modified
- Version number

## Core Concepts

### State Persistence

The agent stores its current state in Statehouse:

```python
def _save_state(self, state: AgentState):
    """Save agent state to Statehouse."""
    with self.client.transaction(agent_id=self.agent_id) as txn:
        txn.write("state", {
            "task": state.task,
            "step": state.step,
            "status": state.status,
            "result": state.result
        })
```

This ensures:
- **Atomicity**: State updates are all-or-nothing
- **Consistency**: State always reflects actual progress
- **Durability**: State survives process crashes

### Crash Recovery

When starting, the agent checks for existing state:

```python
def start(self, task: str) -> str:
    # Try to load previous state
    state = self._load_state()
    
    if state and state.status == 'running':
        print(f"[RESUME] Continuing from step {state.step}")
        # Continue from last checkpoint
    else:
        # Start fresh
        state = AgentState(task=task, step=0, status='running')
        self._save_state(state)
```

This pattern enables:
- **Seamless resume** after crashes
- **No lost work** - all progress is saved
- **Idempotent operations** - safe to retry

### Step Logging

Each step is logged with structured data:

```python
def _log_step(self, step: int, event_type: str, data: Dict[str, Any]):
    """Log a step to Statehouse for replay."""
    key = f"step/{step:04d}/{event_type}"
    
    with self.client.transaction(agent_id=self.agent_id) as txn:
        txn.write(key, {
            "step": step,
            "type": event_type,
            "timestamp": int(time.time()),
            "data": data
        })
```

The hierarchical keys create a natural ordering:
- `step/0001/reasoning`
- `step/0001/tool_result`
- `step/0002/reasoning`
- `step/0002/final_answer`

### Replay

Full execution history is available via replay:

```python
def replay(self):
    """Replay the agent's history."""
    for line in self.client.replay_pretty(agent_id=self.agent_id):
        print(line)
```

Replay provides:
- **Auditability**: See exactly what the agent did
- **Debugging**: Understand failures
- **Provenance**: Track where answers came from

## Hands-On Exercises

### Exercise 1: Try Different Tasks

Run the agent with different types of questions:

```bash
# Mathematical
./run.sh --task "What is 42 * 137?"

# Factual (mocked search)
./run.sh --task "What is the capital of France?"

# Information lookup
./run.sh --task "What is the weather in Paris?"
```

### Exercise 2: Simulate Crashes

Enable crash simulation (30% chance per step):

```bash
./run.sh --crash --task "What is 42 * 137?"
```

If it crashes, you'll see:

```
[CRASH] 💥 Agent crashed! Run ./run.sh --resume to continue.
```

Resume from the checkpoint:

```bash
./run.sh --resume
```

The agent picks up where it left off!

### Exercise 3: Inspect State

View the agent's current state:

```bash
statehousectl get tutorial-agent-1 state
```

**Output:**

```
Key:       state
Version:   4
Commit TS: 1770488464

Value:
{
  "task": "What is 42 * 137?",
  "step": 1,
  "status": "running",
  "result": null
}
```

### Exercise 4: View Full History

Use the CLI to replay:

```bash
# Pretty format (default)
statehousectl replay tutorial-agent-1

# Verbose (with transaction IDs)
statehousectl replay tutorial-agent-1 --verbose

# JSON (for parsing)
statehousectl replay tutorial-agent-1 --json
```

### Exercise 5: Agent Inspection

Get a summary of agent activity:

```bash
statehousectl inspect tutorial-agent-1
```

**Output:**

```
Agent: tutorial-agent-1
Namespace: default

State Summary:
  Current keys: 7

Activity Summary:
  Total events: 7
  Write operations: 7
  Delete operations: 0
  First activity: 12:31:04Z
  Latest activity: 12:31:06Z

Sample Keys:
  - state
  - step/0001/reasoning
  - step/0001/tool_result
  ...
```

### Exercise 6: Reset and Start Fresh

Clear all agent state:

```bash
./reset.sh
```

Now run a new task:

```bash
./run.sh --task "What is the capital of Japan?"
```

## Code Walkthrough

The tutorial code is designed for learning. Let's walk through the key parts.

### Agent Initialization

```python
class ResearchAgent:
    def __init__(self, agent_id: str, statehouse_url: str = "localhost:50051"):
        self.agent_id = agent_id
        self.client = Statehouse(url=statehouse_url)
```

Simple initialization:
- `agent_id` uniquely identifies this agent
- `client` connects to the Statehouse daemon

### Main Loop

```python
def start(self, task: str, max_steps: int = 10) -> str:
    state = self._load_state()
    
    if state and state.status == 'running':
        # Resume from checkpoint
        print(f"[RESUME] Continuing from step {state.step}")
    else:
        # Start fresh
        state = AgentState(task=task, step=0, status='running')
        self._save_state(state)
    
    # Reasoning loop
    while state.step < max_steps and state.status == 'running':
        state.step += 1
        
        action = self._reason(state)
        self._log_step(state.step, "reasoning", {"action": action})
        
        if action["type"] == "tool":
            result = self._execute_tool(action["tool"], action["args"])
            self._log_step(state.step, "tool_result", {...})
        elif action["type"] == "answer":
            state.result = action["answer"]
            state.status = 'completed'
            self._log_step(state.step, "final_answer", {...})
            return state.result
        
        self._save_state(state)  # Checkpoint!
```

Key patterns:
- Check for existing state (resume)
- Save after every step (checkpoint)
- Log all actions (auditability)

### Tool Execution

```python
def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
    print(f"  Executing: {tool_name}({args})")
    
    if tool_name == "calculator":
        expr = args.get("expression", "0")
        result = eval(expr, {"__builtins__": {}})
        return str(result)
    
    elif tool_name == "search":
        # Mock search results
        query = args.get("query", "")
        if "capital" in query.lower():
            # Return mock results based on query
            ...
```

For the tutorial, tools are mocked with deterministic results. In production, replace with real tool implementations.

## Real-World Applications

This pattern is valuable for:

### 1. Long-Running Agents

Agents that run for hours or days need checkpoints:

```python
# Every 10 steps, save progress
if step % 10 == 0:
    self._save_state(state)
```

### 2. Batch Processing

Process thousands of items with fault tolerance:

```python
for item in items:
    process_item(item)
    self._save_progress(item.id)  # Resume point
```

### 3. Compliance and Auditing

Full replay provides audit trails:

```bash
# Export audit trail
statehousectl replay compliance-agent --json > audit.jsonl
```

### 4. Debugging

Replay helps understand failures:

```bash
# Verbose replay shows all details
statehousectl replay failed-agent --verbose
```

## Common Pitfalls

### Pitfall 1: Not Checkpointing Frequently

**Problem**: Crash loses hours of work.

**Solution**: Save state after every significant step:

```python
# BAD: Only save at end
complete_long_task()
self._save_state()

# GOOD: Checkpoint frequently
for step in long_task_steps:
    complete_step(step)
    self._save_state()  # Checkpoint!
```

### Pitfall 2: Missing Replay Data

**Problem**: Replay doesn't show what happened.

**Solution**: Log all significant actions:

```python
self._log_step(step, "reasoning", {"action": action})
self._log_step(step, "tool_result", {"tool": tool, "result": result})
```

### Pitfall 3: Non-Atomic Updates

**Problem**: State inconsistent after crash.

**Solution**: Use transactions:

```python
# BAD: Separate writes (not atomic)
self.client.write("state", state_data)
self.client.write("progress", progress_data)

# GOOD: Atomic transaction
with self.client.transaction() as txn:
    txn.write("state", state_data)
    txn.write("progress", progress_data)
```

## Next Steps

### Extend the Tutorial

Try adding:

1. **Real LLM**: Replace `_reason()` with actual LLM calls
2. **More tools**: Add file operations, API calls, database queries
3. **Parallel execution**: Run multiple agents
4. **Streaming output**: Show progress in real-time

### Explore the SDK

```python
# Read specific versions
result = client.get_state(agent_id, key, version=5)

# Scan by prefix
steps = client.scan_prefix(agent_id, prefix="step/")

# Time-based replay
events = client.replay(agent_id, start_ts=yesterday)
```

### Use the CLI

```bash
# List all agent keys
statehousectl keys tutorial-agent-1

# Get specific state
statehousectl get tutorial-agent-1 state --pretty

# Tail recent activity
statehousectl tail tutorial-agent-1 -n 20

# Export state
statehousectl dump tutorial-agent-1 -o backup.json
```

## Troubleshooting

### Daemon Not Responding

**Error**: `Connection failed`

**Solution**:

```bash
# Check daemon status
statehousectl health

# If not running, start it
STATEHOUSE_USE_MEMORY=1 statehoused
```

### Agent Won't Resume

**Problem**: Agent always starts fresh.

**Check**:

```bash
# Is state actually saved?
statehousectl get tutorial-agent-1 state

# Is status "running"?
statehousectl get tutorial-agent-1 state | grep status
```

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'statehouse'`

**Solution**:

```bash
cd ../../python
pip install -e .
```

## Source Code

All tutorial code is available in the repository:

[`tutorials/01-resumable-research-agent/`](https://github.com/yourusername/statehouse/tree/main/tutorials/01-resumable-research-agent)

Key files:
- [`agent.py`](https://github.com/yourusername/statehouse/blob/main/tutorials/01-resumable-research-agent/agent.py) - Main agent implementation
- [`memory.py`](https://github.com/yourusername/statehouse/blob/main/tutorials/01-resumable-research-agent/memory.py) - Memory abstraction
- [`tools.py`](https://github.com/yourusername/statehouse/blob/main/tutorials/01-resumable-research-agent/tools.py) - Tool registry
- [`run.sh`](https://github.com/yourusername/statehouse/blob/main/tutorials/01-resumable-research-agent/run.sh) - Convenience script
- [`README.md`](https://github.com/yourusername/statehouse/blob/main/tutorials/01-resumable-research-agent/README.md) - Full tutorial guide

## Summary

You've learned:

✓ How to persist agent state in Statehouse  
✓ How to implement crash recovery with checkpoints  
✓ How to log steps for complete auditability  
✓ How to use transactions for consistency  
✓ How to inspect and debug agents with CLI tools  

These patterns form the foundation for building **reliable, auditable AI agents** that survive failures and provide complete transparency.

## Further Reading

- [Python SDK Overview](../python-sdk/overview.md)
- [Replay Semantics](../concepts/replay.md)
- [Transaction Guarantees](../concepts/transactions.md)
- [CLI Reference](../operations/cli.md)
- [Reference Agent Example](../examples/reference-agent.md)

## Feedback

Questions or issues?

- Check the [FAQ](../faq.md)
- Open an issue on [GitHub](https://github.com/yourusername/statehouse/issues)
- Join the [Discord community](#)
