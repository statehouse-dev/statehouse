# Tutorials

Learn Statehouse through hands-on, practical tutorials.

## Philosophy

These tutorials teach by doing. Each tutorial:

- ✅ **Works immediately** - Copy, run, learn
- ✅ **Self-contained** - All code and dependencies included
- ✅ **Well-commented** - Learn why, not just what
- ✅ **Deterministic** - Same input, same output, always

## Getting Started

### Prerequisites

All tutorials require:

- **Python 3.9+**
- **Running Statehouse daemon**
- **Statehouse Python SDK**

### Start the Daemon

Before any tutorial:

```bash
# From repository root
STATEHOUSE_USE_MEMORY=1 cargo run --bin statehouse-daemon
```

Wait for: `🏠 Statehouse daemon listening on 0.0.0.0:50051`

### Install Dependencies

```bash
cd tutorials/XX-tutorial-name
python3 -m venv venv
source venv/bin/activate
pip install -e ../../../python
```

## Available Tutorials

### Tutorial 01: Resumable Research Agent

**Level**: Beginner  
**Time**: 15-20 minutes  
**Repository**: [tutorials/01-resumable-research-agent/](https://github.com/username/statehouse/tree/main/tutorials/01-resumable-research-agent)

Build a research agent that survives crashes and provides full audit trails.

**What you'll learn:**

- Storing agent state in Statehouse
- Resuming after crashes
- Replaying execution history
- Building deterministic tools

**Topics covered:**

- State persistence patterns
- Checkpoint-based recovery
- Transaction management
- Memory abstractions
- Tool registries

[**Start Tutorial →**](./resumable-research-agent)

### More Coming Soon

Additional tutorials in development:

- **Tutorial 02**: Multi-Agent Workflows
- **Tutorial 03**: Long-Running Computations
- **Tutorial 04**: Audit and Compliance

## Tutorial Structure

Each tutorial follows a consistent structure:

```
tutorials/NN-tutorial-name/
├── README.md           # Complete guide
├── agent.py            # Main implementation
├── memory.py           # State management
├── tools.py            # Tool implementations
├── run.sh              # Convenience runner
├── reset.sh            # State cleanup
└── requirements.txt    # Dependencies
```

## Running a Tutorial

General pattern:

```bash
# Navigate to tutorial
cd tutorials/01-resumable-research-agent

# Follow README setup
source venv/bin/activate
pip install -e ../../../python

# Run tutorial
./run.sh --task "Your question here"

# View results
python3 -m statehouse.cli replay <agent-id>
```

## Tutorial Code Style

Tutorial code prioritizes learning:

```python
# ✅ Good - Clear and explicit
def save_step(self, step_num: int, step_data: Dict[str, Any]) -> None:
    """Store results from a research step."""
    key = f"step/{step_num:03d}"
    with self.client.begin_transaction() as tx:
        tx.write(agent_id=self.agent_id, key=key, value=step_data)

# ❌ Avoid - Too clever
save = lambda n, d: self.client.begin_transaction().__enter__().write(
    self.agent_id, f"step/{n:03d}", d
)
```

**Principles:**

1. **Clarity over conciseness**
2. **Explicit over implicit**
3. **Comments explain why**
4. **Type hints for understanding**
5. **No magic or clever tricks**

## Testing Tutorials

Each tutorial is tested for:

- ✅ Setup runs without errors
- ✅ Code produces expected output
- ✅ Deterministic results
- ✅ Clean state management

Run tests:

```bash
cd tutorials/01-resumable-research-agent
./test.sh  # (if provided)
```

## From Tutorial to Production

Tutorials are teaching tools. For production:

1. **Check [examples/](https://github.com/username/statehouse/tree/main/examples)** - Production-ready reference implementations
2. **Read [Architecture Docs](../introduction/design-philosophy)** - Design patterns and best practices
3. **Review [Python SDK](../python-sdk/overview)** - Complete API reference
4. **See [Operations](../operations/configuration)** - Deployment and monitoring

## Common Issues

### Daemon Connection Failed

```
✗ Failed to connect to daemon: failed to connect
```

**Solution**: Start the daemon:

```bash
STATEHOUSE_USE_MEMORY=1 cargo run --bin statehouse-daemon
```

### Module Not Found

```
ModuleNotFoundError: No module named 'statehouse'
```

**Solution**: Install the SDK:

```bash
pip install -e ../../../python
```

### Port Already in Use

```
Error: Address already in use (os error 48)
```

**Solution**: Kill existing daemon or use different port:

```bash
# Find and kill
lsof -ti:50051 | xargs kill -9

# Or use different port
STATEHOUSE_PORT=50052 cargo run --bin statehouse-daemon
```

## Getting Help

- **Tutorial Issues**: Check the tutorial's README troubleshooting section
- **General Questions**: See [FAQ](../faq)
- **Bug Reports**: File an issue on GitHub
- **Discussions**: Join our community discussions

## Next Steps

After completing tutorials:

1. **Explore Examples** - See production patterns
2. **Read Concepts** - Deep dive into design
3. **Build Your Agent** - Apply what you learned
4. **Share Your Work** - Contribute back!

## Contributing Tutorials

Have an idea for a tutorial? We welcome contributions!

See [CONTRIBUTING.md](https://github.com/username/statehouse/blob/main/CONTRIBUTING.md) for guidelines.

**Good tutorial topics:**

- Real-world agent patterns
- Specific use cases
- Integration examples
- Performance optimization
- Testing strategies
