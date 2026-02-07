# Research Agent Example

A reference implementation of an AI research agent using Statehouse for state management.

## How to use (quick reference)

1. **Start the daemon** (in a separate terminal, from the repo root):
   ```bash
   cargo build --release
   STATEHOUSE_USE_MEMORY=1 ./target/release/statehoused
   ```

2. **Run the agent** (from this directory or repo root):
   ```bash
   ./run.sh
   # or: python3 agent.py   (with PYTHONPATH or pip install -e ../../python)
   ```

3. **Interactive commands** at the `> ` prompt:
   - **`ask <question>`** – Run a research task (e.g. `ask What is Statehouse?`, `ask find information about Rust`)
   - **`replay`** – Replay the current session’s history (steps, tool calls, answer)
   - **`replay <session_id>`** – Replay a specific session (e.g. `replay session-1707311234`)
   - **`quit`** (or `exit`, `q`) – Exit the agent

4. **First run:** You may see “Resume from previous session? (y/n)”. Type **`n`** for a new session or **`y`** to continue the last one.

**Adding info / asking questions:** The agent gets context from the text you type after **`ask`** and from tool results (e.g. mock search). There is no separate add-info command—use **`ask your question here`**; the agent stores the question, runs tools, and stores the answer. Use **`replay`** to see what was stored.

### Where does the "information" come from?

The example uses **mock tools**—there is no real web search. The **search** tool returns fake results so you can see the full flow (question → plan → tool call → stored result → answer). When your question mentions **Statehouse**, the mock returns short real facts about this project so the answer is at least meaningful. In a real deployment you would replace the mock with a true search API (e.g. web search, internal docs, RAG).

### Working example (copy-paste)

With the daemon running and `./run.sh` started, type exactly:

```
n
ask find information about Statehouse
replay
quit
```

**What you’ll see:** After `n` (new session), the agent will run a search step and then synthesize an answer. Example output:

```
[START] New session: session-1234567890
...
> ask find information about Statehouse
[QUESTION] find information about Statehouse
[PLAN] 2 steps planned
[STEP 1] Search for relevant information
[RESULT] Found 2 results for "find information about Statehouse"
[STEP 2] Synthesize final answer
[ANSWER] Based on the research, here's what I found:
1. Found 2 results for "find information about Statehouse"
[COMPLETE] Session session-1234567890 finished after 2 steps
> replay
[REPLAY] Replaying session session-1234567890
...
> quit
[SHUTDOWN] Agent stopped
```

Other working `ask` examples: **`ask What is Statehouse?`**, **`ask search for Rust`**, **`ask calculate 10 times 5`** (uses the calculator tool).

---

## Overview

This example demonstrates how to build a production-ready AI agent that:

- **Stores every step** in Statehouse for full auditability
- **Stores tool calls and outputs** with timestamps
- **Stores final answers with provenance** (sources, steps, tools used)
- **Can resume from crashes** by reading its last state
- **Supports replay** to see exactly what the agent did

## Architecture

```
agent.py       - Main agent loop and orchestration
memory.py      - Memory management abstractions for Statehouse
tools.py       - Tool registry (search, calculator, file ops)
run.sh         - Startup script with dependency checking
```

## How It Works

### 1. Session Management

Each research session gets a unique ID:

```python
session_id = f"session-{int(time.time())}"
```

The agent stores session metadata:

```python
{
    'session_id': 'session-1707311234',
    'created_at': '2026-02-07T12:13:54Z',
    'status': 'active',
    'step_count': 0
}
```

### 2. Step-by-Step Storage

Every reasoning step is stored:

```python
await memory.store_step(
    session_id,
    step_number,
    {
        'type': 'tool',
        'tool': 'search',
        'action': 'Search for relevant information',
        'args': {'query': question}
    }
)
```

### 3. Tool Call Provenance

Tool calls and their results are stored separately:

```python
await memory.store_tool_result(
    session_id,
    step_number,
    'search',
    {'query': 'statehouse architecture'},
    {
        'results': [...],
        'summary': 'Found 2 results',
        'source': 'mock_search_api'
    }
)
```

### 4. Final Answer with Full Provenance

The final answer includes complete provenance:

```python
await memory.store_answer(
    session_id,
    answer={'text': '...', 'confidence': 0.85},
    provenance={
        'question': question,
        'steps': 5,
        'tools_used': ['search', 'calculator'],
        'results': [...]
    }
)
```

### 5. Crash Recovery

On startup, the agent checks for incomplete sessions:

```python
last_session = await memory.get_last_session()
if last_session and last_session['status'] == 'active':
    # Offer to resume
    self.session_id = last_session['session_id']
    self.step_count = last_session['step_count']
```

### 6. Replay and Audit

The agent can replay any session's complete history:

```python
async for event in memory.replay_session(session_id):
    print(f"[{event.timestamp}] {event.operation}")
    print(f"  Key: {event.key}")
    print(f"  Value: {event.value}")
```

## Running the Agent

### Prerequisites

1. Start the Statehouse daemon (from the repo root):

```bash
cargo build --release
./target/release/statehoused
# or in-memory (no disk): STATEHOUSE_USE_MEMORY=1 ./target/release/statehoused
```

2. From the `examples/agent_research/` directory, run:

```bash
./run.sh
```

This starts an interactive session. At the `> ` prompt you can:

```
> ask What is the capital of France?
[QUESTION] What is the capital of France?
[PLAN] 2 steps planned
[STEP 1] Search for relevant information
[RESULT] Found 2 results for "What is the capital of France?"
[ANSWER] Based on the research, here's what I found:
1. Found 2 results for "What is the capital of France?"
[COMPLETE] Session session-1707311234 finished after 1 steps

> replay
[REPLAY] Replaying session session-1707311234
============================================================
[12:13:54] WRITE
  Key: session:session-1707311234:question
  Question: What is the capital of France?
...
============================================================
[REPLAY] Complete (8 events)

> quit
```

### Direct Question Mode

```bash
./run.sh "What is 123 * 456?"
```

### Environment Variables

- `AGENT_ID` - Agent identifier (default: `agent-research-1`)
- `STATEHOUSE_ADDR` - Daemon address (default: `localhost:50051`)
- `PYTHON` - Python interpreter (default: `python3`)

## Key Features

### Full Auditability

Every action is stored with:
- Timestamp
- Operation type (WRITE, DELETE)
- Complete value

### Deterministic Replay

Replay events in exact chronological order:
- See exactly what the agent thought
- See exactly what tools were called
- See exactly what results came back

### Crash Recovery

If the agent crashes mid-session:
1. Restart the agent
2. It detects the incomplete session
3. Offer to resume from the last step

### Provenance Tracking

Final answers include:
- Original question
- Steps taken
- Tools used
- Sources consulted
- Results obtained

## Data Model

### Keys Structure

```
session:{session_id}                          - Session metadata
session:{session_id}:question                 - Research question
session:{session_id}:plan                     - Research plan
session:{session_id}:step:{number:04d}        - Individual step
session:{session_id}:tool_result:{number:04d} - Tool call result
session:{session_id}:answer                   - Final answer
```

### Example Event Log

```
1. WRITE session:session-1234:question
   value: {"question": "What is the capital of France?"}

2. WRITE session:session-1234:plan
   value: {"steps": [...]}

3. WRITE session:session-1234:step:0001
   value: {"action": "Search for relevant information", "type": "tool"}

4. WRITE session:session-1234:tool_result:0001
   value: {"tool": "search", "result": {...}}

5. WRITE session:session-1234:answer
   value: {"text": "...", "provenance": {...}}

6. WRITE session:session-1234
   value: {"status": "complete"}
```

## Extending the Agent

### Adding New Tools

1. Create a new tool class:

```python
class MyTool(Tool):
    @property
    def name(self) -> str:
        return "my_tool"
    
    @property
    def description(self) -> str:
        return "Description of what this tool does"
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        # Implement tool logic
        return {
            'summary': 'Tool execution summary',
            'source': 'my_tool'
        }
```

2. Register it in `agent.py`:

```python
self.tools.register(MyTool())
```

### Integrating Real LLMs

Replace the mock LLM functions:

1. `_generate_plan()` - Call OpenAI/Anthropic to generate research plan
2. `_synthesize_answer()` - Call LLM to synthesize final answer from results

Example with OpenAI:

```python
async def _generate_plan(self, question: str) -> Dict[str, Any]:
    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a research planner..."},
            {"role": "user", "content": f"Generate a research plan for: {question}"}
        ]
    )
    
    # Parse response into plan format
    return parse_plan(response.choices[0].message.content)
```

## Benefits of Statehouse

1. **No manual state management** - Just write to Statehouse
2. **Automatic versioning** - Every write gets a version number
3. **Built-in replay** - No need to build audit logs
4. **Crash recovery** - State survives crashes
5. **Strong consistency** - No race conditions
6. **Simple API** - Pythonic, no gRPC visible

## Testing

Run the agent with various questions:

```bash
# Test search
./run.sh "Search for information about Rust"

# Test calculator
./run.sh "Calculate 42 * 1337"

# Test multi-step
./run.sh "Search for Python frameworks and calculate 10 + 20"
```

## Production Considerations

For production deployments:

1. **Add authentication** - Secure the gRPC connection
2. **Add rate limiting** - Prevent tool abuse
3. **Add monitoring** - Track agent performance
4. **Use real LLMs** - Replace mock LLM with production provider
5. **Add error recovery** - Handle tool failures gracefully
6. **Add timeouts** - Prevent infinite loops
7. **Add cost tracking** - Monitor LLM API usage

## License

Same as parent project.
