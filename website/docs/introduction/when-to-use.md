# When to Use Statehouse

Statehouse is designed for specific use cases. Here's when it makes sense.

## Ideal Use Cases

### AI Agent Memory

Statehouse excels at storing agent memory:
- Episodic memory (what happened when)
- Semantic memory (facts and knowledge)
- Context across multiple tool invocations
- Decision history with full provenance

### Workflow Orchestration

For long-running workflows that need:
- Strong consistency guarantees
- Crash recovery
- Audit trails
- State inspection and debugging

### Audit and Compliance

When you need:
- Complete event history
- Deterministic replay
- Immutable audit logs
- Provenance tracking

### Debugging Agent Behavior

Statehouse's replay capability makes it ideal for:
- Understanding why an agent made a decision
- Reproducing agent behavior
- Inspecting state at any point in time
- Debugging complex multi-step workflows

### Single-Node Deployment

Statehouse is perfect when:
- You need strong consistency
- You can run a single daemon instance
- You don't need horizontal scaling (yet)
- You want simplicity over distributed complexity

## Characteristics of Good Statehouse Users

- You need strong consistency, not eventual consistency
- You value correctness and auditability over raw performance
- You're building agent-based systems or workflows
- You need to debug and understand system behavior
- You're comfortable with self-hosted infrastructure

## Next Steps

- [When Not to Use Statehouse](when-not-to-use) - Learn about alternatives
- [Getting Started](getting-started/installation) - Install and run Statehouse
