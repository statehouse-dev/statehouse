# Statehouse

**Statehouse** is a strongly consistent state and memory engine designed for AI agents, workflows, and automation systems.

It provides **durable, versioned, replayable state** with clear semantics, so agent-based systems can be debugged, audited, and trusted in production.

Statehouse is **not a cloud service**.
It is a **self-hosted, licensed infrastructure component**, designed to be embedded or run alongside your application.

🌐 https://statehouse.dev

---

## Why Statehouse exists

Modern AI agents and automation systems are fundamentally **stateful**:
- they make decisions
- they remember context
- they evolve over time
- they retry, branch, and recover

Today, this state is usually stored in:
- ad-hoc PostgreSQL tables
- Redis
- JSON blobs
- vector databases used as general storage

These solutions make systems:
- hard to reason about
- impossible to replay
- difficult to debug
- unsafe under concurrency

**Statehouse exists to make agent state boring, correct, and inspectable.**

---

## What Statehouse is (and is not)

### Statehouse **is**
- A strongly consistent state engine
- Transactional and deterministic
- Append-only at its core
- Designed for **replay, audit, and explainability**
- Optimized for agent memory and workflow state
- Built in Rust, with correctness first

### Statehouse **is not**
- A general-purpose SQL database
- A vector database
- A cloud SaaS
- An eventually-consistent cache

---

## Core concepts

### State
State is stored as **versioned records**.
Every change is immutable and timestamped.

You can ask:
- what was the state at time `T`?
- how did we get here?
- what did the agent know when it made this decision?

### Transactions
All writes are transactional.
Either a state transition happened, or it did not.

### Event log
Under the hood, Statehouse is **append-only**.
Snapshots are derived, not authoritative.

This enables:
- replay
- recovery
- auditing
- deterministic debugging

### Replay
Statehouse can replay an agent or workflow’s history step-by-step.

This is essential for:
- debugging agent behavior
- compliance
- reproducibility
- trust

---

## AI / Agent use cases

Statehouse is designed to be used *by agents*, not just humans.

Examples:
- Agent memory (episodic + semantic)
- Workflow orchestration state
- Tool invocation logs
- Decision provenance
- Long-running agent coordination
- Human-in-the-loop checkpoints

Statehouse does **not** embed models.
It provides the **ground truth state layer** agents depend on.

---

## Example (conceptual)

```rust
let tx = statehouse.begin_transaction()?;

tx.write_state(
    agent_id,
    "research_context",
    json!({
        "topic": "distributed systems",
        "sources": ["paper_a", "paper_b"]
    })
)?;

tx.commit()?;
```

Later:

```rust
let snapshot = statehouse.read_state_at(
    agent_id,
    "research_context",
    timestamp
)?;
```

And for debugging:

```rust
statehouse.replay(agent_id)?;
```

---

## Development environment and dependency management

### Devbox (recommended)

This repo includes a [Devbox](https://www.jetify.com/docs/devbox) config so you get **Rust** and **Python (with pip)** without installing them system-wide. Devbox uses Nix to provide pinned toolchains only inside this project.

**Install Devbox:** [jetify.com/docs/devbox/installing-devbox](https://www.jetify.com/docs/devbox/installing-devbox)

From the repo root:

```bash
devbox shell
# You now have: cargo, rustc, python3, pip (from devbox.json)

cd python
pip install -e .
```

Then build the daemon and run the SDK as in [Python Quickstart](#python-quickstart). The first `devbox shell` may take a minute while Nix fetches the toolchains.

### Dependency management

| Layer        | Toolchain / runtime | Dependency definition        | Install / build              |
|-------------|---------------------|-----------------------------|------------------------------|
| **Rust**    | `cargo`, `rustc`    | `Cargo.toml` (workspace + crates) | `cargo build` / `cargo test` |
| **Python**  | `python3`, `pip`    | `python/pyproject.toml`     | `pip install -e python`      |

- **Rust**: Dependencies are declared in the root `Cargo.toml` and in `crates/*/Cargo.toml`. Run `cargo build` and `cargo test` from the repo root. Devbox provides the Rust toolchain; no need to run `rustup` yourself.
- **Python**: Dependencies are in `python/pyproject.toml` (runtime: grpcio, protobuf, click, tabulate; dev: pytest, ruff, mypy). From the repo root, `cd python` then `pip install -e .` installs the `statehouse` package in editable mode with all dependencies. Devbox provides Python 3.11 and pip and creates a virtual environment when you run `devbox shell`.

Without Devbox, install [Rust](https://rustup.rs/) and Python 3.9+ (with pip) yourself, then use the same `Cargo.toml` / `pyproject.toml` and commands above.

---

## Python Quickstart

### Prerequisites

1. **Start the Statehouse daemon** (Rust binary required):

```bash
# Build the daemon (requires Rust toolchain)
cargo build --release

# Run with in-memory storage (for testing)
STATEHOUSE_USE_MEMORY=1 ./target/release/statehoused

# Or run with persistent RocksDB storage (production)
./target/release/statehoused
```

The daemon will start on `localhost:50051` by default. You should see:

```
╔════════════════════════════════════════════════╗
║          🏛️  STATEHOUSE DAEMON 🏛️             ║
║     Strongly consistent state + memory         ║
║            engine for AI agents                ║
╚════════════════════════════════════════════════╝
```

2. **Install the Python SDK**:

```bash
# From the repository root
cd python
pip install -e .

# Or install from PyPI
pip install statehouse
```

### Basic Usage

Runnable examples (including basic usage, transactions, and an agent with replay) are in **`examples/`**. See **`examples/agent_research/README.md`** and run with `./run.sh` from that directory (daemon must be running).

Equivalent code:

```python
from statehouse import Statehouse

# Connect to daemon
client = Statehouse(url="localhost:50051")

# Write state
with client.begin_transaction() as tx:
    tx.write(
        agent_id="my-agent",
        key="memory",
        value={"fact": "Paris is the capital of France"},
    )
# Transaction auto-commits on exit

# Read state
result = client.get_state(agent_id="my-agent", key="memory")
print(result.value)  # {"fact": "Paris is the capital of France"}

# List all keys
keys = client.list_keys(agent_id="my-agent")

# Replay events
for event in client.replay(agent_id="my-agent"):
    print(f"[{event.commit_ts}] Transaction {event.txn_id}")
    for op in event.operations:
        print(f"  {op.key}: {op.value}")
```

### Key Features

**Transactions**: All writes are atomic and isolated

```python
# All operations succeed or fail together
with client.begin_transaction() as tx:
    tx.write(agent_id="agent-1", key="step-1", value={"status": "started"})
    tx.write(agent_id="agent-1", key="step-2", value={"status": "pending"})
    # Both writes committed atomically
```

**Versioning**: Every write creates a new version

```python
# First write
with client.begin_transaction() as tx:
    tx.write(agent_id="agent-1", key="config", value={"mode": "learning"})

# Second write
with client.begin_transaction() as tx:
    tx.write(agent_id="agent-1", key="config", value={"mode": "inference"})

# Get latest version
result = client.get_state(agent_id="agent-1", key="config")
print(result.version)  # 2
```

**Deletes**: Tombstone-based with version tracking

```python
with client.begin_transaction() as tx:
    tx.delete(agent_id="agent-1", key="temp-data")

# Deleted keys don't exist
result = client.get_state(agent_id="agent-1", key="temp-data")
print(result.exists)  # False
```

**Prefix Scanning**: Efficient key prefix queries

```python
# Write multiple related keys
with client.begin_transaction() as tx:
    tx.write(agent_id="agent-1", key="memory:episodic:001", value={...})
    tx.write(agent_id="agent-1", key="memory:episodic:002", value={...})
    tx.write(agent_id="agent-1", key="memory:semantic:001", value={...})

# Scan by prefix
episodes = client.scan_prefix(agent_id="agent-1", prefix="memory:episodic:")
# Returns only keys starting with "memory:episodic:"
```

### Agent Example

A runnable agent example is in **`examples/agent_research/`** (see README and `./run.sh`; daemon must be running).

```python
from statehouse import Statehouse
import time

class ResearchAgent:
    def __init__(self):
        self.client = Statehouse()
        self.agent_id = "agent-research-1"

    def research(self, question: str):
        # Store the question
        with self.client.begin_transaction() as tx:
            tx.write(
                agent_id=self.agent_id,
                key=f"question:{int(time.time())}",
                value={"text": question, "timestamp": time.time()},
            )

        # Do research (stub: replace with real LLM or tool calls)
        answer = self._perform_research(question)

        # Store the answer with provenance
        with self.client.begin_transaction() as tx:
            tx.write(
                agent_id=self.agent_id,
                key=f"answer:{int(time.time())}",
                value={
                    "question": question,
                    "answer": answer,
                    "sources": ["source1", "source2"],
                    "confidence": 0.95,
                },
            )

        return answer

    def _perform_research(self, question: str) -> str:
        """Stub: replace with real LLM or tool calls."""
        if "statehouse" in question.lower():
            return "Statehouse is a strongly consistent state and memory engine for AI agents."
        return f"(stub answer for: {question})"

    def replay_history(self):
        """Replay all research sessions."""
        for event in self.client.replay(agent_id=self.agent_id):
            print(f"Transaction {event.txn_id} at ts={event.commit_ts}")
            for op in event.operations:
                print(f"  {op.key}: {op.value}")

# Usage
agent = ResearchAgent()
answer = agent.research("What is Statehouse?")

# Replay everything the agent did
agent.replay_history()
```

### CLI Tools

Statehouse includes `statehousectl` for command-line operations:

```bash
# Check daemon health
statehousectl health

# List agent keys
statehousectl keys my-agent

# Filter by prefix
statehousectl keys my-agent --prefix memory

# Get specific state value
statehousectl get my-agent memory

# Replay events
statehousectl replay my-agent

# Replay with time range
statehousectl replay my-agent --start-ts 0 --end-ts 10

# Show last N events
statehousectl replay my-agent --limit 10

# Tail recent events
statehousectl tail my-agent

# Dump all agent state to JSON
statehousectl dump my-agent -o /tmp/backup.json
```

### Configuration

The Python SDK can be configured with environment variables:

```bash
# Daemon URL (default: localhost:50051)
export STATEHOUSE_URL=localhost:50051

# Default namespace (default: "default")
export STATEHOUSE_NAMESPACE=production

# Connection timeout in seconds (default: 30)
export STATEHOUSE_TIMEOUT=60
```

Or via code:

```python
client = Statehouse(
    url="localhost:50051",
    namespace="production",
    timeout=60
)
```

### Error Handling

```python
from statehouse import Statehouse, StatehouseError, TransactionError

client = Statehouse()

try:
    with client.begin_transaction() as tx:
        tx.write(agent_id="agent-1", key="data", value={"x": 1})
        # Transaction will auto-commit
except TransactionError as e:
    print(f"Transaction failed: {e}")
except StatehouseError as e:
    print(f"Statehouse error: {e}")
```

### Next Steps

- **Full Example**: See [`examples/agent_research/`](examples/agent_research/) for a complete agent with crash recovery and replay
- **Python SDK Reference**: See [`python/README.md`](python/README.md) for detailed API documentation
- **CLI Reference**: See [`python/docs/CLI.md`](python/docs/CLI.md) for all CLI commands
- **Architecture**: See [`docs/architecture.md`](docs/architecture.md) to understand the design

See [Python SDK docs](python/README.md) and [CLI docs](python/docs/CLI.md) for more details.

---

**License:** Free to use, source-available proprietary. See [LICENSE.md](LICENSE.md).
