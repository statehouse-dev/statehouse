"""
Human approval simulation module.

This module provides utilities for requesting and recording
human approval decisions. In production, this would integrate
with a proper approval system (Slack, email, web UI, etc.).
"""

import os
import time
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ApprovalDecision:
    """Represents a human approval decision."""

    approved: bool
    reason: Optional[str] = None
    decided_by: str = "human"
    decided_at: float = 0.0

    def __post_init__(self) -> None:
        if self.decided_at == 0.0:
            self.decided_at = time.time()


def request_human_approval(proposal: dict[str, Any]) -> ApprovalDecision:
    """
    Request human approval for a proposal.

    This function supports three modes:
    1. Interactive: Prompts user via stdin (default)
    2. Auto-approve: Set APPROVAL_AUTO=approve
    3. Auto-reject: Set APPROVAL_AUTO=reject

    Args:
        proposal: The proposal requiring approval

    Returns:
        ApprovalDecision with the human's choice
    """
    # Check for auto-approval mode (for testing/CI)
    auto_mode = os.environ.get("APPROVAL_AUTO", "").lower()

    if auto_mode == "approve":
        return ApprovalDecision(
            approved=True,
            reason="Auto-approved (APPROVAL_AUTO=approve)",
            decided_by="auto",
        )
    elif auto_mode == "reject":
        return ApprovalDecision(
            approved=False,
            reason="Auto-rejected (APPROVAL_AUTO=reject)",
            decided_by="auto",
        )

    # Interactive mode
    print("\n" + "=" * 60)
    print("APPROVAL REQUIRED")
    print("=" * 60)

    # Display proposal details
    print(f"\nProposed Action: {proposal.get('action', 'unknown')}")
    print(f"Risk Level: {proposal.get('risk_level', 'unknown')}")

    params = proposal.get("parameters", {})
    if params:
        print("\nParameters:")
        for key, value in params.items():
            print(f"  {key}: {value}")

    justification = proposal.get("justification", "")
    if justification:
        print(f"\nJustification: {justification}")

    reversible = proposal.get("reversible", False)
    print(f"\nReversible: {'Yes' if reversible else 'No'}")

    print("\n" + "-" * 60)

    # Get decision
    while True:
        try:
            response = input("\nApprove this action? [y/n]: ").strip().lower()

            if response in ("y", "yes"):
                reason = input(
                    "Approval reason (optional, press Enter to skip): "
                ).strip()
                return ApprovalDecision(
                    approved=True,
                    reason=reason if reason else None,
                    decided_by="human",
                )
            elif response in ("n", "no"):
                reason = input("Rejection reason (required): ").strip()
                return ApprovalDecision(
                    approved=False,
                    reason=reason if reason else "No reason provided",
                    decided_by="human",
                )
            else:
                print("Please enter 'y' for yes or 'n' for no.")

        except (EOFError, KeyboardInterrupt):
            # Non-interactive environment or user cancelled
            print("\nNo input available - auto-rejecting.")
            return ApprovalDecision(
                approved=False,
                reason="No human input available (non-interactive)",
                decided_by="system",
            )


def format_decision_for_audit(decision: ApprovalDecision) -> str:
    """
    Format an approval decision for audit logging.

    Args:
        decision: The approval decision

    Returns:
        Formatted string for logging
    """
    status = "APPROVED" if decision.approved else "REJECTED"
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(decision.decided_at))

    lines = [
        f"Decision: {status}",
        f"Decided by: {decision.decided_by}",
        f"Timestamp: {ts}",
    ]

    if decision.reason:
        lines.append(f"Reason: {decision.reason}")

    return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    print("=== Human Approval Module Demo ===\n")

    # Example proposal
    example_proposal = {
        "action": "process_refund",
        "parameters": {
            "customer_id": "CUST-12345",
            "amount": 150.00,
            "method": "original_payment_method",
        },
        "justification": "Customer returned item within policy window",
        "risk_level": "medium",
        "reversible": True,
    }

    # Request approval
    decision = request_human_approval(example_proposal)

    # Display result
    print("\n" + "=" * 60)
    print("DECISION RECORDED")
    print("=" * 60)
    print(format_decision_for_audit(decision))
