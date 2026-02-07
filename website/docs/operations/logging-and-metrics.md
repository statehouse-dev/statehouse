# Logging and Metrics

Statehouse provides structured logging for observability.

## Log Format

Logs use structured format with consistent fields:

```
2026-02-07T12:00:00Z INFO  [statehouse_daemon::service] Transaction committed txn_id=abc123 commit_ts=12345 operations=3
```

## Log Levels

| Level | When Used |
|-------|-----------|
| ERROR | Failures requiring attention |
| WARN | Recoverable issues |
| INFO | Normal operations |
| DEBUG | Detailed flow |
| TRACE | Very verbose |

Configure with `RUST_LOG`:

```bash
export RUST_LOG=info
```

## Key Log Events

### Startup

```
INFO  Statehouse starting
INFO  Storage: RocksDB at /var/lib/statehouse
INFO  Listening on 0.0.0.0:50051
```

### Transaction Lifecycle

```
DEBUG Transaction started txn_id=abc123
INFO  Transaction committed txn_id=abc123 commit_ts=12345 operations=3
DEBUG Transaction aborted txn_id=abc123
```

### Replay

```
INFO  Replay started namespace=default agent_id=my-agent
INFO  Replay completed namespace=default agent_id=my-agent events=147
```

### Recovery

```
INFO  Loading snapshot: snapshot-12345.json
INFO  Replaying 147 events since snapshot
INFO  Recovery complete
```

### Errors

```
ERROR Write failed: disk full
ERROR Transaction timeout: txn_id=abc123
```

## Log Output

By default, logs go to stderr. Redirect as needed:

```bash
# To file
./statehoused 2> /var/log/statehouse.log

# With systemd (automatic)
journalctl -u statehoused
```

## Internal Metrics

Statehouse tracks internal counters:

| Metric | Description |
|--------|-------------|
| Transactions started | Total BeginTransaction calls |
| Transactions committed | Successful commits |
| Transactions aborted | Explicit aborts |
| Transactions expired | Timeout aborts |
| Writes | Total write operations |
| Deletes | Total delete operations |
| Reads | Total read operations |
| Replay events | Events streamed |

Currently exposed in debug logs. Prometheus endpoint planned for future.

## Log Rotation

With logrotate:

```
/var/log/statehouse.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    copytruncate
}
```

With systemd journal:

```bash
# Configure journal size
journalctl --vacuum-size=500M
```

## Debugging

Enable debug logging for specific modules:

```bash
# State machine details
RUST_LOG=statehouse_core::state_machine=debug,info

# gRPC layer
RUST_LOG=statehouse_daemon::service=debug,info

# All debug
RUST_LOG=debug
```

## Tracing

For distributed tracing (future):

- OpenTelemetry support planned
- Trace IDs in log output
- Span correlation

## Health Monitoring

Check daemon health:

```python
from statehouse import Statehouse

client = Statehouse()
status = client.health()  # Returns "ok"
```

Or via CLI:

```bash
statehousectl health
```

## Alerting Recommendations

Alert on:

- Daemon not responding to health checks
- Error rate spike in logs
- Disk usage approaching capacity
- Transaction timeout rate increase

Monitor:

- Commits per second
- Replay latency
- Recovery time after restart
