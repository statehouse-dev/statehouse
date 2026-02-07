"""
Agent memory management using Statehouse.

This module provides high-level abstractions for storing agent state,
including sessions, steps, tool calls, and answers.
Uses the synchronous Statehouse client API.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from statehouse import Statehouse


@dataclass
class SessionEvent:
    """One event in a session replay (key, value, timestamp, operation type)."""

    key: str
    value: Optional[Dict[str, Any]]
    timestamp: str
    operation_name: str


class AgentMemory:
    """
    Memory management for an AI agent.

    Provides methods to:
    - Create and manage sessions
    - Store reasoning steps
    - Store tool calls and results
    - Store final answers with provenance
    - Replay session history
    """

    def __init__(self, client: Statehouse, agent_id: str, namespace: str = "default"):
        self.client = client
        self.agent_id = agent_id
        self.namespace = namespace

    def create_session(self, session_id: str) -> None:
        """
        Create a new session.

        Args:
            session_id: Unique session identifier
        """
        with self.client.begin_transaction(namespace=self.namespace) as tx:
            tx.write(
                agent_id=self.agent_id,
                key=f"session:{session_id}",
                value={
                    "session_id": session_id,
                    "created_at": datetime.now().isoformat(),
                    "status": "active",
                    "step_count": 0,
                },
            )

    def get_last_session(self) -> Optional[Dict[str, Any]]:
        """
        Get the last active session for this agent.

        Returns:
            Session data if found, None otherwise
        """
        keys = self.client.list_keys(
            agent_id=self.agent_id,
            namespace=self.namespace,
        )
        # Session metadata keys are exactly "session:{session_id}" (two parts)
        session_keys = [
            k for k in keys if k.startswith("session:") and len(k.split(":")) == 2
        ]
        if not session_keys:
            return None
        session_keys.sort(reverse=True)
        last_key = session_keys[0]
        result = self.client.get_state(
            agent_id=self.agent_id,
            key=last_key,
            namespace=self.namespace,
        )
        if result.exists and result.value:
            return result.value
        return None

    def update_session_progress(
        self,
        session_id: str,
        step_count: int,
        last_step: str,
    ) -> None:
        """Update session progress."""
        with self.client.begin_transaction(namespace=self.namespace) as tx:
            tx.write(
                agent_id=self.agent_id,
                key=f"session:{session_id}",
                value={
                    "session_id": session_id,
                    "step_count": step_count,
                    "last_step": last_step,
                    "updated_at": datetime.now().isoformat(),
                    "status": "active",
                },
            )

    def store_question(self, session_id: str, question: str) -> None:
        """Store the research question for a session."""
        with self.client.begin_transaction(namespace=self.namespace) as tx:
            tx.write(
                agent_id=self.agent_id,
                key=f"session:{session_id}:question",
                value={
                    "session_id": session_id,
                    "question": question,
                    "timestamp": datetime.now().isoformat(),
                },
            )

    def store_plan(self, session_id: str, plan: Dict[str, Any]) -> None:
        """Store the research plan for a session."""
        with self.client.begin_transaction(namespace=self.namespace) as tx:
            tx.write(
                agent_id=self.agent_id,
                key=f"session:{session_id}:plan",
                value={
                    "session_id": session_id,
                    "plan": plan,
                    "timestamp": datetime.now().isoformat(),
                },
            )

    def store_step(
        self,
        session_id: str,
        step_number: int,
        step_data: Dict[str, Any],
    ) -> None:
        """Store a reasoning step."""
        with self.client.begin_transaction(namespace=self.namespace) as tx:
            tx.write(
                agent_id=self.agent_id,
                key=f"session:{session_id}:step:{step_number:04d}",
                value={
                    "session_id": session_id,
                    "step_number": step_number,
                    "timestamp": datetime.now().isoformat(),
                    **step_data,
                },
            )

    def store_tool_result(
        self,
        session_id: str,
        step_number: int,
        tool_name: str,
        args: Dict[str, Any],
        result: Dict[str, Any],
    ) -> None:
        """Store a tool call and its result."""
        with self.client.begin_transaction(namespace=self.namespace) as tx:
            tx.write(
                agent_id=self.agent_id,
                key=f"session:{session_id}:tool_result:{step_number:04d}",
                value={
                    "session_id": session_id,
                    "step_number": step_number,
                    "tool": tool_name,
                    "args": args,
                    "result": result,
                    "timestamp": datetime.now().isoformat(),
                },
            )

    def store_answer(
        self,
        session_id: str,
        answer: Dict[str, Any],
        provenance: Dict[str, Any],
    ) -> None:
        """Store the final answer with full provenance."""
        with self.client.begin_transaction(namespace=self.namespace) as tx:
            tx.write(
                agent_id=self.agent_id,
                key=f"session:{session_id}:answer",
                value={
                    "session_id": session_id,
                    "answer": answer,
                    "provenance": provenance,
                    "timestamp": datetime.now().isoformat(),
                },
            )
            tx.write(
                agent_id=self.agent_id,
                key=f"session:{session_id}",
                value={
                    "session_id": session_id,
                    "status": "complete",
                    "completed_at": datetime.now().isoformat(),
                },
            )

    def replay_session(self, session_id: str) -> List[SessionEvent]:
        """
        Replay all events for a session in chronological order.

        Returns:
            List of SessionEvent (key, value, timestamp, operation_name).
        """
        events: List[SessionEvent] = []
        prefix = f"session:{session_id}"
        for ev in self.client.replay(
            agent_id=self.agent_id,
            namespace=self.namespace,
        ):
            ts_str = datetime.fromtimestamp(ev.commit_ts / 1000.0).isoformat()
            for op in ev.operations:
                if op.key.startswith(prefix) or session_id in op.key:
                    events.append(
                        SessionEvent(
                            key=op.key,
                            value=op.value,
                            timestamp=ts_str,
                            operation_name="Write"
                            if op.value is not None
                            else "Delete",
                        )
                    )
        return events

    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of a session."""
        session_result = self.client.get_state(
            agent_id=self.agent_id,
            key=f"session:{session_id}",
            namespace=self.namespace,
        )
        if not session_result.exists or not session_result.value:
            return None
        session_data = session_result.value
        question_result = self.client.get_state(
            agent_id=self.agent_id,
            key=f"session:{session_id}:question",
            namespace=self.namespace,
        )
        answer_result = self.client.get_state(
            agent_id=self.agent_id,
            key=f"session:{session_id}:answer",
            namespace=self.namespace,
        )
        return {
            "session": session_data,
            "question": question_result.value if question_result.exists else None,
            "answer": answer_result.value if answer_result.exists else None,
        }
