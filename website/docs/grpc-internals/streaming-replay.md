# Streaming Replay

The Replay RPC uses gRPC server streaming to efficiently deliver event logs.

## Protocol

```protobuf
rpc Replay(ReplayRequest) returns (stream ReplayEvent);
```

The server streams `ReplayEvent` messages to the client until:
- All matching events are sent
- Client cancels the stream
- An error occurs

## Request

```protobuf
message ReplayRequest {
  string namespace = 1;
  string agent_id = 2;
  optional uint64 start_ts = 3;
  optional uint64 end_ts = 4;
}
```

| Field | Description |
|-------|-------------|
| `namespace` | State namespace |
| `agent_id` | Agent to replay |
| `start_ts` | Include events at or after this timestamp (optional) |
| `end_ts` | Include events at or before this timestamp (optional) |

## Response Stream

```protobuf
message ReplayEvent {
  string txn_id = 1;
  uint64 commit_ts = 2;
  repeated ReplayOperation operations = 3;
}

message ReplayOperation {
  string key = 1;
  google.protobuf.Struct value = 2;
  uint64 version = 3;
}
```

Each event represents one committed transaction.

## Ordering Guarantee

Events are streamed in **commit timestamp order**, which is the same as commit order. This ordering is deterministic.

```python
for event in client.replay(agent_id="agent"):
    # Events arrive in commit order
    # event.commit_ts is monotonically increasing
```

## Backpressure

gRPC provides automatic backpressure:

1. Client processes events at its own pace
2. Server pauses when client buffer is full
3. No memory explosion on either side

This is critical for large replays (millions of events).

## Early Termination

Clients can terminate replay early:

```python
for event in client.replay(agent_id="agent"):
    if should_stop(event):
        break  # Stream is cancelled
```

The server detects cancellation and stops sending.

## Memory Efficiency

The streaming model ensures:

- Server doesn't load entire log into memory
- Client doesn't buffer all events
- Constant memory usage regardless of log size

## Error Handling

Stream errors are delivered as gRPC status codes:

```python
try:
    for event in client.replay(agent_id="agent"):
        process(event)
except StatehouseError as e:
    # Handle stream error
    pass
```

## Performance Characteristics

| Metric | Typical Value |
|--------|---------------|
| Events per second | 10,000-100,000 |
| Latency per event | < 1ms |
| Memory per stream | O(1) constant |

Actual performance depends on:
- Event size
- Network bandwidth
- Storage backend

## Implementation Notes

The Rust daemon uses `tokio` and `tonic` for async streaming:

```rust
async fn replay(
    &self,
    request: Request<ReplayRequest>,
) -> Result<Response<Self::ReplayStream>, Status> {
    // Create async stream of events
    let stream = self.state_machine.replay(...);
    Ok(Response::new(stream))
}
```

The Python SDK wraps the gRPC stream as a Python iterator:

```python
def replay(self, agent_id, ...):
    for event in self._stub.Replay(request):
        yield ReplayEvent(...)
```
