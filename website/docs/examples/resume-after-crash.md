# Resume After Crash

This example demonstrates recovering agent state after a crash.

## The Problem

AI agents run long tasks. If the process crashes:

- Work is lost
- User must restart from beginning
- Expensive LLM calls wasted

## The Solution

Store every step in Statehouse. On restart:

1. Read last completed step
2. Resume from that point
3. Continue to completion

## Implementation

### Store Every Step

```python
def agent_loop(client, agent_id, task):
    # Store the task
    with client.begin_transaction() as tx:
        tx.write(agent_id=agent_id, key="task", value={"task": task})
    
    step = 0
    while step < MAX_STEPS:
        # Think and act
        action = decide_next_action(step)
        
        # Store before executing (intention)
        with client.begin_transaction() as tx:
            tx.write(
                agent_id=agent_id,
                key=f"step:{step}",
                value={"action": action, "status": "pending"},
            )
        
        # Execute
        result = execute_action(action)
        
        # Store result (completion)
        with client.begin_transaction() as tx:
            tx.write(
                agent_id=agent_id,
                key=f"step:{step}",
                value={"action": action, "status": "done", "result": result},
            )
        
        if is_complete(result):
            return result
        
        step += 1
```

### Find Last Step

```python
def find_resume_point(client, agent_id) -> int:
    """Find the last completed step."""
    keys = client.list_keys(agent_id=agent_id)
    
    last_complete = -1
    for key in keys:
        if key.startswith("step:"):
            step_num = int(key.split(":")[0].split(":")[-1])
            state = client.get_state(agent_id=agent_id, key=key)
            if state.value.get("status") == "done":
                last_complete = max(last_complete, step_num)
    
    return last_complete
```

### Resume Function

```python
def resume_agent(client, agent_id):
    """Resume an interrupted agent."""
    # Check if there's work to resume
    task_state = client.get_state(agent_id=agent_id, key="task")
    if not task_state.exists:
        print("No task to resume")
        return
    
    task = task_state.value["task"]
    last_step = find_resume_point(client, agent_id)
    
    print(f"Resuming from step {last_step + 1}")
    
    # Continue from last completed step
    agent_loop_from_step(client, agent_id, task, start_step=last_step + 1)
```

## Complete Example

```python
from statehouse import Statehouse

def main():
    client = Statehouse()
    agent_id = "research-agent-001"
    
    # Check for resumable work
    task_state = client.get_state(agent_id=agent_id, key="task")
    
    if task_state.exists:
        last_step = find_resume_point(client, agent_id)
        answer = client.get_state(agent_id=agent_id, key="answer")
        
        if answer.exists:
            print(f"Task already complete: {answer.value}")
            return
        
        print(f"Resuming from step {last_step + 1}")
        continue_agent(client, agent_id, last_step + 1)
    else:
        # New task
        task = input("Enter task: ")
        run_agent(client, agent_id, task)
```

## Crash Scenarios

### Crash Before Step Stored

```python
action = decide_next_action(step)
# CRASH HERE
with client.begin_transaction() as tx:
    tx.write(...)
```

Result: Step not recorded. Resume repeats the decision.

### Crash After Step, Before Result

```python
with client.begin_transaction() as tx:
    tx.write(..., value={"status": "pending"})
# CRASH HERE
result = execute_action(action)
```

Result: Step shows "pending". Resume re-executes the action.

### Crash After Result Stored

```python
with client.begin_transaction() as tx:
    tx.write(..., value={"status": "done", "result": result})
# CRASH HERE
step += 1
```

Result: Step complete. Resume continues to next step.

## Idempotent Actions

For safe resumption, make actions idempotent:

```python
def execute_action(action):
    if action["type"] == "api_call":
        # Use idempotency key
        return call_api(
            endpoint=action["endpoint"],
            idempotency_key=action["id"],
        )
```

This prevents duplicate side effects.

## Best Practices

1. **Store intention before action**: Record what you're about to do
2. **Store result after action**: Record what happened
3. **Use unique step IDs**: Enable precise resumption
4. **Design for idempotency**: Safe to repeat actions
5. **Test crash recovery**: Include in your test suite
