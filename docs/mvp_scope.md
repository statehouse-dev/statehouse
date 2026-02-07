# Statehouse MVP Scope

> Clear boundaries for the MVP release

---

## What IS in the MVP

### Core Features

✅ **Single-node deployment**
- Local, self-hosted daemon
- No clustering, no distributed consensus
- Strong consistency via single-writer design

✅ **Transactional state**
- Begin/Write/Delete/Commit/Abort
- Atomic transaction commits
- Read-after-write consistency

✅ **Versioned state**
- Every write creates a new version
- Read at specific version
- Monotonic version counters per key

✅ **Append-only event log**
- Immutable audit trail
- Deterministic replay
- Recovery from log

✅ **Replay**
- Stream events for an agent
- Reconstruct state history
- Debug and audit agent behavior

✅ **gRPC API**
- Language-agnostic protocol
- Protobuf-defined contract
- Streaming support for replay

✅ **Python SDK**
- Clean, ergonomic API
- No gRPC visible to users
- Async and sync support

✅ **RocksDB storage**
- Persistent state
- Snapshotting
- Crash recovery

✅ **Basic observability**
- Structured logging
- Transaction lifecycle logs
- Health check endpoint

---

## What is NOT in the MVP

### Explicitly Deferred

❌ **Clustering**
- No multi-node support
- No Raft or consensus protocols
- No replication

❌ **Sharding**
- Single storage backend
- No horizontal partitioning

❌ **Authentication/Authorization**
- No user accounts
- No permissions
- No ACLs
- Trust-based (local deployment only)

❌ **Encryption**
- No encryption at rest
- No TLS (optional, not required)
- No key management

❌ **SQL/Query Layer**
- No SQL interface
- No complex queries
- K/V access only

❌ **Vector Search**
- No embeddings
- No similarity search
- Use a dedicated vector DB if needed

❌ **Advanced Indexing**
- No secondary indexes
- Prefix scans only

❌ **Multi-tenancy**
- Single-user deployment
- Namespace is a soft isolation boundary only

❌ **Cloud/SaaS**
- No hosted service
- Self-hosted only

---

## Success Criteria for MVP

The MVP is complete when:

1. ✅ Rust daemon (`statehoused`) runs locally
2. ✅ Python SDK can:
   - Begin/commit transactions
   - Write/read/delete state
   - Replay events
3. ✅ Reference agent example works end-to-end
4. ✅ All integration tests pass
5. ✅ Documentation is complete and accurate
6. ✅ Build/packaging works (local install)

---

## Post-MVP Roadmap (Conceptual)

Future releases may include:
- Clustering and replication
- Authentication and authorization
- Encryption at rest
- Advanced query capabilities
- Go, TypeScript, Rust client libraries
- Performance optimizations
- Cloud-ready deployment patterns

These are **not commitments** — just illustrative of possible directions.

---

## Why This Scope?

The MVP is intentionally narrow to:
1. **Validate core value proposition**: Does this solve agent state problems?
2. **Prove correctness**: Get the semantics right before scaling
3. **Establish foundation**: Build on solid primitives
4. **Ship quickly**: Avoid scope creep

Statehouse's strength is **correctness and simplicity**, not feature count.

---

**Status**: This scope is locked for MVP. Feature requests should target post-MVP milestones.
