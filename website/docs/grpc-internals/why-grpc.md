# Why gRPC

Statehouse uses gRPC as its wire protocol. This document explains the rationale.

## Requirements

Statehouse needed a protocol that provides:

1. **Strong typing**: Clear contract between client and server
2. **Streaming**: Efficient replay of large event logs
3. **Code generation**: Reduce boilerplate in client SDKs
4. **Language support**: Rust server, Python/Go/etc clients
5. **Performance**: Low overhead for high-frequency operations

## Why Not REST/HTTP?

REST was considered but rejected for several reasons:

| Concern | REST | gRPC |
|---------|------|------|
| Streaming | Chunked/SSE (awkward) | First-class support |
| Typing | JSON Schema (optional) | Protobuf (required) |
| Codegen | Limited | Excellent |
| Binary payloads | Base64 encoding | Native |
| Backpressure | Manual | Built-in |

The replay RPC, which streams potentially millions of events, benefits significantly from gRPC's streaming model.

## Why Not Custom Protocol?

A custom binary protocol would provide maximum performance but:

- Requires custom parsers for every language
- No standardized tooling (debugging, tracing)
- Higher maintenance burden
- Steeper learning curve for contributors

gRPC provides 90% of custom protocol performance with significantly less complexity.

## Protocol Buffers

Statehouse uses Protocol Buffers (protobuf) for message serialization:

- Schema evolution with backwards compatibility
- Compact binary encoding
- Generated code with type safety
- Self-documenting API

The proto file is the source of truth for the API.

## gRPC Features Used

### Unary RPCs

Most operations use simple request-response:

```protobuf
rpc BeginTransaction(BeginTransactionRequest) returns (BeginTransactionResponse);
rpc Write(WriteRequest) returns (WriteResponse);
rpc Commit(CommitRequest) returns (CommitResponse);
```

### Server Streaming

Replay uses server streaming for efficient event delivery:

```protobuf
rpc Replay(ReplayRequest) returns (stream ReplayEvent);
```

This allows:
- Backpressure from slow clients
- Early termination
- Memory-efficient large replays

## Hidden from Users

The Python SDK completely hides gRPC:

```python
# Users see this (Pythonic)
result = client.get_state(agent_id="agent", key="memory")

# Not this (gRPC)
request = statehouse_pb2.GetStateRequest(...)
response = stub.GetState(request)
```

This abstraction ensures:
- Users don't need gRPC knowledge
- SDK can change internal protocol
- Clean, Pythonic API

## Trade-offs

### Accepted Trade-offs

- **Binary protocol**: Harder to debug with curl (mitigated by grpcurl)
- **Protobuf dependency**: Adds complexity to build process
- **HTTP/2 requirement**: Some proxies need configuration

### Mitigations

- `statehousectl` CLI for human interaction
- Structured logging for debugging
- Docker/packaging includes all dependencies
