"""
Human-in-the-loop approval agent tutorial.

This agent demonstrates:
- Audit trails for every decision
- Explainability - every action can be traced
- Human-in-the-loop workflows with approval gates
- Post-hoc inspection and replay

The workflow:
1. Receive a request
2. Analyze the request (mock LLM)
3. Generate a proposal
4. Request human approval
5. Wait for decision
6. Apply or abort based on decision
"""

import argparse
import time
from dataclasses import dataclass
from typing import Any, Optional

from statehouse import Statehouse

from human import request_human_approval, ApprovalDecision


# Keys used in Statehouse (documented for auditability)
KEY_REQUEST = "request"
KEY_ANALYSIS = "analysis"
KEY_PROPOSAL = "proposal"
KEY_APPROVAL_REQUEST = "approval_request"
KEY_HUMAN_DECISION = "human_decision"
KEY_FINAL_ACTION = "final_action"
KEY_WORKFLOW_STATE = "workflow_state"


@dataclass
class WorkflowState:
    """Tracks the current state of the approval workflow."""

    step: str  # Current step name
    status: str  # pending, waiting_approval, approved, rejected, completed
    started_at: float  # Unix timestamp
    updated_at: float  # Unix timestamp

    @classmethod
    def new(cls) -> "WorkflowState":
        """Create a new workflow state."""
        now = time.time()
        return cls(step="init", status="pending", started_at=now, updated_at=now)

    def advance(self, step: str, status: str = "pending") -> "WorkflowState":
        """Advance to a new step."""
        return WorkflowState(
            step=step,
            status=status,
            started_at=self.started_at,
            updated_at=time.time(),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "step": self.step,
            "status": self.status,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowState":
        """Create from dictionary."""
        return cls(
            step=data["step"],
            status=data["status"],
            started_at=data["started_at"],
            updated_at=data["updated_at"],
        )


class ApprovalAgent:
    """
    An agent that requires human approval before taking actions.

    This demonstrates a typical enterprise workflow where:
    - AI analyzes and proposes actions
    - Humans approve or reject proposals
    - All decisions are auditable
    - The workflow survives restarts
    """

    def __init__(self, agent_id: str):
        """
        Initialize the approval agent.

        Args:
            agent_id: Unique identifier for this agent instance
        """
        self.agent_id = agent_id
        self.client = Statehouse()
        self.crash_before_approval = False
        self.crash_after_approval = False

    def run(self, request: dict[str, Any]) -> Optional[dict[str, Any]]:
        """
        Run the approval workflow on a request.

        Args:
            request: The request to process (e.g., refund, access change, etc.)

        Returns:
            Final action result, or None if aborted/crashed
        """
        print("\n=== Human-in-the-loop Approval Agent ===")
        print(f"Agent ID: {self.agent_id}")
        print(f"Request: {request.get('description', 'No description')}\n")

        # Check if we're resuming
        state = self._load_workflow_state()
        if state and state.step != "init":
            print(f"[RESUME] Resuming from step: {state.step} (status: {state.status})")
            return self._resume_from_state(state, request)

        # Start fresh workflow
        return self._execute_workflow(request)

    def _execute_workflow(self, request: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Execute the full workflow from the beginning."""
        # Step 1: Store request
        print("[STEP 1] Recording request...")
        self._persist_request(request)

        # Step 2: Analyze request
        print("[STEP 2] Analyzing request...")
        analysis = self._analyze_request(request)
        self._persist_analysis(analysis)
        print(f"  Analysis: {analysis.get('summary', 'N/A')}")

        # Step 3: Generate proposal
        print("[STEP 3] Generating proposal...")
        proposal = self._generate_proposal(request, analysis)
        self._persist_proposal(proposal)
        print(f"  Proposal: {proposal.get('action', 'N/A')}")

        # Step 4: Request approval
        print("[STEP 4] Requesting human approval...")
        self._persist_approval_request(proposal)

        # Crash simulation before approval
        if self.crash_before_approval:
            print("\n💥 CRASH SIMULATION - Before approval")
            print("   Run with --resume to continue after restart\n")
            return None

        # Step 5: Get human decision
        print("[STEP 5] Waiting for human decision...")
        decision = request_human_approval(proposal)
        self._persist_human_decision(decision)
        print(f"  Decision: {decision.approved and 'APPROVED' or 'REJECTED'}")
        if decision.reason:
            print(f"  Reason: {decision.reason}")

        # Crash simulation after approval
        if self.crash_after_approval:
            print("\n💥 CRASH SIMULATION - After approval")
            print("   Run with --resume to continue after restart\n")
            return None

        # Step 6: Apply or abort
        if decision.approved:
            print("[STEP 6] Applying final action...")
            result = self._apply_action(proposal)
            self._persist_final_action(result, approved=True)
            print(f"  Result: {result.get('status', 'N/A')}")
            print("\n=== Workflow Complete ===")
            return result
        else:
            print("[STEP 6] Aborting action...")
            result = {"status": "aborted", "reason": decision.reason}
            self._persist_final_action(result, approved=False)
            print("\n=== Workflow Aborted ===")
            return result

    def _resume_from_state(
        self, state: WorkflowState, request: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Resume workflow from a saved state."""
        # Load existing data
        stored_request = self._load_key(KEY_REQUEST)
        analysis = self._load_key(KEY_ANALYSIS)
        proposal = self._load_key(KEY_PROPOSAL)
        decision_data = self._load_key(KEY_HUMAN_DECISION)

        # Resume based on current step
        if state.step == "request" or state.step == "analysis":
            # Need to continue from analysis
            print("  Resuming from analysis step...")
            if not analysis:
                analysis = self._analyze_request(stored_request or request)
                self._persist_analysis(analysis)
            return self._continue_from_proposal(stored_request or request, analysis)

        elif state.step == "proposal" or state.step == "approval_request":
            # Waiting for human approval
            print("  Resuming from approval step...")
            if state.status == "waiting_approval":
                print("[STEP 5] Waiting for human decision...")
                decision = request_human_approval(proposal)
                self._persist_human_decision(decision)
                return self._complete_workflow(proposal, decision)
            return self._continue_from_approval(proposal)

        elif state.step == "human_decision":
            # Have decision, need to apply
            print("  Resuming from action step...")
            decision = ApprovalDecision(
                approved=decision_data.get("approved", False),
                reason=decision_data.get("reason"),
                decided_by=decision_data.get("decided_by"),
                decided_at=decision_data.get("decided_at"),
            )
            return self._complete_workflow(proposal, decision)

        elif state.step == "final_action":
            # Already complete
            print("  Workflow already complete.")
            final = self._load_key(KEY_FINAL_ACTION)
            return final

        return None

    def _continue_from_proposal(
        self, request: dict[str, Any], analysis: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Continue workflow from proposal generation."""
        print("[STEP 3] Generating proposal...")
        proposal = self._generate_proposal(request, analysis)
        self._persist_proposal(proposal)
        print(f"  Proposal: {proposal.get('action', 'N/A')}")
        return self._continue_from_approval(proposal)

    def _continue_from_approval(
        self, proposal: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Continue workflow from approval request."""
        print("[STEP 4] Requesting human approval...")
        self._persist_approval_request(proposal)

        print("[STEP 5] Waiting for human decision...")
        decision = request_human_approval(proposal)
        self._persist_human_decision(decision)
        return self._complete_workflow(proposal, decision)

    def _complete_workflow(
        self, proposal: dict[str, Any], decision: ApprovalDecision
    ) -> dict[str, Any]:
        """Complete the workflow with final action."""
        print(f"  Decision: {decision.approved and 'APPROVED' or 'REJECTED'}")

        if decision.approved:
            print("[STEP 6] Applying final action...")
            result = self._apply_action(proposal)
            self._persist_final_action(result, approved=True)
            print(f"  Result: {result.get('status', 'N/A')}")
            print("\n=== Workflow Complete ===")
            return result
        else:
            print("[STEP 6] Aborting action...")
            result = {"status": "aborted", "reason": decision.reason}
            self._persist_final_action(result, approved=False)
            print("\n=== Workflow Aborted ===")
            return result

    # -------------------------------------------------------------------------
    # Mock LLM functions (replace with real LLM in production)
    # -------------------------------------------------------------------------

    def _analyze_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze the request (mock LLM).

        In production, this would call an LLM to understand the request.
        """
        req_type = request.get("type", "unknown")
        description = request.get("description", "")

        # Deterministic mock analysis
        if req_type == "refund":
            return {
                "summary": "Customer refund request",
                "category": "financial",
                "risk_level": "medium",
                "amount": request.get("amount", 0),
                "recommendation": "approve"
                if request.get("amount", 0) < 500
                else "review",
                "factors": [
                    "Customer history: good standing",
                    "Product category: electronics",
                    "Return window: within policy",
                ],
            }
        elif req_type == "access":
            return {
                "summary": "Access permission change request",
                "category": "security",
                "risk_level": "high",
                "target_resource": request.get("resource", "unknown"),
                "recommendation": "manual_review",
                "factors": [
                    "Scope: admin-level access",
                    "Duration: permanent",
                    "Justification: provided",
                ],
            }
        else:
            return {
                "summary": f"Request analysis: {description[:50]}",
                "category": "general",
                "risk_level": "low",
                "recommendation": "approve",
                "factors": ["Standard request type"],
            }

    def _generate_proposal(
        self, request: dict[str, Any], analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Generate an action proposal based on analysis.

        In production, this would use an LLM to craft the proposal.
        """
        req_type = request.get("type", "unknown")

        if req_type == "refund":
            return {
                "action": "process_refund",
                "parameters": {
                    "customer_id": request.get("customer_id", "unknown"),
                    "amount": request.get("amount", 0),
                    "method": "original_payment_method",
                },
                "justification": f"Based on analysis: {analysis.get('summary', 'N/A')}",
                "risk_level": analysis.get("risk_level", "unknown"),
                "reversible": True,
            }
        elif req_type == "access":
            return {
                "action": "grant_access",
                "parameters": {
                    "user_id": request.get("user_id", "unknown"),
                    "resource": request.get("resource", "unknown"),
                    "level": request.get("level", "read"),
                },
                "justification": f"Based on analysis: {analysis.get('summary', 'N/A')}",
                "risk_level": analysis.get("risk_level", "unknown"),
                "reversible": True,
            }
        else:
            return {
                "action": "process_request",
                "parameters": request,
                "justification": f"Based on analysis: {analysis.get('summary', 'N/A')}",
                "risk_level": analysis.get("risk_level", "unknown"),
                "reversible": False,
            }

    def _apply_action(self, proposal: dict[str, Any]) -> dict[str, Any]:
        """
        Apply the proposed action.

        In production, this would execute the actual action.
        """
        action = proposal.get("action", "unknown")

        # Mock execution
        return {
            "status": "success",
            "action_taken": action,
            "parameters_used": proposal.get("parameters", {}),
            "executed_at": time.time(),
            "confirmation_id": f"ACT-{int(time.time())}",
        }

    # -------------------------------------------------------------------------
    # State persistence (each step = one event in Statehouse)
    # -------------------------------------------------------------------------

    def _persist_request(self, request: dict[str, Any]) -> None:
        """Persist the initial request."""
        state = WorkflowState.new().advance("request", "pending")
        with self.client.begin_transaction() as tx:
            tx.write(agent_id=self.agent_id, key=KEY_REQUEST, value=request)
            tx.write(
                agent_id=self.agent_id, key=KEY_WORKFLOW_STATE, value=state.to_dict()
            )

    def _persist_analysis(self, analysis: dict[str, Any]) -> None:
        """Persist the analysis output."""
        state = self._load_workflow_state()
        new_state = (state or WorkflowState.new()).advance("analysis", "pending")
        with self.client.begin_transaction() as tx:
            tx.write(agent_id=self.agent_id, key=KEY_ANALYSIS, value=analysis)
            tx.write(
                agent_id=self.agent_id,
                key=KEY_WORKFLOW_STATE,
                value=new_state.to_dict(),
            )

    def _persist_proposal(self, proposal: dict[str, Any]) -> None:
        """Persist the generated proposal."""
        state = self._load_workflow_state()
        new_state = (state or WorkflowState.new()).advance("proposal", "pending")
        with self.client.begin_transaction() as tx:
            tx.write(agent_id=self.agent_id, key=KEY_PROPOSAL, value=proposal)
            tx.write(
                agent_id=self.agent_id,
                key=KEY_WORKFLOW_STATE,
                value=new_state.to_dict(),
            )

    def _persist_approval_request(self, proposal: dict[str, Any]) -> None:
        """Persist the approval request event."""
        state = self._load_workflow_state()
        new_state = (state or WorkflowState.new()).advance(
            "approval_request", "waiting_approval"
        )
        approval_request = {
            "proposal_summary": proposal.get("action", "unknown"),
            "risk_level": proposal.get("risk_level", "unknown"),
            "requested_at": time.time(),
            "status": "pending",
        }
        with self.client.begin_transaction() as tx:
            tx.write(
                agent_id=self.agent_id, key=KEY_APPROVAL_REQUEST, value=approval_request
            )
            tx.write(
                agent_id=self.agent_id,
                key=KEY_WORKFLOW_STATE,
                value=new_state.to_dict(),
            )

    def _persist_human_decision(self, decision: ApprovalDecision) -> None:
        """Persist the human decision verbatim."""
        state = self._load_workflow_state()
        status = "approved" if decision.approved else "rejected"
        new_state = (state or WorkflowState.new()).advance("human_decision", status)
        decision_data = {
            "approved": decision.approved,
            "reason": decision.reason,
            "decided_by": decision.decided_by,
            "decided_at": decision.decided_at,
        }
        with self.client.begin_transaction() as tx:
            tx.write(
                agent_id=self.agent_id, key=KEY_HUMAN_DECISION, value=decision_data
            )
            tx.write(
                agent_id=self.agent_id,
                key=KEY_WORKFLOW_STATE,
                value=new_state.to_dict(),
            )

    def _persist_final_action(self, result: dict[str, Any], approved: bool) -> None:
        """Persist the final action result."""
        state = self._load_workflow_state()
        new_state = (state or WorkflowState.new()).advance("final_action", "completed")
        final_data = {
            "approved": approved,
            "result": result,
            "completed_at": time.time(),
        }
        with self.client.begin_transaction() as tx:
            tx.write(agent_id=self.agent_id, key=KEY_FINAL_ACTION, value=final_data)
            tx.write(
                agent_id=self.agent_id,
                key=KEY_WORKFLOW_STATE,
                value=new_state.to_dict(),
            )

    def _load_workflow_state(self) -> Optional[WorkflowState]:
        """Load the current workflow state."""
        result = self.client.get_state(agent_id=self.agent_id, key=KEY_WORKFLOW_STATE)
        if result.exists and result.value:
            return WorkflowState.from_dict(result.value)
        return None

    def _load_key(self, key: str) -> Optional[dict[str, Any]]:
        """Load a value from Statehouse."""
        result = self.client.get_state(agent_id=self.agent_id, key=key)
        if result.exists and result.value:
            return result.value
        return None

    def close(self) -> None:
        """Clean up resources."""
        self.client.close()


def explain_decision(agent_id: str) -> None:
    """
    Explain why a decision was made, using only stored state.

    This demonstrates post-hoc explainability - we can answer
    "Why did this action happen?" without re-executing anything.
    """
    print(f"\n=== Explaining Decision for Agent: {agent_id} ===\n")

    client = Statehouse()
    try:
        # Load all relevant state
        request = client.get_state(agent_id=agent_id, key=KEY_REQUEST)
        analysis = client.get_state(agent_id=agent_id, key=KEY_ANALYSIS)
        proposal = client.get_state(agent_id=agent_id, key=KEY_PROPOSAL)
        decision = client.get_state(agent_id=agent_id, key=KEY_HUMAN_DECISION)
        final = client.get_state(agent_id=agent_id, key=KEY_FINAL_ACTION)

        if not request.exists:
            print("No workflow found for this agent.")
            return

        # Build explanation
        print("1. ORIGINAL REQUEST:")
        if request.value:
            print(f"   Type: {request.value.get('type', 'N/A')}")
            print(f"   Description: {request.value.get('description', 'N/A')}")

        print("\n2. AI ANALYSIS:")
        if analysis.exists and analysis.value:
            print(f"   Summary: {analysis.value.get('summary', 'N/A')}")
            print(f"   Risk Level: {analysis.value.get('risk_level', 'N/A')}")
            print(f"   Recommendation: {analysis.value.get('recommendation', 'N/A')}")
            factors = analysis.value.get("factors", [])
            if factors:
                print("   Factors:")
                for f in factors:
                    print(f"     - {f}")

        print("\n3. PROPOSED ACTION:")
        if proposal.exists and proposal.value:
            print(f"   Action: {proposal.value.get('action', 'N/A')}")
            print(f"   Justification: {proposal.value.get('justification', 'N/A')}")
            print(f"   Reversible: {proposal.value.get('reversible', 'N/A')}")

        print("\n4. HUMAN DECISION:")
        if decision.exists and decision.value:
            approved = decision.value.get("approved", False)
            print(f"   Approved: {'Yes' if approved else 'No'}")
            print(f"   Decided by: {decision.value.get('decided_by', 'N/A')}")
            if decision.value.get("reason"):
                print(f"   Reason: {decision.value.get('reason')}")

        print("\n5. FINAL OUTCOME:")
        if final.exists and final.value:
            result = final.value.get("result", {})
            print(f"   Status: {result.get('status', 'N/A')}")
            if result.get("confirmation_id"):
                print(f"   Confirmation ID: {result.get('confirmation_id')}")
            if result.get("reason"):
                print(f"   Reason: {result.get('reason')}")

        print("\n=== End of Explanation ===")

    finally:
        client.close()


def replay_workflow(agent_id: str, verbose: bool = False) -> None:
    """Display the complete replay of the workflow."""
    print(f"\n=== Replay: {agent_id} ===\n")

    client = Statehouse()
    try:
        events = list(client.replay(agent_id=agent_id))
        if not events:
            print("No events to replay.")
            return

        print(f"Replaying {len(events)} events:\n")
        for event in events:
            ts = time.strftime("%H:%M:%SZ", time.gmtime(event.commit_ts))

            for op in event.operations:
                op_type = "DEL" if op.value is None else "WRITE"
                value_str = ""
                if op.value:
                    if verbose:
                        import json

                        value_str = json.dumps(op.value, indent=2)
                    else:
                        value_str = str(op.value)[:80]
                        if len(str(op.value)) > 80:
                            value_str += "..."

                print(
                    f"{ts}  agent={event.agent_id}  {op_type:6}  key={op.key:20}  {value_str}"
                )
    finally:
        client.close()


def reset_agent(agent_id: str) -> None:
    """Clear all state for an agent."""
    print(f"\n=== Resetting Agent: {agent_id} ===\n")

    client = Statehouse()
    try:
        keys = client.list_keys(agent_id=agent_id)
        if keys:
            print(f"Deleting {len(keys)} keys...")
            with client.begin_transaction() as tx:
                for key in keys:
                    tx.delete(agent_id=agent_id, key=key)
            print("State cleared.")
        else:
            print("No state to clear.")
    finally:
        client.close()


def main() -> None:
    """Main entry point for the tutorial."""
    parser = argparse.ArgumentParser(
        description="Human-in-the-loop Approval Agent Tutorial"
    )

    # Commands
    parser.add_argument(
        "--refund",
        type=float,
        metavar="AMOUNT",
        help="Process a refund request for the specified amount",
    )
    parser.add_argument(
        "--access",
        type=str,
        metavar="RESOURCE",
        help="Process an access request for the specified resource",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Explain why a decision was made",
    )
    parser.add_argument(
        "--replay",
        action="store_true",
        help="Show complete replay of workflow",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear all agent state",
    )

    # Options
    parser.add_argument(
        "--agent-id",
        type=str,
        default="approval-agent-1",
        help="Agent ID (default: approval-agent-1)",
    )
    parser.add_argument(
        "--crash-before-approval",
        action="store_true",
        help="Simulate crash before approval step",
    )
    parser.add_argument(
        "--crash-after-approval",
        action="store_true",
        help="Simulate crash after approval step",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()
    agent_id = args.agent_id

    # Handle utility commands
    if args.reset:
        reset_agent(agent_id)
        return

    if args.replay:
        replay_workflow(agent_id, verbose=args.verbose)
        return

    if args.explain:
        explain_decision(agent_id)
        return

    # Handle workflow commands
    if args.resume:
        agent = ApprovalAgent(agent_id=agent_id)
        agent.crash_before_approval = args.crash_before_approval
        agent.crash_after_approval = args.crash_after_approval
        try:
            # Load existing request
            stored = agent._load_key(KEY_REQUEST)
            if stored:
                agent.run(stored)
            else:
                print(
                    "No workflow to resume. Start a new one with --refund or --access."
                )
        finally:
            agent.close()
        return

    if args.refund is not None:
        request = {
            "type": "refund",
            "description": f"Customer refund request for ${args.refund:.2f}",
            "amount": args.refund,
            "customer_id": "CUST-12345",
        }
    elif args.access:
        request = {
            "type": "access",
            "description": f"Access request for {args.access}",
            "resource": args.access,
            "user_id": "USER-67890",
            "level": "admin",
        }
    else:
        print(
            "Error: Must provide --refund, --access, --resume, --explain, --replay, or --reset"
        )
        parser.print_help()
        return

    # Execute workflow
    agent = ApprovalAgent(agent_id=agent_id)
    agent.crash_before_approval = args.crash_before_approval
    agent.crash_after_approval = args.crash_after_approval
    try:
        agent.run(request)
    finally:
        agent.close()


if __name__ == "__main__":
    main()
