# Troubleshooting Guide

Common problems and solutions when using Statehouse.

## Connection Issues

### Cannot connect to daemon

**Symptom:**
```python
ConnectionError: Failed to connect to localhost:50051
```

**Diagnosis:**
```bash
# Check if daemon is running
pgrep -fl statehoused

# Try connecting with grpcurl
grpcurl -plaintext localhost:50051 list
```

**Solutions:**

1. **Start the daemon:**
   ```bash
   ./target/release/statehoused
   ```

2. **Check the port:**
   ```bash
   # Daemon listening?
   lsof -i :50051
   
   # Port in use by something else?
   ```

3. **Check the address:**
   ```python
   # Make sure URL matches daemon
   client = Statehouse(url="localhost:50051")  # Default
   
   # If daemon runs elsewhere:
   client = Statehouse(url="192.168.1.100:50051")
   ```

4. **Check firewall:**
   ```bash
   # macOS
   sudo pfctl -s rules | grep 50051
   
   # Linux
   sudo iptables -L | grep 50051
   ```

### Connection drops during operation

**Symptom:**
```python
grpc.RpcError: Connection lost
```

**Causes:**
- Daemon crashed
- Network interruption
- Daemon restart

**Solutions:**

1. **Check daemon logs:**
   ```bash
   RUST_LOG=debug ./statehoused 2>&1 | tee daemon.log
   ```

2. **Add retry logic:**
   ```python
   from statehouse.exceptions import ConnectionError
   
   def with_retry(fn, retries=3):
       for i in range(retries):
           try:
               return fn()
           except ConnectionError:
               if i == retries - 1:
                   raise
               time.sleep(1)
   ```

3. **Use connection pooling:**
   ```python
   # Reuse client instance
   client = Statehouse()
   
   # Don't create new client for each operation
   # BAD: client = Statehouse() for every call
   ```

## Transaction Issues

### Transaction expired

**Symptom:**
```python
TransactionError: Transaction expired
```

**Cause:**
Transaction took longer than 30 seconds (default timeout).

**Solutions:**

1. **Speed up the transaction:**
   ```python
   # BAD: doing work inside transaction
   with client.begin_transaction() as tx:
       result = slow_computation()  # Takes 40 seconds
       tx.write(agent_id="a1", key="k", value=result)
   
   # GOOD: do work outside
   result = slow_computation()  # Do work first
   with client.begin_transaction() as tx:
       tx.write(agent_id="a1", key="k", value=result)  # Fast
   ```

2. **Reduce transaction scope:**
   ```python
   # BAD: huge batch
   with client.begin_transaction() as tx:
       for i in range(10000):  # Too many
           tx.write(agent_id="a1", key=f"k{i}", value={...})
   
   # GOOD: reasonable batch
   for batch in chunks(items, 100):
       with client.begin_transaction() as tx:
           for item in batch:
               tx.write(agent_id="a1", key=item.key, value=item.value)
   ```

3. **Increase timeout (daemon restart required):**
   Currently not configurable via client. Fixed at 30s in daemon.

### Cannot commit transaction twice

**Symptom:**
```python
TransactionError: Transaction already committed
```

**Cause:**
Trying to commit a transaction multiple times.

**Solution:**
```python
# BAD
tx = client.begin_transaction()
tx.write(agent_id="a1", key="k", value={"x": 1})
tx.commit()
tx.commit()  # ERROR!

# GOOD: use context manager
with client.begin_transaction() as tx:
    tx.write(agent_id="a1", key="k", value={"x": 1})
# Auto-commits exactly once
```

### Transaction not found

**Symptom:**
```python
StatehouseError: Transaction not found
```

**Causes:**
- Transaction ID is wrong
- Transaction already committed/aborted
- Transaction timed out (auto-aborted)

**Solution:**
```python
# Always use fresh transactions
tx = client.begin_transaction()
try:
    tx.write(agent_id="a1", key="k", value={"x": 1})
    tx.commit()
except Exception as e:
    tx.abort()  # Clean up
    raise
```

## State Issues

### Key not found

**Symptom:**
```python
result = client.get_state(agent_id="a1", key="k")
# result is None
```

**Diagnosis:**
```python
# List all keys for agent
keys = client.list_keys(agent_id="a1")
print(keys)

# Check replay for deleted keys
for event in client.replay(agent_id="a1"):
    for op in event.operations:
        if op.key == "k":
            print(f"{event.timestamp}: {op.type.name}")
```

**Causes:**
1. Key was never written
2. Key was deleted
3. Wrong agent_id or namespace
4. Typo in key name

**Solution:**
```python
# Always check if key exists
result = client.get_state(agent_id="a1", key="k")
if result is None:
    # Handle missing key
    default_value = {"x": 0}
    with client.begin_transaction() as tx:
        tx.write(agent_id="a1", key="k", value=default_value)
```

### State not updating

**Symptom:**
```python
# Write
with client.begin_transaction() as tx:
    tx.write(agent_id="a1", key="k", value={"x": 2})

# Read
result = client.get_state(agent_id="a1", key="k")
print(result.value)  # Still {"x": 1} ???
```

**Diagnosis:**
```python
# Check commit succeeded
try:
    with client.begin_transaction() as tx:
        tx.write(agent_id="a1", key="k", value={"x": 2})
    print("Commit succeeded")
except Exception as e:
    print(f"Commit failed: {e}")

# Check replay
for event in client.replay(agent_id="a1"):
    print(event)
```

**Causes:**
1. Transaction failed (exception swallowed)
2. Wrong namespace
3. Reading from different client/connection
4. Caching issue (unlikely)

**Solution:**
```python
# Verify commit
with client.begin_transaction() as tx:
    tx.write(agent_id="a1", key="k", value={"x": 2})
print("Write committed")

# Verify read
result = client.get_state(agent_id="a1", key="k")
assert result.value == {"x": 2}, f"Got {result.value}"
```

### Value is wrong type

**Symptom:**
```python
# Wrote a float
tx.write(agent_id="a1", key="k", value={"x": 3.5})

# Read back an int
result = client.get_state(agent_id="a1", key="k")
print(result.value)  # {"x": 3} or {"x": 3.0}
```

**Cause:**
JSON number precision or Python float/int conversion.

**Solution:**
```python
# Store numbers as strings if exact precision needed
tx.write(agent_id="a1", key="k", value={"x": "3.5"})

# Or use Decimal
from decimal import Decimal
value = {"x": float(Decimal("3.5"))}
```

## Replay Issues

### No events in replay

**Symptom:**
```python
events = list(client.replay(agent_id="a1"))
# events is []
```

**Diagnosis:**
```python
# Check if any keys exist
keys = client.list_keys(agent_id="a1")
print(f"Keys: {keys}")

# Check all namespaces
for ns in ["default", "dev", "prod"]:
    events = list(client.replay(agent_id="a1", namespace=ns))
    print(f"{ns}: {len(events)} events")
```

**Causes:**
1. No transactions committed for this agent
2. Wrong agent_id
3. Wrong namespace
4. Time range filter excludes all events

**Solution:**
```python
# Verify agent has data
keys = client.list_keys(agent_id="a1")
if not keys:
    print("Agent has no state")
else:
    # Try replay without filters
    events = list(client.replay(agent_id="a1"))
    print(f"Found {len(events)} events")
```

### Replay is slow

**Symptom:**
```python
# Takes forever
for event in client.replay(agent_id="agent-with-millions-of-events"):
    process(event)
```

**Cause:**
Large event history (millions of events).

**Solutions:**

1. **Use time range filter:**
   ```python
   # Only recent events
   for event in client.replay(
       agent_id="a1",
       from_timestamp="2026-02-07T00:00:00Z"
   ):
       process(event)
   ```

2. **Process incrementally:**
   ```python
   # Save last processed timestamp
   last_ts = load_checkpoint()
   
   for event in client.replay(
       agent_id="a1",
       from_timestamp=last_ts
   ):
       process(event)
       save_checkpoint(event.timestamp)
   ```

3. **Use summaries:**
   ```python
   # Don't replay everything
   # Instead, store periodic summaries
   result = client.get_state(agent_id="a1", key="summary:latest")
   ```

## Performance Issues

### Writes are slow

**Symptom:**
```python
# Takes 100ms per write
for i in range(100):
    with client.begin_transaction() as tx:
        tx.write(agent_id="a1", key=f"k{i}", value={"x": i})
# Total: 10 seconds!
```

**Cause:**
Each transaction requires a disk fsync (2-5ms).

**Solution:**

Batch writes:
```python
# One transaction for all writes
with client.begin_transaction() as tx:
    for i in range(100):
        tx.write(agent_id="a1", key=f"k{i}", value={"x": i})
# Total: <100ms
```

### Daemon uses too much memory

**Symptom:**
```bash
$ ps aux | grep statehoused
# RSS: 5GB
```

**Causes:**
1. Large values
2. Many active transactions
3. RocksDB cache

**Solutions:**

1. **Reduce value sizes:**
   ```python
   # BAD: storing large data
   tx.write(agent_id="a1", key="k", value={"data": [...1MB list...]})
   
   # GOOD: store reference
   s3_key = store_to_s3(large_data)
   tx.write(agent_id="a1", key="k", value={"s3_key": s3_key})
   ```

2. **Clean up transactions:**
   ```python
   # Make sure transactions are committed or aborted
   try:
       with client.begin_transaction() as tx:
           # ...
   except Exception:
       # Context manager handles abort
   ```

3. **Tune RocksDB:**
   Configure block cache size (future: via config file).

### Daemon crashes

**Symptom:**
```bash
$ pgrep statehoused
# No output
```

**Diagnosis:**
```bash
# Check logs
tail -100 daemon.log

# Try running in foreground
RUST_LOG=debug ./statehoused
```

**Common causes:**

1. **Out of memory:**
   ```bash
   # Check dmesg
   dmesg | grep -i "out of memory"
   ```

2. **Disk full:**
   ```bash
   df -h
   ```

3. **RocksDB corruption:**
   ```bash
   # Check data directory
   ls -lh data/rocksdb/
   
   # Try recovery
   mv data/rocksdb data/rocksdb.bak
   ./statehoused  # Starts fresh
   ```

4. **Panic:**
   ```
   # Rust panic in logs
   thread 'main' panicked at 'assertion failed: ...'
   ```
   → File a bug report

## Testing Issues

### Tests fail with "Connection refused"

**Symptom:**
```bash
$ pytest
# ConnectionError: Failed to connect to localhost:50051
```

**Cause:**
Daemon not running.

**Solution:**
```bash
# Terminal 1: start daemon
STATEHOUSE_USE_MEMORY=1 ./target/release/statehoused

# Terminal 2: run tests
cd python && pytest
```

### Tests are flaky

**Symptom:**
Tests pass sometimes, fail sometimes.

**Causes:**
1. **Test isolation** - tests interfering with each other
2. **Timing issues** - race conditions
3. **Shared state** - tests using same agent_id

**Solutions:**

1. **Use unique agent IDs:**
   ```python
   import time
   
   def test_something():
       agent_id = f"test-agent-{time.time()}"
       # Use this agent_id
   ```

2. **Clean up:**
   ```python
   def test_something(client):
       agent_id = "test-agent"
       
       # Test logic
       
       # Clean up
       keys = client.list_keys(agent_id=agent_id)
       with client.begin_transaction() as tx:
           for key in keys:
               tx.delete(agent_id=agent_id, key=key)
   ```

3. **Use fixtures:**
   ```python
   @pytest.fixture
   def unique_agent():
       return f"agent-{uuid.uuid4()}"
   
   def test_something(unique_agent):
       client.write(agent_id=unique_agent, ...)
   ```

## Python SDK Issues

### Import error

**Symptom:**
```python
>>> import statehouse
ModuleNotFoundError: No module named 'statehouse'
```

**Solution:**
```bash
cd python
pip install -e .
```

### Protobuf version conflict

**Symptom:**
```python
TypeError: Descriptors cannot not be created directly
```

**Cause:**
Incompatible protobuf versions.

**Solution:**
```bash
pip install --upgrade protobuf>=4.25.0
```

### AttributeError in generated code

**Symptom:**
```python
AttributeError: module 'statehouse._generated...' has no attribute 'X'
```

**Cause:**
Generated code is stale.

**Solution:**
```bash
cd python
bash generate_proto.sh
pip install -e .
```

## CLI Issues

### statehousectl command not found

**Symptom:**
```bash
$ statehousectl health
bash: statehousectl: command not found
```

**Solutions:**

1. **Install package:**
   ```bash
   cd python
   pip install -e .
   ```

2. **Use module form:**
   ```bash
   python3 -m statehouse.cli.main health
   ```

3. **Check PATH:**
   ```bash
   # Find where pip installed it
   which statehousectl
   
   # Add to PATH if needed
   export PATH="$HOME/.local/bin:$PATH"
   ```

### CLI hangs

**Symptom:**
```bash
$ statehousectl keys agent-1
# Hangs forever
```

**Causes:**
1. Daemon not responding
2. Network issue
3. Large result set

**Solutions:**

1. **Check daemon:**
   ```bash
   statehousectl health
   ```

2. **Try simpler command:**
   ```bash
   statehousectl health
   statehousectl keys agent-1 --json
   ```

3. **Use timeout:**
   ```bash
   timeout 10s statehousectl keys agent-1
   ```

## Build Issues

### Cargo build fails

**Symptom:**
```bash
$ cargo build
error: failed to compile ...
```

**Solutions:**

1. **Update Rust:**
   ```bash
   rustup update stable
   rustc --version  # Should be 1.70+
   ```

2. **Clean build:**
   ```bash
   cargo clean
   cargo build
   ```

3. **Check dependencies:**
   ```bash
   # RocksDB requires clang
   # macOS
   xcode-select --install
   
   # Linux
   sudo apt install clang librocksdb-dev
   ```

### Proto codegen fails

**Symptom:**
```bash
error: failed to run custom build command for `statehouse-proto`
```

**Solution:**
```bash
# Make sure protoc is installed
protoc --version

# macOS
brew install protobuf

# Linux
sudo apt install protobuf-compiler
```

## Getting Help

If you can't solve the problem:

1. **Check logs:**
   ```bash
   RUST_LOG=debug ./statehoused 2>&1 | tee debug.log
   ```

2. **Minimal reproduction:**
   Create a simple script that reproduces the issue.

3. **Gather info:**
   - Statehouse version
   - Python version
   - OS and version
   - Error messages
   - Logs

4. **Contact support:**
   - Email: support@statehouse.dev
   - Include all info above
   - Attach logs if possible

## Common Patterns

### Idempotent Operations

```python
def write_idempotent(client, agent_id, key, value):
    """Write that can be safely retried."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with client.begin_transaction() as tx:
                tx.write(agent_id=agent_id, key=key, value=value)
            return
        except TransactionError:
            if attempt == max_retries - 1:
                raise
            time.sleep(1)
```

### Safe Deletion

```python
def safe_delete(client, agent_id, key):
    """Delete only if key exists."""
    if client.get_state(agent_id=agent_id, key=key):
        with client.begin_transaction() as tx:
            tx.delete(agent_id=agent_id, key=key)
```

### Conditional Update

```python
def update_if_version(client, agent_id, key, expected_version, new_value):
    """Update only if version matches (optimistic locking)."""
    current = client.get_state(agent_id=agent_id, key=key)
    
    if current and current.version == expected_version:
        with client.begin_transaction() as tx:
            tx.write(agent_id=agent_id, key=key, value=new_value)
        return True
    else:
        return False  # Version conflict
```

## See Also

- [FAQ](faq.md) - Frequently asked questions
- [gRPC Architecture](grpc_architecture.md) - How Statehouse works
- [Python SDK](../python/README.md) - Client documentation
- [Example Agent](../examples/agent_research/) - Working examples
