# Data Directories

Statehouse stores all persistent data in a single directory.

## Structure

```
statehouse-data/
├── rocksdb/           # RocksDB database files
│   ├── CURRENT
│   ├── IDENTITY
│   ├── LOCK
│   ├── LOG
│   ├── MANIFEST-*
│   ├── OPTIONS-*
│   └── *.sst          # Data files
└── snapshots/         # Snapshot files
    └── snapshot-*.json
```

## Configuration

Set the data directory:

```bash
export STATEHOUSE_DATA_DIR=/var/lib/statehouse
```

Default: `./statehouse-data`

## Permissions

The data directory must be:
- Writable by the daemon process
- Readable only by the daemon (recommended)

```bash
# Create with proper permissions
sudo mkdir -p /var/lib/statehouse
sudo chown statehouse:statehouse /var/lib/statehouse
sudo chmod 700 /var/lib/statehouse
```

## Disk Space

Monitor disk usage:

```bash
du -sh /var/lib/statehouse
```

Space is consumed by:
- RocksDB SST files (main storage)
- Write-ahead log
- Snapshots

## RocksDB Files

| File Type | Purpose |
|-----------|---------|
| `*.sst` | Sorted string table (data) |
| `MANIFEST-*` | Database metadata |
| `LOG` | RocksDB operational log |
| `LOCK` | Prevents concurrent access |

Do not modify these files manually.

## Backup

To backup Statehouse data:

```bash
# Stop daemon first (recommended)
systemctl stop statehoused

# Copy entire directory
cp -r /var/lib/statehouse /backup/statehouse-$(date +%Y%m%d)

# Or use rsync
rsync -av /var/lib/statehouse/ /backup/statehouse/

# Restart daemon
systemctl start statehoused
```

For online backup, use RocksDB's checkpoint feature (advanced).

## Recovery

To restore from backup:

```bash
systemctl stop statehoused
rm -rf /var/lib/statehouse
cp -r /backup/statehouse-20260207 /var/lib/statehouse
chown -R statehouse:statehouse /var/lib/statehouse
systemctl start statehoused
```

## Multiple Instances

Run multiple instances with different data directories:

```bash
# Instance 1
STATEHOUSE_DATA_DIR=/var/lib/statehouse-1 \
STATEHOUSE_LISTEN_ADDR=0.0.0.0:50051 \
./statehoused

# Instance 2
STATEHOUSE_DATA_DIR=/var/lib/statehouse-2 \
STATEHOUSE_LISTEN_ADDR=0.0.0.0:50052 \
./statehoused
```

Each instance is completely independent.

## Cleanup

To completely reset:

```bash
systemctl stop statehoused
rm -rf /var/lib/statehouse
mkdir -p /var/lib/statehouse
chown statehouse:statehouse /var/lib/statehouse
systemctl start statehoused
```

This destroys all data. Use with caution.
