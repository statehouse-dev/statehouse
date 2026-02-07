# What is Statehouse?

Statehouse is a strongly consistent state and memory engine designed for AI agents, workflows, and automation systems.

## Core Purpose

Statehouse provides **durable, versioned, replayable state** with clear semantics, so agent-based systems can be debugged, audited, and trusted in production.

## What Statehouse Is

- A strongly consistent state engine
- Transactional and deterministic
- Append-only at its core
- Designed for replay, audit, and explainability
- Optimized for agent memory and workflow state
- Built in Rust, with correctness first

## What Statehouse Is Not

- A general-purpose SQL database
- A vector database
- A cloud SaaS
- An eventually-consistent cache

## Key Features

### Strong Consistency

All writes are transactional. Either a state transition happened, or it did not. There are no partial transactions visible to readers.

### Versioning

Every write creates a new version. You can ask:
- What was the state at time `T`?
- How did we get here?
- What did the agent know when it made this decision?

### Event Log

Under the hood, Statehouse is append-only. Snapshots are derived, not authoritative. This enables replay, recovery, auditing, and deterministic debugging.

### Replay

Statehouse can replay an agent or workflow's history step-by-step. This is essential for debugging agent behavior, compliance, reproducibility, and trust.

## Architecture

Statehouse consists of:

1. **Rust daemon** (`statehoused`): The core state engine, exposed via gRPC
2. **Python SDK**: A clean, ergonomic client library that hides gRPC complexity
3. **CLI tools**: Command-line utilities for inspection and debugging

The daemon runs locally (or on your infrastructure) and provides a strongly consistent state layer that agents depend on.

## Use Cases

Statehouse is designed to be used by agents, not just humans:

- Agent memory (episodic + semantic)
- Workflow orchestration state
- Tool invocation logs
- Decision provenance
- Long-running agent coordination
- Human-in-the-loop checkpoints

Statehouse does not embed models. It provides the ground truth state layer agents depend on.

## Next Steps

- [When to Use Statehouse](when-to-use) - Understand when Statehouse is the right choice
- [When Not to Use Statehouse](when-not-to-use) - Learn about alternatives
- [Design Philosophy](design-philosophy) - Understand the principles behind Statehouse
