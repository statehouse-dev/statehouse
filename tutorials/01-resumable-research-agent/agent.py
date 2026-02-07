"""
Resumable research agent tutorial implementation.

This agent demonstrates:
- Step-by-step execution with state persistence
- Crash recovery and resume capability
- Tool usage with audit trails
- Replay for debugging and analysis
"""

import time
import argparse
from typing import Optional
from statehouse import Statehouse
from memory import AgentMemory
from tools import ToolRegistry


class ResearchAgent:
    """
    A simple research agent that can resume after crashes.

    The agent executes a task in discrete steps, storing state after
    each step. If it crashes, it can resume from the last checkpoint.
    """

    def __init__(self, agent_id: str, max_steps: int = 5):
        """
        Initialize the research agent.

        Args:
            agent_id: Unique identifier for this agent instance
            max_steps: Maximum number of steps to execute
        """
        self.agent_id = agent_id
        self.max_steps = max_steps
        self.client = Statehouse()
        self.memory = AgentMemory(agent_id=agent_id, client=self.client)
        self.tools = ToolRegistry()
        self.crash_at_step: Optional[int] = None

    def run(self, task: str):
        """
        Run the agent on a new task.

        Args:
            task: The task description
        """
        print("\n=== Starting Research Agent ===")
        print(f"Agent ID: {self.agent_id}")
        print(f"Task: {task}\n")

        # Store the task
        self.memory.save_task(task)

        # Execute steps
        for step_num in range(1, self.max_steps + 1):
            # Check for crash simulation
            if self.crash_at_step and step_num == self.crash_at_step:
                print(f"\n💥 CRASH SIMULATION - Agent stopping at step {step_num}")
                return

            self.execute_step(step_num, task)

            # Save progress checkpoint
            self.memory.save_progress(step_num)

            # Check if we have final answer
            if self.memory.get_answer():
                print("\n=== Task Complete ===")
                final_answer = self.memory.get_answer()
                print(f"Answer: {final_answer}\n")
                break

    def resume(self):
        """
        Resume execution from the last checkpoint.

        This method:
        1. Loads the stored task
        2. Finds the last completed step
        3. Continues execution from the next step
        """
        print("\n=== Resuming Research Agent ===")
        print(f"Agent ID: {self.agent_id}\n")

        # Get task
        task_data = self.memory.get_task()
        if not task_data:
            print("❌ No task found - cannot resume")
            return

        task = task_data.get("description", "")

        # Get last completed step
        progress = self.memory.load_progress()
        last_step = int(progress.get("completed_steps", 0))

        print("Recovered state:")
        print(f"  - Task: {task}")
        print(f"  - Last completed step: {last_step}")
        print(f"  - Resuming from step: {last_step + 1}\n")

        # Check if already complete
        if self.memory.get_answer():
            print("✓ Task already complete")
            final_answer = self.memory.get_answer()
            print(f"Answer: {final_answer}\n")
            return

        # Continue execution
        for step_num in range(last_step + 1, self.max_steps + 1):
            # Check for crash simulation
            if self.crash_at_step and step_num == self.crash_at_step:
                print(f"\n💥 CRASH SIMULATION - Agent stopping at step {step_num}")
                return

            self.execute_step(step_num, task)

            # Save progress checkpoint
            self.memory.save_progress(step_num)

            # Check if we have final answer
            if self.memory.get_answer():
                print("\n=== Task Complete ===")
                final_answer = self.memory.get_answer()
                print(f"Answer: {final_answer}\n")
                break

    def execute_step(self, step_num: int, task: str):
        """
        Execute a single step of the agent's workflow.

        This is a simplified demo that shows different tool usage
        based on keywords in the task.

        Args:
            step_num: Current step number
            task: The task being worked on
        """
        print(f"Step {step_num}: ", end="")

        # Simple heuristic-based execution (in real agents, use LLM)
        task_lower = task.lower()

        if step_num == 1:
            # First step: analyze task
            print("Analyzing task...")
            self.memory.save_step(
                step_num=step_num, step_data={"action": "analyze", "task": task}
            )
            print("  ✓ Stored step state")

        elif step_num == 2:
            # Second step: use appropriate tool
            if any(op in task_lower for op in ["+", "-", "*", "/", "calculate"]):
                print("Using calculator tool")
                # Extract expression (simplified)
                expr = self._extract_math_expression(task)
                result = self.tools.call_tool("calculator", expression=expr)

                print(f"  Tool: calculator({expr})")
                print(f"  Result: {result}")

                self.memory.save_step(
                    step_num=step_num,
                    step_data={
                        "action": "tool_call",
                        "tool": "calculator",
                        "args": {"expression": expr},
                        "result": result,
                    },
                )
                print("  ✓ Stored tool call and result")

            elif any(
                kw in task_lower for kw in ["research", "find", "search", "what is"]
            ):
                print("Using search tool")
                query = self._extract_search_query(task)
                results = self.tools.call_tool("search", query=query)

                print(f'  Tool: search("{query}")')
                print(f"  Results: {len(results)} found")

                self.memory.save_step(
                    step_num=step_num,
                    step_data={
                        "action": "tool_call",
                        "tool": "search",
                        "args": {"query": query},
                        "results": results,
                    },
                )
                print("  ✓ Stored tool call and result")

            else:
                print("Analyzing requirements...")
                self.memory.save_step(
                    step_num=step_num,
                    step_data={
                        "action": "analyze",
                        "observations": "Task requires further breakdown",
                    },
                )
                print("  ✓ Stored step state")

        elif step_num == 3:
            # Third step: synthesize information
            print("Synthesizing information...")

            self.memory.save_step(
                step_num=step_num,
                step_data={
                    "action": "synthesize",
                    "based_on": "step_2",
                    "summary": "Prepared answer",
                },
            )
            print("  ✓ Stored step state")

        elif step_num >= 4:
            # Final step: generate answer
            print("Generating final answer")

            # Create answer based on what tools were used
            answer = self._generate_answer(task)

            self.memory.save_answer(
                answer=answer, metadata={"steps_taken": step_num, "task": task}
            )
            print(f"  Answer: {answer[:60]}...")
            print("  ✓ Stored final answer")

    def _extract_math_expression(self, task: str) -> str:
        """Extract math expression from task (simplified)."""
        # Look for pattern like "42 * 137"
        import re

        match = re.search(r"(\d+\s*[+\-*/]\s*\d+)", task)
        if match:
            return match.group(1)
        return "1 + 1"  # Default

    def _extract_search_query(self, task: str) -> str:
        """Extract search query from task (simplified)."""
        # Remove common question words
        task_lower = task.lower()
        for prefix in [
            "research ",
            "find ",
            "search for ",
            "what is ",
            "tell me about ",
        ]:
            if task_lower.startswith(prefix):
                return task[len(prefix) :].strip()
        return task

    def _generate_answer(self, task: str) -> str:
        """Generate final answer based on task and stored results."""
        # Get step 2 data (where tool was likely called)
        step2_data = self.memory.get_step(2)

        if step2_data and step2_data.get("tool") == "calculator":
            result_value = step2_data.get("result", 0)
            # Extract the expression
            import re

            match = re.search(r"(\d+)\s*\*\s*(\d+)", task)
            if match:
                a, b = int(match.group(1)), int(match.group(2))
                return f"The result of {a} * {b} is {int(result_value):,}"
            return f"The result is {result_value}"

        elif step2_data and step2_data.get("tool") == "search":
            results = step2_data.get("results", [])
            count = len(results)
            args = step2_data.get("args") or {}
            query = (
                args.get("query", "the topic")
                if isinstance(args, dict)
                else "the topic"
            )
            return f"Based on {count} sources about {query}, the key findings are: Raft and Paxos are both consensus algorithms used in distributed systems..."

        else:
            return f"Completed analysis of: {task}"

    def close(self):
        """Clean up resources."""
        self.client.close()


def main():
    """Main entry point for the tutorial."""
    parser = argparse.ArgumentParser(description="Resumable Research Agent Tutorial")
    parser.add_argument("--task", type=str, help="Task to execute")
    parser.add_argument(
        "--resume", action="store_true", help="Resume from last checkpoint"
    )
    parser.add_argument(
        "--agent-id",
        type=str,
        default="tutorial-agent-1",
        help="Agent ID (default: tutorial-agent-1)",
    )
    parser.add_argument("--crash-at-step", type=int, help="Simulate crash at this step")
    parser.add_argument(
        "--reset", action="store_true", help="Reset/clear all agent state"
    )
    parser.add_argument(
        "--replay", action="store_true", help="Show complete replay of agent history"
    )

    args = parser.parse_args()

    # Generate agent ID if needed
    agent_id = args.agent_id

    # Handle reset command
    if args.reset:
        print(f"\n=== Resetting Agent: {agent_id} ===\n")
        client = Statehouse()

        # Delete all keys for this agent
        try:
            keys = client.list_keys(agent_id=agent_id)
            if keys:
                print(f"Deleting {len(keys)} keys...")
                with client.begin_transaction() as txn:
                    for key in keys:
                        txn.delete(agent_id=agent_id, key=key)
                print("✓ State cleared")
            else:
                print("No state to clear")
        finally:
            client.close()
        return

    # Handle replay command
    if args.replay:
        print(f"\n=== Replay: {agent_id} ===\n")
        client = Statehouse()
        try:
            events = list(client.replay(agent_id=agent_id))
            if not events:
                print("No events to replay")
            else:
                print(f"Replaying {len(events)} events:\n")
                for event in events:
                    # Format timestamp
                    ts = time.strftime("%H:%M:%SZ", time.gmtime(event.commit_ts))
                    
                    # Each event may have multiple operations
                    for op in event.operations:
                        # Format operation
                        op_type = "DEL" if op.value is None else "WRITE"
                        # Format value
                        value_str = ""
                        if op.value:
                            value_str = str(op.value)[:80]
                            if len(str(op.value)) > 80:
                                value_str += "..."

                        print(
                            f"{ts}  agent={event.agent_id}  {op_type:6}  key={op.key:20}  {value_str}"
                        )
        finally:
            client.close()
        return

    # Create agent
    agent = ResearchAgent(agent_id=agent_id)

    # Set crash simulation if requested
    if args.crash_at_step:
        agent.crash_at_step = args.crash_at_step

    try:
        if args.resume:
            # Resume mode
            agent.resume()
        elif args.task:
            # New task mode
            agent.run(args.task)
        else:
            print("Error: Must provide --task, --resume, --reset, or --replay")
            parser.print_help()
    finally:
        agent.close()


if __name__ == "__main__":
    main()
