# Frequently Asked Questions

## General

### What is Statehouse?

Statehouse is a strongly consistent state and memory engine for AI agents and workflows. It provides durable, versioned, replayable state with clear semantics.

### Who should use Statehouse?

Statehouse is designed for:

- AI agent developers who need reliable state persistence
- Workflow systems that require crash recovery
- Applications that need audit trails and replay capability
- Teams that want debuggable, inspectable agent behavior

### Is Statehouse a database?

Statehouse is a specialized state engine, not a general-purpose database. It focuses on:

- Key-value state per agent
- Transaction atomicity
- Event logging and replay
- Crash recovery

It does not provide SQL, joins, or complex queries.

### Is Statehouse open source?

Statehouse is source-available but not open source. You can use it freely, including in production, but cannot redistribute it. See the [License](license) page for details.

## Architecture

### Why gRPC instead of HTTP/REST?

gRPC provides:

- Efficient streaming for replay
- Strong typing with protobuf
- Built-in backpressure
- Better code generation

See [Why gRPC](grpc-internals/why-grpc) for the full rationale.

### Why Rust for the daemon?

Rust provides:

- Memory safety without garbage collection
- Predictable performance
- Excellent async support with tokio
- Strong ecosystem (RocksDB, tonic)

### Can I use Statehouse without Python?

Yes. While the Python SDK is the primary client, you can:

- Use gRPC directly with generated stubs
- Implement clients in any language with gRPC support
- Use the protobuf definitions to generate code

## Operations

### How do I back up Statehouse?

Stop the daemon and copy the data directory. For online backup, use RocksDB's checkpoint feature. See [Data Directories](operations/data-directories).

### What happens if the daemon crashes?

It recovers automatically on restart. Committed transactions are preserved, uncommitted transactions are lost. See [Process Crash](failure-modes/process-crash).

### How much disk space do I need?

Depends on your workload:

- ~100 bytes per key-value (plus value size)
- ~50 bytes overhead per transaction
- Snapshots add ~1x current state size

For 1 million keys with 1KB values: approximately 1-2 GB.

### Can I run multiple instances?

Yes, with different data directories and ports. Each instance is independent. Statehouse MVP does not support clustering.

## Transactions

### Can I have concurrent transactions?

Yes, but commits are serialized. Multiple clients can have open transactions simultaneously, but commits happen one at a time to maintain consistency.

### What's the transaction timeout?

Default is 30 seconds. Configure with `timeout_ms` when beginning a transaction.

### What happens to uncommitted transactions on crash?

They're lost. This is expected behavior. Only committed transactions are durable.

## Performance

### How many operations per second?

Depends on hardware, but typical ranges:

- Writes: 1,000-10,000 TPS
- Reads: 10,000-100,000 TPS
- Replay: 10,000-100,000 events/second

With fsync enabled, write TPS is lower due to disk sync.

### What's the latency?

Typical latency:

- Read: < 1ms
- Write (in transaction): < 1ms
- Commit (with fsync): 1-10ms
- Commit (without fsync): < 1ms

### How does it scale?

Statehouse is single-node by design (MVP). For higher scale:

- Run multiple instances (sharding by agent)
- Use faster storage (NVMe SSD)
- Tune snapshot intervals

Clustering is a potential future feature.

## Python SDK

### Does the SDK support async?

Yes. The SDK provides both sync and async interfaces. The async client uses `grpc.aio`.

### Is the client thread-safe?

No. Create one client per thread, or use external synchronization.

### How do I handle connection errors?

Catch `statehouse.ConnectionError` and implement retry logic with backoff. See [Error Handling](python-sdk/errors).

## Future Features

### Will there be clustering?

Clustering is a potential future feature but not in the MVP. Current focus is single-node reliability.

### Will there be authentication?

Not in MVP. Authentication and authorization may be added in future versions.

### Will there be encryption at rest?

Not in MVP. Consider filesystem-level encryption for now.

### Will there be a web UI?

Potentially. For now, use the CLI (`statehousectl`) for interactive access.

## Troubleshooting

### The daemon won't start

Check:
- Port 50051 is available
- Data directory is writable
- Sufficient disk space
- No other instance running (lock file)

### Writes are failing

Check:
- Daemon is running (`statehousectl health`)
- Network connectivity
- Transaction not timed out
- Disk not full

### Replay is slow

Check:
- Network bandwidth
- Number of events (large logs take time)
- Consider time range filtering

See the [Troubleshooting Guide](operations/logging-and-metrics) for more details.
