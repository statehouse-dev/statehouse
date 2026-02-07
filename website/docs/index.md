# Statehouse Documentation

Welcome to the Statehouse documentation.

Statehouse is a strongly consistent state and memory engine designed for AI agents, workflows, and automation systems. It provides durable, versioned, replayable state with clear semantics.

## Quick Links

- [What is Statehouse?](introduction/what-is-statehouse) - Overview and core concepts
- [Getting Started](getting-started/installation) - Installation and first steps
- [Python SDK](python-sdk/overview) - Python client library documentation
- [Examples](examples/reference-agent) - Real-world usage examples

## Documentation Structure

### Introduction
Learn about Statehouse's purpose, design philosophy, and when to use it (or not).

### Concepts
Deep dive into core concepts: state and events, transactions, versions, replay, and determinism.

### Getting Started
Step-by-step guides to install Statehouse, run the daemon, and perform your first operations.

### Python SDK
Complete reference for the Python client library, including transactions, reads, replay, and error handling.

### gRPC Internals
For advanced users: understand the gRPC protocol, API versioning, and streaming replay.

### Operations
Production guidance: configuration, data directories, snapshots, recovery, and observability.

### Failure Modes
What happens when things go wrong: process crashes, disk full, partial writes, and transaction timeouts.

### Examples
Real-world examples including the reference agent, crash recovery, and audit workflows.

---

**Status**: This documentation covers the MVP release. Some features may be marked as "Draft / MVP" where appropriate.
