"""
Type definitions for Statehouse SDK
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class StateResult:
    """Result of a state read operation"""

    value: Optional[Dict[str, Any]]
    version: int
    commit_ts: int
    exists: bool


@dataclass
class Operation:
    """A single operation in an event"""

    key: str
    value: Optional[Dict[str, Any]]
    version: int


@dataclass
class ReplayEvent:
    """An event from the replay stream"""

    txn_id: str
    commit_ts: int
    operations: list[Operation]
    namespace: str = "default"
    agent_id: str = ""

    def __repr__(self) -> str:
        """Pretty representation using formatting module."""
        # Import here to avoid circular dependency
        from .formatting import format_event_pretty

        # Format each operation
        lines = []
        for op in self.operations:
            line = format_event_pretty(
                timestamp=self.commit_ts,
                agent_id=self.agent_id,
                operation="write" if op.value is not None else "delete",
                key=op.key,
                version=op.version,
                value=op.value,
                namespace=self.namespace,
            )
            lines.append(line)

        return "\n".join(lines) if lines else f"<ReplayEvent txn_id={self.txn_id}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for structured access."""
        return {
            "txn_id": self.txn_id,
            "commit_ts": self.commit_ts,
            "namespace": self.namespace,
            "agent_id": self.agent_id,
            "operations": [
                {
                    "key": op.key,
                    "value": op.value,
                    "version": op.version,
                }
                for op in self.operations
            ],
        }
