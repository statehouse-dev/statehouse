# Statehouse Python SDK Tests

These are integration tests that require a running Statehouse daemon.

## Running Tests

### 1. Start the Daemon

From the repository root:

```bash
# Use in-memory storage for testing (no persistence)
STATEHOUSE_USE_MEMORY=1 cargo run --bin statehouse-daemon
```

Or use the dev script:

```bash
./scripts/dev.sh
```

### 2. Run Tests

In a separate terminal:

```bash
cd python
pytest tests/ -v
```

## Test Coverage

- **TestHealthAndVersion**: Health check and version endpoints
- **TestTransactionLifecycle**: Transaction write/commit/abort operations
- **TestReadOperations**: Read-after-write, list_keys, scan_prefix
- **TestReplay**: Event replay and iteration
- **TestErrorMapping**: Error handling and exception types
- **TestRestartSafety**: Data persistence and recovery

## Test Requirements

- pytest
- grpcio
- Running Statehouse daemon on localhost:50051

## Notes

- Tests use unique keys/agent IDs (timestamped) to avoid conflicts
- In-memory storage is recommended for tests (faster, cleaner)
- Some tests verify error conditions (timeouts, invalid IDs, etc.)
