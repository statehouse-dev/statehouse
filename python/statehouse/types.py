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
