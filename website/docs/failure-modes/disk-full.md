# Disk Full

This document describes behavior when the storage disk runs out of space.

## Symptoms

When disk is full:

- Write operations fail
- Commits fail
- Logs show I/O errors
- Daemon may crash

## Impact

| Operation | Behavior |
|-----------|----------|
| Read | Works (existing data) |
| Write | Fails with error |
| Commit | Fails with error |
| Snapshot | Fails |

## Client Experience

Clients receive errors:

```python
from statehouse import TransactionError

try:
    with client.begin_transaction() as tx:
        tx.write(...)
except TransactionError as e:
    # "Write failed: No space left on device"
    pass
```

## Recovery

1. **Free disk space**

```bash
# Check usage
df -h /var/lib/statehouse

# Remove old logs/backups
rm /var/log/old-logs/*

# Clean old snapshots
cd /var/lib/statehouse/snapshots
ls -t | tail -n +4 | xargs rm -f
```

2. **Restart daemon if crashed**

```bash
systemctl start statehoused
```

3. **Verify operation**

```python
client.health()  # Should return "ok"
```

## Prevention

### Monitor Disk Usage

Set up alerts:

```bash
# Alert at 80% usage
if [ $(df /var/lib/statehouse --output=pcent | tail -1 | tr -dc '0-9') -gt 80 ]; then
    echo "Disk usage high"
fi
```

### Size Estimation

Estimate storage needs:

| Factor | Space |
|--------|-------|
| Per key-value | ~100 bytes + value size |
| Per transaction | ~50 bytes overhead |
| Snapshots | ~size of all current state |

For 1 million keys with 1KB values: ~1-2 GB

### Separate Partition

Consider dedicated partition:

```bash
# Mount dedicated volume
mount /dev/sdb1 /var/lib/statehouse
```

Benefits:
- Isolation from system disk
- Predictable space
- Easy to expand

### Log Rotation

Configure RocksDB log limits (future configuration):

```bash
# Currently: monitor and clean manually
STATEHOUSE_MAX_LOG_SIZE=104857600  # 100MB
```

## Data Safety

Disk full does not corrupt existing data:

- RocksDB handles write failures gracefully
- Committed transactions remain intact
- Recovery works after space freed

## Emergency Procedures

If disk is 100% full:

1. Stop daemon to prevent further issues
2. Free space (delete non-essential files)
3. Verify at least 10% free
4. Start daemon
5. Verify data integrity with reads

```bash
systemctl stop statehoused
rm -rf /tmp/large-files
df -h  # Verify space
systemctl start statehoused
statehousectl health
```
