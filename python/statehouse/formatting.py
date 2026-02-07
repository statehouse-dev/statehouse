"""
Output formatting utilities for Statehouse events.

This module provides human-readable formatting for replay events and state values.
All formatters are pure, deterministic, and safe for use in production.
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional


def format_ts(ts: int) -> str:
    """
    Format a Unix timestamp (seconds) to HH:MM:SSZ format (UTC).

    Args:
        ts: Unix timestamp in seconds

    Returns:
        Formatted timestamp string (e.g., "12:31:04Z")
    """
    dt = datetime.utcfromtimestamp(ts)
    return dt.strftime("%H:%M:%SZ")


def format_key(key: str, max_len: int = 48) -> str:
    """
    Format a key for display, truncating if necessary.

    Long path-like keys retain prefix/suffix context.

    Args:
        key: The state key to format
        max_len: Maximum length before truncation (default: 48)

    Returns:
        Formatted key string, possibly truncated with ellipsis
    """
    if len(key) <= max_len:
        return key

    # For path-like keys, preserve structure
    if "/" in key:
        parts = key.split("/")
        if len(parts) > 2:
            # Keep first and last parts, truncate middle
            first = parts[0]
            last = parts[-1]
            available = max_len - len(first) - len(last) - 5  # 5 for "/.../""
            if available > 0:
                return f"{first}/.../{last}"

    # Simple truncation with ellipsis
    return key[: max_len - 3] + "..."


def format_value_summary(value: Any, max_len: int = 120) -> str:
    """
    Format a value for display as a compact summary.

    Handles strings, numbers, booleans, null, lists, and dicts.
    Large structures are summarized rather than displayed in full.

    Args:
        value: The value to format (any JSON-serializable type)
        max_len: Maximum length for the summary (default: 120)

    Returns:
        Formatted summary string
    """
    if value is None:
        return "null"

    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, (int, float)):
        return str(value)

    if isinstance(value, str):
        # Escape newlines and control characters
        escaped = value.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        if len(escaped) <= max_len:
            return f'"{escaped}"'
        return f'"{escaped[: max_len - 6]}..."'

    if isinstance(value, list):
        if len(value) == 0:
            return "[]"

        # Try compact representation first
        try:
            compact = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            if len(compact) <= max_len:
                return compact
        except (TypeError, ValueError):
            pass

        # Summary with preview
        preview_items = []
        for item in value[:2]:
            item_str = format_value_summary(item, max_len=30)
            preview_items.append(item_str)

        if len(value) <= 2:
            return f"[{', '.join(preview_items)}]"
        else:
            return f"[{', '.join(preview_items)}, ...] len={len(value)}"

    if isinstance(value, dict):
        if len(value) == 0:
            return "{}"

        # Try compact JSON first
        try:
            compact = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            if len(compact) <= max_len:
                return compact
        except (TypeError, ValueError):
            pass

        # Summary format: {field1:..., n_fields=N}
        keys = list(value.keys())[:2]
        field_preview = ", ".join(f"{k}:..." for k in keys)

        if len(value) <= 2:
            return f"{{{field_preview}}}"
        else:
            return f"{{{field_preview}, n_fields={len(value)}}}"

    # Fallback for unknown types
    try:
        return str(value)[:max_len]
    except Exception:
        return "<unprintable>"


def format_event_pretty(
    timestamp: int,
    agent_id: str,
    operation: str,
    key: str,
    version: int,
    value: Optional[Any] = None,
    namespace: str = "default",
) -> str:
    """
    Format a replay event in the standard pretty format.

    Format: <HH:MM:SSZ>  agent=<agent_id>  <OP>  key=<key>  v=<version>  <summary>

    Args:
        timestamp: Unix timestamp in seconds
        agent_id: Agent identifier
        operation: Operation type (write, delete, etc.)
        key: State key
        version: Version number
        value: Optional value payload
        namespace: Namespace (only shown if not "default")

    Returns:
        Formatted event string (single line)
    """
    ts_str = format_ts(timestamp)

    # Determine operation label
    op_map = {
        "write": "WRITE",
        "delete": "DEL",
    }

    # Heuristic operation detection from key prefix
    if key.startswith("tool/"):
        op_label = "TOOL"
    elif key.startswith("note/") or key.startswith("annotation/"):
        op_label = "NOTE"
    elif key.startswith("final/") or key.startswith("answer/"):
        op_label = "FINAL"
    else:
        op_label = op_map.get(operation, operation.upper())

    # Format key
    key_str = format_key(key)

    # Format agent ID (truncate if very long)
    agent_str = agent_id if len(agent_id) <= 20 else agent_id[:17] + "..."

    # Build base line
    base = f"{ts_str}  agent={agent_str}  {op_label:<5}  key={key_str:<20}  v={version}"

    # Add summary if value present
    if value is not None:
        summary = format_value_summary(value)
        line = f"{base}  {summary}"
    else:
        line = base

    # Add namespace if not default
    if namespace != "default":
        line = f"{ts_str}  ns={namespace}  {line[len(ts_str) + 2 :]}"

    return line


def format_event_verbose(
    timestamp: int,
    agent_id: str,
    operation: str,
    key: str,
    version: int,
    txn_id: str,
    event_id: int,
    value: Optional[Any] = None,
    namespace: str = "default",
) -> str:
    """
    Format a replay event in verbose format with full details.

    Includes transaction ID, event ID, and full payload.

    Args:
        timestamp: Unix timestamp in seconds
        agent_id: Agent identifier
        operation: Operation type
        key: State key
        version: Version number
        txn_id: Transaction identifier
        event_id: Event sequence number
        value: Optional value payload
        namespace: Namespace

    Returns:
        Multi-line formatted event string
    """
    ts_str = format_ts(timestamp)
    op_label = operation.upper()
    key_str = format_key(key)
    agent_str = agent_id if len(agent_id) <= 20 else agent_id[:17] + "..."

    # Truncate txn_id for display
    txn_short = txn_id[:12] if len(txn_id) > 12 else txn_id

    header = (
        f"{ts_str}  agent={agent_str}  {op_label:<5}  key={key_str}  v={version}  txn={txn_short}  event={event_id}"
    )

    if namespace != "default":
        header = f"{ts_str}  ns={namespace}  {header[len(ts_str) + 2 :]}"

    if value is not None:
        try:
            payload_json = json.dumps(value, ensure_ascii=False, indent=2)
            return f"{header}\n  payload: {payload_json}"
        except (TypeError, ValueError):
            return f"{header}\n  payload: <unprintable>"

    return header


def format_event_json(event_data: Dict[str, Any]) -> str:
    """
    Format an event as a single-line JSON object (JSONL).

    Args:
        event_data: Complete event dictionary

    Returns:
        JSON string (single line)
    """
    try:
        return json.dumps(event_data, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError) as e:
        # Fallback for unprintable data
        return json.dumps(
            {
                "error": "serialization_failed",
                "message": str(e),
                "event_id": event_data.get("event_id"),
            },
            separators=(",", ":"),
        )
