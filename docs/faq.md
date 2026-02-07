# Statehouse FAQ

Frequently asked questions about Statehouse.

## General

### What is Statehouse?

Statehouse is a strongly consistent state and memory engine for AI agents. It provides durable, versioned, replayable state with transactional guarantees.

Think of it as a specialized database designed for agent workflows - not for general application data.

### Why not just use PostgreSQL / Redis / MongoDB?

You can, but:

1. **No replay** - These databases don't keep deterministic event logs
2. **No versioning** - Hard to ask "what was the state at time T?"
3. **Complex schemas** - Need to design tables/collections yourself
4. **Agent-unfriendly** - Not designed for agent state patterns

Statehouse is **purpose-built for agents** with these features built-in.

### Is Statehouse open source?

No. Statehouse is a **licensed, commercial product**.

It's designed to be self-hosted by organizations building AI agent systems.

### Can I use Statehouse in production?

The MVP is functional and tested, but:
- **No clustering yet** - single daemon instance
- **No built-in auth** - needs network-level security
- **No managed service** - you run the infrastructure

For production use:
1. Test thoroughly with your workload
2. Implement security (TLS, network isolation)
3. Set up monitoring and backups
4. Have a support agreement

### What's the performance like?

Local daemon (single instance):
- Reads: 10,000+ ops/sec
- Writes: 2,000-5,000 ops/sec (with fsync)
- Latency: 1-5ms per operation

Bottleneck is usually storage fsync. Use batching for high throughput.

## Architecture

### How does Statehouse work internally?

```
Client (Python) 
    │
    ▼
gRPC (wire protocol)
    │
    ▼
Rust Daemon (statehoused)
    │
    ├─ State Machine (single-writer)
    │     │
    │     ├─ Transaction staging
    │     ├─ Version control
    │     └─ Event log management
    │
    └─ Storage (RocksDB or InMemory)
          │
          ├─ State records
          ├─ Version counters
          └─ Event log
```

See [gRPC Architecture](grpc_architecture.md) for details.

### Why gRPC?

- **Strongly typed** - protocol buffers define exact API
- **Language agnostic** - easy to add new clients
- **Efficient** - binary protocol with HTTP/2
- **Streaming** - native support for replay
- **Tooling** - excellent debugging tools

### Why Rust for the daemon?

- **Correctness** - type system catches bugs at compile time
- **Performance** - zero-cost abstractions
- **Reliability** - no garbage collector pauses
- **Safety** - memory safety without runtime overhead

Agents need a **rock-solid** foundation. Rust delivers.

### What's the concurrency model?

**Server-side:**
- Single-writer state machine (all mutations serialize)
- Concurrent reads (immutable data)
- No distributed locks needed

**Client-side:**
- Multiple clients can connect
- Transactions are isolated
- Commit order determines replay order

This design is **simple and correct** - no race conditions.

## Usage

### How do I start the daemon?

```bash
# Build from source
cargo build --release --bin statehoused

# Run
./target/release/statehoused
```

Or for development:
```bash
STATEHOUSE_USE_MEMORY=1 ./target/release/statehoused
```

### How do I connect from Python?

```python
from statehouse import Statehouse

client = Statehouse(url="localhost:50051")
```

### Do I need to define a schema?

No! Statehouse is schema-free:
- Keys are strings
- Values are JSON (stored as dicts)
- No migrations needed

Just write data:
```python
tx.write(agent_id="a1", key="memory", value={"fact": "Paris is in France"})
```

### Can I use TypeScript / Go / Java?

The Python SDK is complete. Other languages need:
1. Generate client from `.proto` file
2. Wrap in a clean API (hide gRPC details)

The protocol is language-agnostic, so adding clients is straightforward.

### How do I handle large values?

Current limit: **1MB per value** (configurable).

For larger data:
1. Store references (URLs, S3 keys) in Statehouse
2. Store actual data in object storage (S3, etc.)
3. Link via Statehouse metadata

Example:
```python
tx.write(
    agent_id="a1",
    key="document:123",
    value={
        "title": "Large Document",
        "s3_key": "s3://bucket/doc123.pdf",
        "size_bytes": 50_000_000,
        "checksum": "sha256:abc123..."
    }
)
```

## Transactions

### What's a transaction?

A transaction groups multiple writes/deletes into an atomic unit:

```python
with client.begin_transaction() as tx:
    tx.write(agent_id="a1", key="k1", value={"x": 1})
    tx.write(agent_id="a1", key="k2", value={"y": 2})
# Auto-commits on exit (or aborts on exception)
```

Either **all** operations succeed or **none** do.

### Can transactions span multiple agents?

Yes! Transactions can write to different agents:

```python
with client.begin_transaction() as tx:
    tx.write(agent_id="agent-1", key="k", value={"x": 1})
    tx.write(agent_id="agent-2", key="k", value={"y": 2})
# Both writes commit atomically
```

### What's the transaction timeout?

Default: **30 seconds**.

If a transaction takes longer, it's automatically aborted.

### Can I have long-running transactions?

Not recommended. Transactions should be:
- Short (< 1 second ideal)
- Focused (group related writes)
- Non-blocking (no I/O during transaction)

For long-running operations:
1. Do work outside transaction
2. Write results atomically

### What happens if a transaction fails?

If `commit()` fails:
- All operations are discarded
- No state is changed
- An exception is raised

```python
try:
    with client.begin_transaction() as tx:
        tx.write(agent_id="a1", key="k", value={"x": 1})
except TransactionError:
    # Handle failure (retry, log, etc.)
```

## State and Replay

### How do I read state?

```python
result = client.get_state(agent_id="a1", key="memory")
if result:
    print(result.value)  # {"fact": "..."}
```

### Can I read historical state?

Yes! Use versioned reads:

```python
# Get state at specific version
result = client.get_state_at_version(
    agent_id="a1",
    key="memory",
    version=5
)
```

Or replay to reconstruct state at any point.

### What is replay?

Replay returns the complete history of state changes:

```python
for event in client.replay(agent_id="a1"):
    print(f"[{event.timestamp}] {event.operations}")
```

See [Replay Semantics](replay_semantics.md) for details.

### Why is replay important?

Replay enables:
- **Debugging** - see exactly what the agent did
- **Auditing** - compliance and accountability  
- **Provenance** - trace decisions to their sources
- **Testing** - verify deterministic behavior

Agents are **complex and non-deterministic** by nature. Replay makes them inspectable.

### Does replay include aborted transactions?

No. Only **committed** transactions appear in replay.

### Can I filter replay?

Yes:
```python
# By time range
for event in client.replay(
    agent_id="a1",
    from_timestamp="2026-02-07T10:00:00Z",
    to_timestamp="2026-02-07T11:00:00Z"
):
    print(event)

# By namespace
for event in client.replay(
    agent_id="a1",
    namespace="production"
):
    print(event)
```

## Data Model

### What's an agent_id?

An **agent_id** is a string identifying an agent or workflow:

```python
agent_id = "research-agent-42"
```

All state for this agent is isolated. Different agents don't see each other's state.

### What's a key?

A **key** is a string identifying a piece of state:

```python
key = "current_task"
key = "memory:facts"
key = "session:2026-02-07:question"
```

Keys are hierarchical by convention (using `:` or `/`).

### What's a namespace?

A **namespace** isolates state environments:

```python
namespace = "production"
namespace = "staging"
namespace = "dev"
```

Same agent in different namespaces has separate state.

### What's a version?

A **version** is a monotonically increasing counter per key:

```python
# First write
tx.write(agent_id="a1", key="k", value={"x": 1})
# k is now version 1

# Update
tx.write(agent_id="a1", key="k", value={"x": 2})
# k is now version 2
```

Versions enable time-travel reads.

## Operations

### Can I update a key?

Yes - just write to the same key again:

```python
# Initial write
tx.write(agent_id="a1", key="config", value={"mode": "fast"})

# Update
tx.write(agent_id="a1", key="config", value={"mode": "slow"})
```

The new value **replaces** the old (not merged).

### Can I delete a key?

Yes:

```python
tx.delete(agent_id="a1", key="temp_data")
```

Delete operations:
- Remove the key from current state
- Appear in replay as DELETE events
- Increment version number

### Can I list all keys for an agent?

Yes:

```python
keys = client.list_keys(agent_id="a1")
print(keys)  # ['config', 'state', 'memory', ...]
```

### Can I scan keys by prefix?

Yes:

```python
keys = client.scan_prefix(
    agent_id="a1",
    prefix="session:2026-02-07:"
)
```

This is efficient for hierarchical keys.

## Performance

### How do I optimize writes?

1. **Batch in transactions:**
   ```python
   with client.begin_transaction() as tx:
       for item in items:
           tx.write(agent_id="a1", key=item.key, value=item.value)
   # One commit for all writes
   ```

2. **Use in-memory storage for development:**
   ```bash
   STATEHOUSE_USE_MEMORY=1 ./statehoused
   ```

3. **Tune RocksDB** (advanced):
   - Adjust fsync behavior
   - Configure compaction
   - Use SSDs

### How do I optimize reads?

Reads are already fast (1-2ms). To go faster:

1. **Cache** - keep frequently-read values in memory
2. **Batch** - read multiple keys if needed
3. **Avoid** - don't read if you already have the value

### Why is my daemon slow?

Common causes:
1. **Storage fsync** - dominates write latency (expected)
2. **Large values** - avoid MB-sized values
3. **Many small transactions** - batch instead
4. **Network latency** - run daemon locally
5. **Debug logging** - set `RUST_LOG=info` not `debug`

### Can I run multiple daemons?

Not yet in MVP. Future features:
- **Replication** - read replicas
- **Sharding** - partition by agent_id
- **Clustering** - high availability

## Security

### Is Statehouse secure?

MVP has **no built-in authentication or encryption**.

For production:
1. **Network isolation** - run in private network
2. **TLS** - encrypt gRPC channel
3. **Firewall** - restrict port 50051
4. **VPN/SSH tunnel** - remote access

### How do I add authentication?

Use gRPC metadata for API keys:

```python
# Client
metadata = [("authorization", "Bearer YOUR_TOKEN")]
client = Statehouse(url="...", metadata=metadata)

# Server (custom)
# Verify token in gRPC interceptor
```

Or use mTLS client certificates.

### How do I encrypt data at rest?

Two options:
1. **Application-level** - encrypt values before writing
2. **Storage-level** - use encrypted filesystem (LUKS, etc.)

Statehouse doesn't have built-in encryption yet.

## Operations

### How do I backup Statehouse?

1. **RocksDB backup:**
   ```bash
   cp -r data/rocksdb/ backup/
   ```

2. **Dump state:**
   ```bash
   statehousectl dump <agent_id> -o backup.json
   ```

3. **Replay log:**
   Store event log separately for point-in-time recovery

### How do I monitor Statehouse?

Current tools:
- **Logs** - `RUST_LOG=info` for structured logs
- **CLI** - `statehousectl health` for basic status
- **gRPC tools** - `grpcurl`, `grpcui` for debugging

Future: Prometheus metrics

### How do I upgrade Statehouse?

1. Stop daemon
2. Backup data directory
3. Install new version
4. Start daemon

Storage format migrations are automatic (with version checks).

### What happens if the daemon crashes?

**Data durability:**
- Committed transactions are durable (with fsync)
- In-progress transactions are lost
- State is recovered on restart

**Client behavior:**
- Connection lost → ConnectionError
- Retry transaction on reconnection

## Troubleshooting

### "Connection refused" error

Daemon not running. Start it:
```bash
./target/release/statehoused
```

### "Transaction expired" error

Transaction took too long (> 30s). Fix:
1. Make transaction faster
2. Do work outside transaction
3. Write results atomically

### "Key not found" error

Key doesn't exist or was deleted. Check:
```python
result = client.get_state(agent_id="a1", key="k")
if result is None:
    # Key doesn't exist
```

### Daemon won't start

Check logs:
```bash
RUST_LOG=debug ./statehoused
```

Common issues:
- Port 50051 already in use
- Data directory not writable
- RocksDB corruption (rare)

### Tests failing

Ensure daemon is running:
```bash
# Terminal 1
STATEHOUSE_USE_MEMORY=1 ./target/release/statehoused

# Terminal 2
cd python && pytest
```

See [Troubleshooting Guide](troubleshooting.md) for more.

## Contributing

### Can I contribute to Statehouse?

Statehouse is a commercial product, not open source.

However, we welcome:
- Bug reports
- Feature requests
- Documentation improvements
- Client libraries for other languages (with license)

### How do I report a bug?

Contact your support channel or email support@statehouse.dev.

Include:
- Statehouse version
- Error message / logs
- Steps to reproduce
- Python SDK version (if applicable)

### How do I request a feature?

Same channels as bugs. We prioritize features based on:
- Customer demand
- Technical feasibility  
- Roadmap fit

## Roadmap

### What's planned for future releases?

- **Clustering** - HA and read replicas
- **Sharding** - horizontal scaling
- **Authentication** - built-in API keys
- **Metrics** - Prometheus exporter
- **SQL queries** - structured querying (maybe)
- **Vector indexes** - embedding search (maybe)

### When will X be released?

We don't publish timelines publicly. Contact sales for roadmap details.

### Can I influence the roadmap?

Yes! Customers with support contracts can:
- Vote on features
- Request priority features
- Propose custom development

## Getting Help

### Where can I get support?

- **Documentation** - Start here (you are here!)
- **Email** - support@statehouse.dev  
- **Slack** - Customer Slack channel (for licensed users)
- **GitHub Issues** - For SDK bugs only

### Is there a community?

Statehouse has a **customer community** for licensed users.

Not open source = no public Discord/forum.

### How do I learn more?

Read the docs:
- [Architecture](architecture.md)
- [gRPC Architecture](grpc_architecture.md)
- [Replay Semantics](replay_semantics.md)
- [API Contract](api_contract.md)
- [Python SDK](../python/README.md)
- [Example Agent](../examples/agent_research/)

Try the examples:
```bash
cd examples/agent_research
./run.sh
```

Experiment with the CLI:
```bash
statehousectl health
statehousectl keys my-agent
statehousectl replay my-agent
```

## License

### What's the license?

Statehouse is **commercial software** with a proprietary license.

Contact sales@statehouse.dev for licensing terms.

### Can I use it for free?

Development and testing: **yes** (subject to license terms).

Production use: **requires a paid license**.

### What about the Python SDK?

Python SDK follows the same license as the daemon.

You cannot use either without a license agreement.
