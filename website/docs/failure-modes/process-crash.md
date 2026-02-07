# Process Crash

This document describes behavior when the Statehouse daemon process crashes.

## Causes

Common crash causes:

- Out of memory (OOM kill)
- Unhandled panic
- SIGKILL from operator
- System shutdown
- Hardware failure

## Impact

| State at Crash | Outcome |
|----------------|---------|
| Idle | No data loss |
| Mid-transaction (uncommitted) | Transaction lost |
| During commit (with fsync) | Transaction atomic |
| After commit | Transaction durable |

## Recovery

Restart the daemon:

```bash
systemctl start statehoused
# or
./statehoused
```

Recovery is automatic:

1. RocksDB opens with crash recovery
2. Latest snapshot loaded
3. Events since snapshot replayed
4. Service ready

## Uncommitted Transactions

Transactions not yet committed are lost. Clients see:

```python
try:
    with client.begin_transaction() as tx:
        tx.write(...)
        # Daemon crashes here
except ConnectionError:
    # Transaction was not committed
    pass
```

This is expected behavior. The client should retry.

## Committed Transactions

Transactions that received a commit response are durable:

```python
with client.begin_transaction() as tx:
    tx.write(...)
commit_ts = tx.commit()  # Returns successfully
# Even if daemon crashes now, this transaction is safe
```

## Client Behavior

Clients detect crash via connection errors:

```python
from statehouse import ConnectionError

try:
    result = client.get_state(...)
except ConnectionError:
    # Daemon crashed or network issue
    # Wait and retry
    time.sleep(1)
    client = Statehouse()  # Reconnect
    result = client.get_state(...)
```

## Automatic Restart

Configure systemd for automatic restart:

```ini
[Service]
Restart=always
RestartSec=1
```

Clients experience brief unavailability, then reconnect.

## Preventing OOM

If crashing due to OOM:

1. Increase system memory
2. Configure systemd memory limits:

```ini
[Service]
MemoryMax=2G
```

3. Review workload for memory leaks

## Monitoring

Alert on:

- Process exit codes
- Systemd restart count
- Recovery time

```bash
# Check restart count
systemctl show statehoused --property=NRestarts
```

## Testing

Include crash testing in your validation:

```bash
# Write data
./write-test.py

# Simulate crash
kill -9 $(pgrep statehoused)

# Restart
systemctl start statehoused

# Verify data
./verify-test.py
```
