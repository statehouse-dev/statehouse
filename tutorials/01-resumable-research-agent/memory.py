"""
Memory management for the research agent.

This module provides a clean abstraction over Statehouse
for storing and retrieving agent state.
"""

from typing import Any, Dict, Optional
from statehouse import Statehouse


class AgentMemory:
    """
    Memory abstraction for agent state management.

    Provides simple methods for storing and retrieving:
    - Task definitions
    - Step results
    - Progress checkpoints
    - Final answers
    """

    def __init__(self, agent_id: str, client: Statehouse):
        """
        Initialize agent memory.

        Args:
            agent_id: Unique agent identifier
            client: Statehouse client instance
        """
        self.agent_id = agent_id
        self.client = client
        self.namespace = "default"

    def save_task(self, task: str) -> None:
        """
        Store the research task.

        Args:
            task: Task description
        """
        with self.client.begin_transaction() as tx:
            tx.write(agent_id=self.agent_id, key="task", value={"description": task})

    def get_task(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve the stored task.

        Returns:
            Task data dict or None if not found
        """
        result = self.client.get_state(agent_id=self.agent_id, key="task")
        return result.value if result.exists else None

    def save_step(self, step_num: int, step_data: Dict[str, Any]) -> None:
        """
        Store results from a research step.

        Args:
            step_num: Step number (1-indexed)
            step_data: Step results and metadata
        """
        key = f"step/{step_num:03d}"

        with self.client.begin_transaction() as tx:
            tx.write(agent_id=self.agent_id, key=key, value=step_data)

    def get_step(self, step_num: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve results from a specific step.

        Args:
            step_num: Step number to retrieve

        Returns:
            Step data dict or None if not found
        """
        key = f"step/{step_num:03d}"

        result = self.client.get_state(agent_id=self.agent_id, key=key)
        return result.value if result.exists else None

    def save_progress(self, completed_steps: int) -> None:
        """
        Save progress checkpoint.

        Args:
            completed_steps: Number of steps completed
        """
        with self.client.begin_transaction() as tx:
            tx.write(
                agent_id=self.agent_id,
                key="progress",
                value={"completed_steps": completed_steps},
            )

    def load_progress(self) -> Dict[str, Any]:
        """
        Load progress checkpoint.

        Returns:
            Progress data dict (defaults to 0 steps if not found)
        """
        result = self.client.get_state(agent_id=self.agent_id, key="progress")

        if result.exists and result.value:
            return result.value

        return {"completed_steps": 0}

    def save_answer(self, answer: str, metadata: Dict[str, Any]) -> None:
        """
        Store final answer with provenance.

        Args:
            answer: Final answer string
            metadata: Additional metadata (task, steps, etc.)
        """
        with self.client.begin_transaction() as tx:
            tx.write(
                agent_id=self.agent_id,
                key="answer",
                value={"answer": answer, "metadata": metadata},
            )

    def get_answer(self) -> Optional[str]:
        """
        Retrieve final answer if it exists.

        Returns:
            Answer string or None if not found
        """
        result = self.client.get_state(agent_id=self.agent_id, key="answer")

        if result.exists and result.value:
            return result.value.get("answer")

        return None

    def list_all_keys(self) -> list[str]:
        """
        List all keys stored for this agent.

        Returns:
            List of key names
        """
        return self.client.list_keys(agent_id=self.agent_id)

    def get_all_steps(self) -> list[Dict[str, Any]]:
        """
        Retrieve all step results.

        Returns:
            List of step data dicts, ordered by step number
        """
        # List keys with step/ prefix
        results = self.client.scan_prefix(agent_id=self.agent_id, prefix="step/")

        # Extract values and sort by step number
        steps = []
        for result in results:
            if result.exists and result.value:
                steps.append(result.value)

        return steps
