# Design Philosophy

Statehouse is built on clear principles that guide its design and development.

## Core Principles

### Correctness First

Statehouse prioritizes correctness over performance. Strong consistency, deterministic replay, and clear semantics are non-negotiable.

### Simplicity Over Features

The MVP is intentionally narrow. Better to do a few things well than many things poorly.

### Explicit Over Implicit

No magic, no hidden behavior. State transitions are explicit, errors are clear, and semantics are documented.

### Language-Agnostic Protocol

gRPC and Protobuf ensure Statehouse can be used from any language. The protocol is the source of truth.

### Client Libraries Hide Complexity

Users should never see gRPC or protobuf types. Client libraries provide clean, ergonomic APIs.

## Architectural Decisions

### Single-Writer Core

The state machine has a single logical writer. This ensures:
- Strong consistency without distributed consensus
- Deterministic ordering
- Simpler correctness proofs

### Append-Only Foundation

The event log is the source of truth. Snapshots are derived, not authoritative. This enables:
- Complete audit trails
- Deterministic replay
- Crash recovery

### gRPC-First

All communication is via gRPC:
- Language-agnostic
- Streaming support for replay
- Strong typing via Protobuf
- No REST, no HTTP (except health checks)

### Storage Abstraction

Statehouse uses RocksDB for persistence but abstracts storage behind a trait. This enables:
- Testing with in-memory storage
- Future storage backends
- Clear separation of concerns

## Tradeoffs

### Chosen

- **Strong consistency** over eventual consistency
- **Correctness** over raw performance
- **Simplicity** over feature completeness
- **Self-hosted** over managed service
- **Single-node** over distributed (for MVP)

### Deferred (Post-MVP)

- Clustering and replication
- Authentication and authorization
- Encryption at rest
- SQL/query layer
- Vector search

These tradeoffs are documented explicitly. Statehouse is honest about what it is and what it is not.

## Non-Goals

Statehouse explicitly does not aim to be:
- A general-purpose database
- A vector database
- A cloud SaaS
- A high-throughput OLTP system
- A distributed consensus system (in MVP)

## Evolution

Statehouse will evolve based on:
- Real-world usage patterns
- User feedback
- Correctness requirements
- Simplicity constraints

New features must align with core principles. Complexity is added only when necessary.

## Next Steps

- [What is Statehouse?](what-is-statehouse) - Overview
- [Getting Started](getting-started/installation) - Start using Statehouse
