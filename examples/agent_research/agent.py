#!/usr/bin/env python3
"""
Reference research agent implementation.

Demonstrates how an AI agent stores state, memory, and tool calls in Statehouse.
The agent can crash and resume from its last known state.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../python"))

from statehouse import Statehouse
from memory import AgentMemory
from tools import ToolRegistry, SearchTool, CalculatorTool, WriteFileTool


class ResearchAgent:
    """
    A research agent that stores all state in Statehouse.
    
    The agent:
    - Stores every reasoning step
    - Stores tool calls and their outputs
    - Stores final answers with provenance
    - Can resume from crashes
    """
    
    def __init__(
        self,
        agent_id: str,
        statehouse_addr: str = "localhost:50051",
        namespace: str = "default"
    ):
        self.agent_id = agent_id
        self.namespace = namespace
        self.client = Statehouse(url=statehouse_addr)
        self.memory = AgentMemory(self.client, agent_id, namespace)
        self.tools = ToolRegistry()
        
        # Register available tools
        self.tools.register(SearchTool())
        self.tools.register(CalculatorTool())
        self.tools.register(WriteFileTool())
        
        # Session state
        self.session_id = None
        self.step_count = 0
        
    def initialize(self):
        """Initialize the agent and check for resumable sessions."""
        last_session = self.memory.get_last_session()
        if last_session:
            print(f"[RESUME] Found previous session: {last_session['session_id']}")
            print(f"[RESUME] Last step: {last_session.get('last_step', 'N/A')}")
            response = input("Resume from previous session? (y/n): ")
            if response.lower() == "y":
                self.session_id = last_session["session_id"]
                self.step_count = last_session.get("step_count", 0)
                print(f"[RESUME] Continuing session {self.session_id} from step {self.step_count}")
                return
        self.session_id = f"session-{int(time.time())}"
        self.memory.create_session(self.session_id)
        print(f"[START] New session: {self.session_id}")
    
    async def research(self, question: str) -> Dict[str, Any]:
        """
        Research a question using available tools.
        
        Args:
            question: The research question to answer
            
        Returns:
            Dict containing the answer and provenance
        """
        print(f"\n[QUESTION] {question}")
        
        self.memory.store_question(self.session_id, question)
        plan = await self._generate_plan(question)
        self.memory.store_plan(self.session_id, plan)
        print(f"[PLAN] {len(plan['steps'])} steps planned")
        
        # Execute plan
        results = []
        for i, step in enumerate(plan['steps'], 1):
            self.step_count += 1
            
            print(f"\n[STEP {self.step_count}] {step['action']}")
            
            self.memory.store_step(self.session_id, self.step_count, step)
            if step["type"] == "tool":
                result = await self._execute_tool(step["tool"], step.get("args", {}))
                results.append(result)
                self.memory.store_tool_result(
                    self.session_id,
                    self.step_count,
                    step["tool"],
                    step.get("args", {}),
                    result,
                )
                print(f"[RESULT] {result.get('summary', result)}")
            self.memory.update_session_progress(
                self.session_id, self.step_count, step["action"]
            )
        
        # Generate final answer (mock LLM)
        answer = await self._synthesize_answer(question, results)
        
        self.memory.store_answer(
            self.session_id,
            answer,
            provenance={
                "question": question,
                "steps": self.step_count,
                "tools_used": [s["tool"] for s in plan["steps"] if s["type"] == "tool"],
                "results": results,
            },
        )
        
        print(f"\n[ANSWER] {answer['text']}")
        print(f"[COMPLETE] Session {self.session_id} finished after {self.step_count} steps")
        
        return answer
    
    async def _generate_plan(self, question: str) -> Dict[str, Any]:
        """
        Generate a research plan (mock LLM).
        
        In a real implementation, this would call an LLM to generate a plan.
        For the demo, we create a simple static plan.
        """
        # Mock plan based on keywords
        steps = []
        
        if 'search' in question.lower() or 'find' in question.lower():
            steps.append({
                'type': 'tool',
                'tool': 'search',
                'action': 'Search for relevant information',
                'args': {'query': question}
            })
        
        if any(op in question.lower() for op in ['calculate', 'compute', 'sum', 'multiply']):
            steps.append({
                'type': 'tool',
                'tool': 'calculator',
                'action': 'Perform calculation',
                'args': {'expression': 'extracted_from_question'}
            })
        
        # Always synthesize at the end
        steps.append({
            'type': 'reasoning',
            'action': 'Synthesize final answer',
        })
        
        return {
            'question': question,
            'steps': steps,
            'created_at': datetime.now().isoformat()
        }
    
    async def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return its result."""
        tool = self.tools.get(tool_name)
        if not tool:
            return {'error': f'Tool {tool_name} not found'}
        
        try:
            result = await tool.execute(args)
            return result
        except Exception as e:
            return {'error': str(e)}
    
    async def _synthesize_answer(
        self,
        question: str,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Synthesize final answer from results (mock LLM).
        
        In a real implementation, this would call an LLM to synthesize the answer.
        """
        # Simple mock synthesis
        answer_text = f"Based on the research, here's what I found:\n"
        
        for i, result in enumerate(results, 1):
            if 'error' in result:
                answer_text += f"\n{i}. Error: {result['error']}"
            elif 'summary' in result:
                answer_text += f"\n{i}. {result['summary']}"
            else:
                answer_text += f"\n{i}. {json.dumps(result, indent=2)}"
        
        return {
            'text': answer_text,
            'confidence': 0.85,
            'sources': [r.get('source') for r in results if 'source' in r],
            'created_at': datetime.now().isoformat()
        }
    
    def replay_session(self, session_id: Optional[str] = None):
        """Replay a session's history."""
        sid = session_id or self.session_id
        if not sid:
            print("[ERROR] No session to replay")
            return
        print(f"\n[REPLAY] Replaying session {sid}")
        print("=" * 60)
        events = self.memory.replay_session(sid)
        for event in events:
            try:
                ts = datetime.fromisoformat(event.timestamp.replace("Z", ""))
                ts_str = ts.strftime("%H:%M:%S")
            except Exception:
                ts_str = event.timestamp
            print(f"\n[{ts_str}] {event.operation_name}")
            print(f"  Key: {event.key}")
            if event.value:
                val = event.value
                if isinstance(val, dict):
                    if "step" in event.key:
                        print(f"  Step: {val.get('action', 'N/A')}")
                    elif "tool_result" in event.key:
                        print(f"  Tool: {val.get('tool', 'N/A')}")
                        res = val.get("result", val)
                        print(f"  Result: {res.get('summary', res) if isinstance(res, dict) else res}")
                    elif "answer" in event.key:
                        ans = val.get("answer") or val
                        text = (ans.get("text", "") if isinstance(ans, dict) else str(ans))[:100]
                        print(f"  Answer: {text}...")
                    else:
                        try:
                            val_str = json.dumps(val, indent=2)[:200]
                        except (TypeError, ValueError):
                            val_str = str(val)[:200]
                        print(f"  Value: {val_str}...")
                else:
                    print(f"  Value: {str(val)[:200]}...")
        print("\n" + "=" * 60)
        print(f"[REPLAY] Complete ({len(events)} events)")

    def close(self):
        """Close the Statehouse connection."""
        self.client.close()


async def main():
    """Main entry point for the research agent."""
    
    # Parse command line args
    agent_id = os.environ.get('AGENT_ID', 'agent-research-1')
    statehouse_addr = os.environ.get('STATEHOUSE_ADDR', 'localhost:50051')
    
    # Create agent
    agent = ResearchAgent(agent_id, statehouse_addr)
    
    try:
        agent.initialize()
        print("\n" + "=" * 60)
        print("Research Agent Ready")
        print("Commands:")
        print("  ask <question> - Research a question")
        print("  replay [session_id] - Replay session history")
        print("  quit - Exit")
        print("=" * 60)
        while True:
            try:
                command = input("\n> ").strip()
                if not command:
                    continue
                if command.lower() in ("quit", "exit", "q"):
                    break
                if command.startswith("ask "):
                    question = command[4:].strip()
                    await agent.research(question)
                elif command.startswith("replay"):
                    parts = command.split(maxsplit=1)
                    session_id = parts[1] if len(parts) > 1 else None
                    agent.replay_session(session_id)
                else:
                    print(f"Unknown command: {command}")
            except KeyboardInterrupt:
                print("\n[INTERRUPT] Use 'quit' to exit")
                continue
    finally:
        agent.close()
        print("\n[SHUTDOWN] Agent stopped")


if __name__ == "__main__":
    asyncio.run(main())
