# Tutorial 01: Resumable Research Agent

**Level**: Beginner  
**Duration**: 15 minutes  
**Prerequisites**: Statehouse daemon running

## What You'll Learn

This tutorial demonstrates the core Statehouse pattern: building an agent that:

1. **Persists all state** - Every step, tool call, and result is stored
2. **Survives crashes** - Agent can resume from the last checkpoint
3. **Provides full auditability** - Complete replay of agent's reasoning
4. **Uses transactions** - State updates are atomic and consistent

## What You'll Build

A simple research agent that:
- Accepts a research question
- Plans and executes tool calls
- Handles crashes gracefully
- Can resume mid-task
- Provides a complete audit trail

## Prerequisites

### 1. Start Statehouse Daemon

In a separate terminal:

```bash
# In-memory mode (recommended for tutorials)
STATEHOUSE_USE_MEMORY=1 statehoused

# Or persistent mode
statehoused
```

Verify it's running:

```bash
statehousectl health
# Expected: ✓ Daemon is healthy
```

### 2. Install Dependencies

```bash
cd tutorials/01-resumable-research-agent

# Install the Statehouse Python SDK (if not already installed)
cd ../../python
pip install -e .
cd -
```

## Quick Start

### Run a Simple Task

```bash
./run.sh --task "What is 42 * 137?"
```

**Expected Output:**

```
=== Resumable Research Agent Tutorial ===

[START] New task: What is 42 * 137?

[STEP 1]
  Executing: calculator({'expression': '42 * 137'})

[STEP 2]

[ANSWER] The result is 5754

✓ Task completed: The result is 5754

=== Full Replay ===

12:31:04Z  agent=tutorial-agent-1  WRITE  key=state                  v=1  {"task":"What is 42 * 137?", "step":0, "status":"running"}
12:31:04Z  agent=tutorial-agent-1  WRITE  key=step/0001/reasoning    v=2  {"step":1, "type":"reasoning", "data":{"action":{...}}}
12:31:05Z  agent=tutorial-agent-1  WRITE  key=step/0001/tool_result  v=3  {"step":1, "type":"tool_result", "data":{"tool":"calculator", "result":"5754"}}
12:31:05Z  agent=tutorial-agent-1  WRITE  key=state                  v=4  {"task":"What is 42 * 137?", "step":1, "status":"running"}
12:31:06Z  agent=tutorial-agent-1  WRITE  key=step/0002/reasoning    v=5  {"step":2, "type":"reasoning", "data":{"action":{...}}}
12:31:06Z  agent=tutorial-agent-1  WRITE  key=step/0002/final_answer v=6  {"step":2, "type":"final_answer", "data":{"answer":"The result is 5754"}}
12:31:06Z  agent=tutorial-agent-1  WRITE  key=state                  v=7  {"task":"What is 42 * 137?", "step":2, "status":"completed", "result":"The result is 5754"}
```

## Core Concepts

### 1. State Persistence

The agent stores its current state after every step:

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

### 2. Resume from Crashes

When the agent starts, it checks for existing state:

```python
def start(self, task: str, max_steps: int = 10) -> str:
    # Check if we're resuming
    state = self._load_state()
    
    if state and state.status == 'running':
        print(f"[RESUME] Continuing from step {state.step}")
        # Continue from where we left off
    else:
        # Start fresh
        state = AgentState(task=task, step=0, status='running')
```

### 3. Step Logging

Each step is logged for replay:

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

### 4. Replay for Auditability

The agent's complete history can be replayed:

```python
def replay(self):
    """Replay the agent's history in a human-readable format."""
    for line in self.client.replay_pretty(agent_id=self.agent_id):
        print(line)
```

## Hands-On Exercises

### Exercise 1: Basic Execution

Try different tasks:

```bash
# Mathematical calculation
./run.sh --task "What is 42 * 137?"

# Factual question
./run.sh --task "What is the capital of France?"

# Weather query
./run.sh --task "What is the weather in Paris?"
```

### Exercise 2: Crash and Resume

Simulate a crash during execution:

```bash
# Enable crash simulation (30% chance per step)
./run.sh --crash --task "What is 42 * 137?"
```

If it crashes, you'll see:

```
[CRASH] 💥 Agent crashed! Run ./run.sh --resume to continue.
```

Resume the agent:

```bash
./run.sh --resume
```

The agent will continue from where it crashed!

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

### Exercise 4: Full Replay

View the complete history:

```bash
./run.sh --replay
```

Or use the CLI:

```bash
statehousectl replay tutorial-agent-1
```

Or with verbose details:

```bash
statehousectl replay tutorial-agent-1 --verbose
```

### Exercise 5: Inspect with CLI

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
  - step/0002/reasoning
  - step/0002/final_answer
```

### Exercise 6: Reset and Start Fresh

Clear all state:

```bash
./run.sh --reset
```

Or:

```bash
./reset.sh
```

Now run a new task:

```bash
./run.sh --task "What is the capital of Japan?"
```

## Understanding the Code

### Agent Architecture

The `ResearchAgent` class has four key components:

1. **State Management** (`_load_state`, `_save_state`)
   - Persists current progress
   - Enables resume functionality

2. **Reasoning Loop** (`start`, `_reason`)
   - Plans next action based on task
   - Executes tools or returns answer

3. **Tool Execution** (`_execute_tool`)
   - Runs tools (calculator, search)
   - Stores results for later use

4. **Replay** (`replay`)
   - Shows complete audit trail
   - Uses Statehouse's replay API

### Key Patterns

#### Pattern 1: Checkpointing

Save state after every significant action:

```python
# After each step
self._save_state(state)
```

This ensures the agent can resume from any point.

#### Pattern 2: Structured Keys

Use hierarchical keys for organization:

```python
key = f"step/{step:04d}/{event_type}"
# Examples:
#   step/0001/reasoning
#   step/0001/tool_result
#   step/0002/final_answer
```

This makes replay output easy to understand.

#### Pattern 3: Transaction Usage

Wrap state updates in transactions:

```python
with self.client.transaction(agent_id=self.agent_id) as txn:
    txn.write("state", data)
```

This ensures atomic updates.

## Real-World Applications

This pattern is useful for:

1. **Long-Running Agents** - Agents that run for hours or days
2. **Batch Processing** - Processing many items with checkpoints
3. **Multi-Step Workflows** - Complex workflows with many stages
4. **Debugging** - Full replay helps debug agent behavior
5. **Compliance** - Complete audit trail for regulated environments

## Common Pitfalls

### Pitfall 1: Not Saving State Frequently

**Problem**: Agent crashes and loses significant progress.

**Solution**: Save state after every step:

```python
# BAD: Only save at the end
answer = self._complete_task()
self._save_state()

# GOOD: Save after each step
for step in steps:
    self._execute_step(step)
    self._save_state()  # Checkpoint!
```

### Pitfall 2: Missing Replay Information

**Problem**: Replay doesn't show what the agent did.

**Solution**: Log all significant actions:

```python
# Log reasoning
self._log_step(step, "reasoning", {"action": action})

# Log tool execution
self._log_step(step, "tool_result", {"tool": tool_name, "result": result})

# Log final answer
self._log_step(step, "final_answer", {"answer": answer})
```

### Pitfall 3: Not Using Transactions

**Problem**: State updates are inconsistent after crashes.

**Solution**: Always use transactions for related updates:

```python
# BAD: Separate writes (not atomic)
self.client.write("state", state_data)
self.client.write("step", step_data)

# GOOD: Atomic transaction
with self.client.transaction() as txn:
    txn.write("state", state_data)
    txn.write("step", step_data)
```

## Next Steps

### Extend the Agent

Try adding:

1. **More tools**: Add a `get_time` tool or `read_file` tool
2. **Better reasoning**: Use an actual LLM instead of rules
3. **Multi-agent**: Create multiple agents that coordinate
4. **Streaming**: Show progress in real-time

### Explore the SDK

```python
# Get specific version
result = client.get_state(agent_id, key, version=3)

# Scan keys by prefix
results = client.scan_prefix(agent_id, prefix="step/")

# Time-based replay
events = client.replay(agent_id, start_ts=yesterday, end_ts=now)
```

### Use the CLI

```bash
# List all keys
statehousectl keys tutorial-agent-1

# Get specific key
statehousectl get tutorial-agent-1 state --pretty

# Tail recent activity
statehousectl tail tutorial-agent-1 -n 20

# Dump all state
statehousectl dump tutorial-agent-1 -o backup.json
```

## Troubleshooting

### Daemon Not Running

**Error**: `Connection failed`

**Solution**:

```bash
# Start the daemon
STATEHOUSE_USE_MEMORY=1 statehoused

# In another terminal, verify
statehousectl health
```

### Agent Stuck in Running State

**Problem**: Agent crashed but state shows "running".

**Solution**:

```bash
# Reset the agent
./reset.sh

# Or manually update state
statehousectl get tutorial-agent-1 state
# Edit and write back with fixed status
```

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'statehouse'`

**Solution**:

```bash
# Install the SDK
cd ../../python
pip install -e .
```

## Summary

You've learned:

✓ How to persist agent state in Statehouse  
✓ How to resume agents after crashes  
✓ How to log steps for replay  
✓ How to use transactions for consistency  
✓ How to inspect and debug agents  

This pattern forms the foundation for building reliable, auditable AI agents.

## Further Reading

- [Python SDK Documentation](../../python/README.md)
- [Replay Semantics](../../docs/replay_semantics.md)
- [CLI Reference](../../python/statehouse/cli/README.md)
- [Reference Agent Example](../../examples/agent_research/)

## Feedback

Questions or issues? Open an issue on GitHub or check the [FAQ](../../docs/faq.md).
