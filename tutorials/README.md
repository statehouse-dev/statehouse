# Statehouse Tutorials

This directory contains hands-on tutorials for learning Statehouse.

## Tutorial Philosophy

These tutorials are designed to be:

1. **Copy-paste ready**: You should be able to follow each tutorial by copying and pasting commands directly into your terminal
2. **Self-contained**: Each tutorial includes all dependencies and setup instructions
3. **Minimal but complete**: Tutorials focus on core concepts without unnecessary complexity
4. **Realistic**: Examples reflect real-world agent patterns and workflows
5. **Testable**: All tutorial code can be run and verified automatically

## Tutorial Structure

Each tutorial follows a standard structure:

```
tutorials/
  NN-tutorial-name/
    README.md          # Complete walkthrough with instructions
    requirements.txt   # Python dependencies (or pyproject.toml)
    *.py              # Tutorial source code
    run.sh            # Convenience script to run the tutorial
    reset.sh          # Script to clear state and start fresh
```

## Naming Convention

Tutorials are numbered sequentially with descriptive names:

- `01-tutorial-name` - Beginner: foundational concepts
- `02-tutorial-name` - Intermediate: building on basics
- `03-tutorial-name` - Advanced: complex patterns

The numbering establishes a recommended learning path, but tutorials can be completed independently.

## Shared Utilities

The `_shared/` directory contains common helper code used across multiple tutorials. This includes:

- Mock LLM providers
- Logging utilities  
- Testing helpers
- Common configuration

## Prerequisites

Before starting any tutorial:

1. **Install Statehouse daemon**:
   ```bash
   # Build from source (requires Rust)
   cargo build --release
   
   # Or download pre-built binary
   # See main README for platform-specific instructions
   ```

2. **Start the daemon**:
   ```bash
   # In-memory mode (no persistence, good for tutorials)
   STATEHOUSE_USE_MEMORY=1 ./target/release/statehoused
   
   # Or persistent mode
   ./target/release/statehoused
   ```

3. **Install Python SDK**:
   ```bash
   cd python
   pip install -e .
   ```

4. **Verify installation**:
   ```bash
   statehousectl health
   ```

## Running Tutorials

Each tutorial includes detailed instructions in its README.md. The general pattern is:

```bash
cd tutorials/NN-tutorial-name
./run.sh
```

Most tutorials support multiple modes:
- **Normal mode**: Run the tutorial from start to finish
- **Mock mode**: Use mock LLM providers (no API keys required)
- **Reset mode**: Clear state and start over

## Tutorial Overview

### 01-resumable-research-agent

**Level**: Beginner  
**Duration**: 15 minutes  
**Prerequisites**: None

Learn the core Statehouse pattern: building a resumable agent that survives crashes.

**Topics covered**:
- Persisting agent state
- Transaction-based updates
- Crash recovery and resume
- Replay for auditability
- Tool call tracking

**What you'll build**: A research agent that can be interrupted mid-task and resume seamlessly.

---

## Tutorial Development Guidelines

When creating new tutorials:

1. **Start with a clear goal**: What will the user learn? What will they build?
2. **Make it runnable offline**: Use mock providers, no required API keys
3. **Include error cases**: Show what happens when things fail
4. **Test thoroughly**: Run the tutorial yourself multiple times
5. **Document prerequisites**: Be explicit about what's needed
6. **Provide reset scripts**: Users should be able to start fresh easily
7. **Use clear variable names**: Prioritize readability over brevity
8. **Add comments**: Explain non-obvious code
9. **Show expected output**: Include terminal output snippets
10. **Keep it focused**: One concept per tutorial

## Testing Tutorials

All tutorials should be testable in CI:

```bash
# Run tutorial in mock/test mode
cd tutorials/NN-tutorial-name
./run.sh --test

# Verify output
./verify.sh
```

## Style Guidelines

Tutorial code should follow Python best practices:

- Use type hints for function signatures
- Use dataclasses for data structures  
- Explicit control flow (avoid "clever" code)
- Descriptive variable names
- Comments for non-obvious logic
- Run `ruff format` and `ruff check`

See `docs/dev/python-style.md` for details.

## Getting Help

If you encounter issues with a tutorial:

1. Check the tutorial's README for troubleshooting tips
2. Verify daemon is running: `statehousectl health`
3. Check daemon logs for errors
4. Reset and try again: `./reset.sh`
5. Open an issue on GitHub with:
   - Tutorial name
   - Steps to reproduce
   - Error output
   - Environment (OS, Python version)

## Contributing Tutorials

We welcome tutorial contributions! See `CONTRIBUTING.md` for guidelines.

When proposing a new tutorial:

1. Open an issue describing the tutorial concept
2. Get feedback on scope and approach
3. Follow the tutorial structure above
4. Test thoroughly in both mock and live modes
5. Include expected output snippets
6. Submit a pull request

## See Also

- [Main Documentation](../docs/)
- [Python SDK Documentation](../python/README.md)
- [Example Agents](../examples/)
- [CLI Reference](../python/statehouse/cli/README.md)
