# Snapshots

Snapshots capture the current state for faster recovery after restart.

## How Snapshots Work

1. Daemon tracks commits since last snapshot
2. At configured interval, creates snapshot
3. Snapshot captures all current state
4. On restart, loads latest snapshot + replays newer events

## Configuration

```bash
# Commits between snapshots (default: 1000)
export STATEHOUSE_SNAPSHOT_INTERVAL=1000
```

| Interval | Trade-off |
|----------|-----------|
| Lower (100) | Faster recovery, more disk I/O |
| Higher (10000) | Slower recovery, less disk I/O |

Recommended: 500-2000 for most workloads.

## Snapshot Format

Snapshots are stored as JSON:

```json
{
  "version": 1,
  "created_at": 1707300000,
  "commit_ts": 12345,
  "state": {
    "default:agent-1:memory": {
      "value": {"fact": "..."},
      "version": 5,
      "commit_ts": 12340
    }
  }
}
```

## Manual Snapshot

Currently, snapshots are automatic only. Manual snapshot API may be added in future versions.

## Recovery Process

On startup:

1. Find latest snapshot in `snapshots/` directory
2. Load snapshot into memory
3. Scan event log for events after snapshot
4. Apply events to reach current state
5. Ready to serve requests

## Performance Impact

Snapshot creation:
- Brief pause (milliseconds for small state)
- Writes to disk synchronously
- Does not block reads

For very large state (millions of keys), consider:
- Increasing snapshot interval
- Faster storage (SSD)

## Disk Space

Old snapshots are kept for safety. Manual cleanup:

```bash
# Keep only recent snapshots
cd /var/lib/statehouse/snapshots
ls -t | tail -n +4 | xargs rm -f
```

This keeps the 3 most recent snapshots.

## Monitoring

Check snapshot status in logs:

```
INFO  Creating snapshot at commit_ts=12345
INFO  Snapshot created: snapshot-12345.json
```

On startup:

```
INFO  Loading snapshot: snapshot-12345.json
INFO  Replaying 42 events since snapshot
INFO  Recovery complete
```

## Disabling Snapshots

Not recommended, but possible:

```bash
# Very high interval effectively disables
export STATEHOUSE_SNAPSHOT_INTERVAL=999999999
```

Recovery will replay entire event log on restart.
