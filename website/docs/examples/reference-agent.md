# Reference Agent

The repository includes a reference agent implementation demonstrating Statehouse integration.

## Location

```
examples/agent_research/
├── agent.py      # Main agent loop
├── memory.py     # Statehouse memory abstraction
├── tools.py      # Tool implementations
├── run.sh        # Runner script
└── README.md     # Detailed documentation
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Agent     │────▶│   Memory    │────▶│ Statehouse  │
│   Loop      │     │ Abstraction │     │   Daemon    │
└─────────────┘     └─────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│   Tools     │
│  Registry   │
└─────────────┘
```

## Running the Agent

```bash
cd examples/agent_research

# Start daemon first
statehoused &

# Run agent with a task
./run.sh --task "What is 42 * 137?"
```

## Agent Loop

The agent follows a simple loop:

```python
def run(self, task: str) -> str:
    self.memory.store_task(task)
    
    for step in range(self.max_steps):
        # Decide next action
        action = self.decide_action()
        
        # Store decision
        self.memory.store_step(step, action)
        
        if action["type"] == "tool":
            # Execute tool
            result = self.execute_tool(action)
            self.memory.store_tool_result(step, result)
            
        elif action["type"] == "answer":
            # Final answer
            self.memory.store_answer(action["content"])
            return action["content"]
    
    return "Max steps reached"
```

## State Schema

The agent stores state with structured keys:

| Key Pattern | Content |
|-------------|---------|
| `task` | Current objective |
| `step:{n}` | Step n decision |
| `step:{n}:tool` | Tool call for step n |
| `step:{n}:result` | Tool result for step n |
| `answer` | Final answer |

## Memory Abstraction

The `Memory` class wraps Statehouse:

```python
class Memory:
    def __init__(self, client, agent_id):
        self.client = client
        self.agent_id = agent_id
    
    def store_step(self, step: int, data: dict):
        with self.client.begin_transaction() as tx:
            tx.write(
                agent_id=self.agent_id,
                key=f"step:{step}",
                value=data,
            )
    
    def get_last_step(self) -> int:
        keys = self.client.list_keys(agent_id=self.agent_id)
        step_keys = [k for k in keys if k.startswith("step:")]
        if not step_keys:
            return -1
        return max(int(k.split(":")[1]) for k in step_keys)
```

## Tools

Available tools:

| Tool | Description |
|------|-------------|
| `search` | Mock web search |
| `calculator` | Basic arithmetic |
| `get_time` | Current timestamp |
| `read_file` | Read file contents |

## LLM Integration

The agent uses a provider interface:

```python
class LLMProvider:
    def generate(self, prompt: str) -> str:
        raise NotImplementedError

class MockProvider(LLMProvider):
    """Rule-based for offline testing."""
    
class OpenAIProvider(LLMProvider):
    """Real LLM integration."""
```

Default uses MockProvider for offline operation.

## Replay

View agent history:

```bash
./run.sh --replay
```

Output:

```
[1707300000] Transaction abc123
  step:0 = {"action": "tool", "tool": "calculator", "args": "42 * 137"}
[1707300001] Transaction def456
  step:0:result = {"result": "5754"}
[1707300002] Transaction ghi789
  answer = "The result is 5754"
```

## Resume After Crash

The agent can resume interrupted work:

```bash
# Agent crashes mid-execution
./run.sh --task "Complex task"
# Ctrl+C

# Resume from last step
./run.sh --resume
```

Resume finds the last completed step and continues.

## Customization

Extend the agent:

```python
# Add new tool
@register_tool("my_tool")
def my_tool(args: str) -> str:
    return "result"

# Use different LLM
agent = Agent(
    memory=memory,
    llm=OpenAIProvider(api_key="..."),
)
```
