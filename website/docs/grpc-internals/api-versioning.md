# API Versioning

Statehouse uses a versioned API to ensure stability and backward compatibility.

## Version Scheme

The API version is embedded in the protobuf package:

```protobuf
package statehouse.v1;
```

This means:
- Current stable API: `v1`
- Package name: `statehouse.v1`
- Service name: `StatehouseService`

## Stability Guarantees

For the `v1` API:

| Change Type | Allowed | Example |
|-------------|---------|---------|
| Add new RPC | Yes | Adding `WatchKeys` |
| Add new field | Yes | Adding `metadata` to response |
| Remove field | No | Removing `version` from response |
| Remove RPC | No | Removing `GetState` |
| Change field type | No | `int64` to `string` |
| Rename field | No | `agent_id` to `agent_identifier` |

## Adding Fields

New fields can be added to existing messages:

```protobuf
message GetStateResponse {
  bool exists = 1;
  google.protobuf.Struct value = 2;
  uint64 version = 3;
  uint64 commit_ts = 4;
  // New field - old clients ignore it
  map<string, string> metadata = 5;
}
```

Old clients simply ignore new fields they don't understand.

## Reserved Fields

Removed fields are reserved to prevent reuse:

```protobuf
message SomeMessage {
  reserved 2, 3;
  reserved "old_field", "deprecated_field";
  
  string current_field = 1;
  string new_field = 4;
}
```

## Version Negotiation

Currently, Statehouse does not perform version negotiation. Clients are expected to use the `v1` API.

The `Version` RPC returns the server version:

```python
version, git_sha = client.version()
# version: "0.1.0"
# git_sha: "abc123"
```

## Future Versions

If a `v2` API is needed:

1. New package: `statehouse.v2`
2. Parallel support for `v1` and `v2`
3. Deprecation period for `v1`
4. Migration guide published

The SDK would handle version selection automatically.

## Proto File Location

The canonical proto file is at:

```
crates/statehouse-proto/proto/statehouse/v1/statehouse.proto
```

Generated code:
- Rust: Built automatically by `tonic-build`
- Python: Generated via `generate_proto.sh`
