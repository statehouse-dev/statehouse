# Determinism

Statehouse provides **deterministic** behavior, which is essential for debugging, testing, and trust.

## What is Determinism?

Determinism means: **given the same inputs, you get the same outputs**.

In Statehouse:
- Same events → same state
- Same replay → same order
- Same operations → same versions

## Deterministic Guarantees

### Event Ordering

Events are ordered deterministically by `commit_ts`:
- Monotonically increasing
- Assigned at commit time
- Same events always produce same order

### State Reconstruction

Replaying events always produces the same state:
- Start from snapshot (if available)
- Apply events in commit timestamp order
- Result is deterministic

### Version Assignment

Versions are assigned deterministically:
- Per-key monotonic counters
- Increment exactly once per write
- Same writes → same versions

## Why Determinism Matters

### Debugging

Deterministic replay enables:
- Reproducing bugs reliably
- Understanding agent behavior
- Inspecting state at any point

### Testing

Deterministic behavior enables:
- Reproducible tests
- Regression detection
- Confidence in correctness

### Trust

Determinism builds trust:
- Predictable behavior
- Auditable history
- Explainable decisions

## Non-Deterministic Aspects

Some aspects are intentionally non-deterministic:

### Transaction Timing

When transactions commit is not deterministic:
- Depends on network latency
- Depends on client behavior
- Depends on server load

### Commit Timestamps

`commit_ts` values are deterministic **relative to each other**:
- Ordering is deterministic
- Absolute values may vary between runs
- Relative ordering is preserved

## Example

```python
# Write operations in different orders
tx1 = client.begin_transaction()
tx1.write(agent_id="agent-1", key="a", value={"x": 1})

tx2 = client.begin_transaction()
tx2.write(agent_id="agent-1", key="b", value={"y": 2})

# Commit order may vary, but replay order is deterministic
tx2.commit()  # commit_ts = 10
tx1.commit()  # commit_ts = 11

# Replay always shows: b (ts=10), then a (ts=11)
for event in client.replay(agent_id="agent-1"):
    # Always: b first, then a
    pass
```

## Next Steps

- [Replay](replay) - See deterministic replay in action
- [State and Events](state-and-events) - Understand the deterministic state model
