"""
Tests for formatting utilities.
"""

import pytest
from statehouse.formatting import (
    format_ts,
    format_key,
    format_value_summary,
    format_event_pretty,
    format_event_verbose,
    format_event_json,
)


def test_format_ts():
    """Test timestamp formatting."""
    # Test a known timestamp
    ts = 1770488464
    result = format_ts(ts)
    assert result == "18:21:04Z"  # Actual UTC time for this timestamp
    
    # Test midnight UTC (1970-01-01 00:00:00)
    ts_midnight = 0
    result = format_ts(ts_midnight)
    assert result == "00:00:00Z"


def test_format_key_short():
    """Test formatting of short keys."""
    key = "context"
    result = format_key(key)
    assert result == "context"
    
    key = "step/001"
    result = format_key(key)
    assert result == "step/001"


def test_format_key_long():
    """Test truncation of long keys."""
    # Very long key without slashes
    key = "a" * 100
    result = format_key(key)
    assert len(result) <= 48
    assert result.endswith("...")
    
    # Path-like key
    key = "agent/research-1/task/subtask/very-long-key-name-that-should-be-truncated"
    result = format_key(key)
    assert len(result) <= 48
    assert "/" in result
    assert "..." in result


def test_format_value_summary_primitives():
    """Test formatting of primitive values."""
    assert format_value_summary(None) == "null"
    assert format_value_summary(True) == "true"
    assert format_value_summary(False) == "false"
    assert format_value_summary(42) == "42"
    assert format_value_summary(3.14159) == "3.14159"


def test_format_value_summary_strings():
    """Test string formatting and truncation."""
    # Short string
    result = format_value_summary("hello")
    assert result == '"hello"'
    
    # String with newlines
    result = format_value_summary("line1\nline2")
    assert result == '"line1\\nline2"'
    
    # Long string (truncated)
    long_str = "a" * 200
    result = format_value_summary(long_str)
    assert len(result) <= 126  # 120 + quotes + "..."
    assert result.endswith('..."')


def test_format_value_summary_lists():
    """Test list formatting."""
    # Empty list
    assert format_value_summary([]) == "[]"
    
    # Short list
    result = format_value_summary([1, 2, 3])
    assert result == "[1,2,3]"
    
    # List with strings
    result = format_value_summary(["a", "b"])
    assert result == '["a","b"]'
    
    # Long list (summarized)
    long_list = list(range(100))
    result = format_value_summary(long_list)
    assert "len=" in result
    assert result.startswith("[")


def test_format_value_summary_dicts():
    """Test dict formatting."""
    # Empty dict
    assert format_value_summary({}) == "{}"
    
    # Small dict (compact JSON)
    result = format_value_summary({"a": 1, "b": 2})
    assert result in ['{"a":1,"b":2}', '{"b":2,"a":1}']  # Order may vary
    
    # Large dict (summarized)
    large_dict = {f"key{i}": i for i in range(20)}
    result = format_value_summary(large_dict)
    assert "n_fields=" in result
    assert "20" in result


def test_format_value_summary_nested():
    """Test nested structure formatting."""
    nested = {
        "user": "agent-1",
        "data": {
            "results": [1, 2, 3],
            "metadata": {"count": 3}
        }
    }
    result = format_value_summary(nested)
    # Should produce compact or summary format
    assert len(result) <= 130  # Slightly over max_len is OK
    assert "{" in result


def test_format_event_pretty_basic():
    """Test basic pretty event formatting."""
    result = format_event_pretty(
        timestamp=1770488464,
        agent_id="research-1",
        operation="write",
        key="context",
        version=3,
        value={"topic": "databases"},
    )
    
    assert "18:21:04Z" in result
    assert "agent=research-1" in result
    assert "WRITE" in result
    assert "key=context" in result
    assert "v=3" in result
    assert "topic" in result or "databases" in result


def test_format_event_pretty_operation_types():
    """Test operation type detection."""
    # DELETE
    result = format_event_pretty(
        timestamp=1770488464,
        agent_id="agent-1",
        operation="delete",
        key="old_key",
        version=5,
    )
    assert "DEL" in result
    
    # TOOL (from key prefix)
    result = format_event_pretty(
        timestamp=1770488464,
        agent_id="agent-1",
        operation="write",
        key="tool/search",
        version=6,
        value={"query": "test"},
    )
    assert "TOOL" in result
    
    # NOTE (from key prefix)
    result = format_event_pretty(
        timestamp=1770488464,
        agent_id="agent-1",
        operation="write",
        key="note/checkpoint",
        version=7,
        value="Starting phase 2",
    )
    assert "NOTE" in result
    
    # FINAL (from key prefix)
    result = format_event_pretty(
        timestamp=1770488464,
        agent_id="agent-1",
        operation="write",
        key="final/answer",
        version=8,
        value="The answer is 42",
    )
    assert "FINAL" in result


def test_format_event_pretty_long_agent_id():
    """Test agent ID truncation."""
    result = format_event_pretty(
        timestamp=1770488464,
        agent_id="very-long-agent-identifier-that-needs-truncation",
        operation="write",
        key="test",
        version=1,
    )
    
    # Agent ID should be truncated with ellipsis
    assert "very-long-agent" in result
    assert "..." in result


def test_format_event_pretty_namespace():
    """Test namespace display."""
    # Default namespace should not appear
    result = format_event_pretty(
        timestamp=1770488464,
        agent_id="agent-1",
        operation="write",
        key="test",
        version=1,
        namespace="default",
    )
    assert "ns=" not in result
    
    # Non-default namespace should appear
    result = format_event_pretty(
        timestamp=1770488464,
        agent_id="agent-1",
        operation="write",
        key="test",
        version=1,
        namespace="custom",
    )
    assert "ns=custom" in result


def test_format_event_verbose():
    """Test verbose event formatting."""
    result = format_event_verbose(
        timestamp=1770488464,
        agent_id="research-1",
        operation="write",
        key="context",
        version=3,
        txn_id="a3f7b2d1-4c8e-4f12-9a8b-3d7e5c2f8a4b",
        event_id=42,
        value={"topic": "databases", "sources": ["paper1", "paper2"]},
    )
    
    # Check header line
    assert "18:21:04Z" in result
    assert "agent=research-1" in result
    assert "v=3" in result
    assert "txn=a3f7b2d1" in result  # Truncated txn_id
    assert "event=42" in result
    
    # Check payload
    assert "payload:" in result
    assert "databases" in result
    assert "paper1" in result


def test_format_event_json():
    """Test JSON event formatting."""
    event_data = {
        "timestamp": "2026-02-07T12:31:04Z",
        "namespace": "default",
        "agent_id": "research-1",
        "key": "context",
        "version": 3,
        "operation": "write",
        "txn_id": "a3f7b2d1",
        "event_id": 42,
        "value": {"topic": "databases"},
    }
    
    result = format_event_json(event_data)
    
    # Should be valid JSON
    import json
    parsed = json.loads(result)
    assert parsed["agent_id"] == "research-1"
    assert parsed["version"] == 3
    assert parsed["value"]["topic"] == "databases"
    
    # Should be single line (no newlines)
    assert "\n" not in result


def test_format_event_json_error_handling():
    """Test JSON formatting with unprintable data."""
    # Create an event with unprintable data
    class Unprintable:
        pass
    
    event_data = {
        "event_id": 99,
        "bad_field": Unprintable(),
    }
    
    result = format_event_json(event_data)
    
    # Should produce error JSON instead of crashing
    import json
    parsed = json.loads(result)
    assert "error" in parsed
    assert parsed["error"] == "serialization_failed"


def test_formatting_determinism():
    """Test that formatting is deterministic."""
    # Same input should always produce same output
    inputs = [
        (1770488464, "agent-1", "write", "key1", 1, {"a": 1, "b": 2}),
        (1770488464, "agent-1", "write", "key1", 1, {"a": 1, "b": 2}),
    ]
    
    results = [format_event_pretty(*inp) for inp in inputs]
    
    # Both should be identical
    assert results[0] == results[1]


def test_no_protobuf_types_exposed():
    """
    Ensure formatting functions work with pure Python types.
    No protobuf dependencies should be required.
    """
    # All these should work with standard Python types
    assert format_ts(1770488464) == "18:21:04Z"
    assert format_key("test") == "test"
    assert format_value_summary("test") == '"test"'
    
    result = format_event_pretty(
        timestamp=1770488464,
        agent_id="agent",
        operation="write",
        key="key",
        version=1,
        value={"data": "value"},
    )
    assert isinstance(result, str)
    assert len(result) > 0
