# Recovery

Statehouse is designed to recover automatically from crashes and restarts.

## Automatic Recovery

When the daemon starts:

1. Opens RocksDB database
2. Loads latest snapshot (if exists)
3. Replays events since snapshot
4. Resumes normal operation

No manual intervention required.

## Recovery Time

Recovery time depends on:

| Factor | Impact |
|--------|--------|
| Snapshot age | More events to replay = slower |
| Event count | Linear in number of events |
| Storage speed | SSD recommended |

With default settings (snapshot every 1000 commits):
- Typical recovery: < 1 second
- Worst case: few seconds

## Verifying Recovery

Check logs after restart:

```
INFO  statehoused starting
INFO  Loading snapshot: snapshot-12345.json
INFO  Replaying 147 events since snapshot
INFO  Recovery complete, current commit_ts: 12492
INFO  Listening on 0.0.0.0:50051
```

## Data Integrity

Statehouse guarantees:

- Committed transactions survive restart
- No partial transactions visible
- Event order preserved
- Deterministic replay

These invariants hold through:
- Process crash
- Kill -9
- Power failure (with fsync enabled)

## Fsync Configuration

For durability:

```bash
# Recommended for production
export STATEHOUSE_FSYNC_ON_COMMIT=1
```

With fsync enabled:
- Each commit is durable before acknowledgment
- Survives power failure
- Slight performance cost

With fsync disabled:
- Faster commits
- May lose recent commits on power failure
- Acceptable for development

## Crash During Write

If crash occurs during a write:

| State | Outcome |
|-------|---------|
| Before commit | Transaction lost (as expected) |
| During commit | Transaction atomic - either complete or absent |
| After commit | Transaction durable |

This is the "no partial transactions visible" invariant.

## Corrupt Data

If RocksDB detects corruption:

1. Daemon logs error and exits
2. Restore from backup
3. Or: delete data directory and start fresh

Corruption is rare with fsync enabled and healthy storage.

## Manual Recovery Steps

If automatic recovery fails:

```bash
# Check logs for error details
journalctl -u statehoused -n 100

# Try with debug logging
RUST_LOG=debug ./statehoused

# As last resort, reset data
rm -rf /var/lib/statehouse
./statehoused
```

## Testing Recovery

Verify recovery works:

```bash
# Write some data
./test-write.py

# Simulate crash
kill -9 $(pgrep statehoused)

# Restart
./statehoused

# Verify data
./test-read.py
```

Include this in your operational testing.
