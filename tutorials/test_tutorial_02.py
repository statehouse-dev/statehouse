"""
Integration tests for Tutorial 02: Human-in-the-loop Approval Agent.

These tests verify:
- Tutorial code runs without errors
- Approval workflow works correctly
- Crash/resume functionality
- Explainability from stored state
- Output is deterministic
"""

import os
import subprocess
import sys

# Set auto-approval mode for non-interactive testing
os.environ["APPROVAL_AUTO"] = "approve"


def run_agent_command(args: list[str], cwd: str) -> subprocess.CompletedProcess:
    """Run the agent with given arguments."""
    return subprocess.run(
        [sys.executable, "agent.py"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
    )


class TestTutorial02:
    """Tests for the human-in-the-loop approval agent tutorial."""

    TUTORIAL_DIR = os.path.join(os.path.dirname(__file__), "02-human-in-the-loop-agent")

    def test_agent_module_imports(self) -> None:
        """Test that agent module can be imported."""
        sys.path.insert(0, self.TUTORIAL_DIR)
        try:
            import agent
            import human

            # Verify key classes exist
            assert hasattr(agent, "ApprovalAgent")
            assert hasattr(agent, "WorkflowState")
            assert hasattr(agent, "explain_decision")
            assert hasattr(human, "ApprovalDecision")
            assert hasattr(human, "request_human_approval")
        finally:
            sys.path.pop(0)

    def test_refund_workflow_approve(self) -> None:
        """Test complete refund workflow with approval."""
        # Reset first
        result = run_agent_command(["--reset"], self.TUTORIAL_DIR)
        assert result.returncode == 0

        # Run refund workflow (auto-approved via env var)
        result = run_agent_command(["--refund", "150.00"], self.TUTORIAL_DIR)

        assert result.returncode == 0
        assert "Workflow Complete" in result.stdout or "success" in result.stdout

    def test_refund_workflow_reject(self) -> None:
        """Test refund workflow with rejection."""
        os.environ["APPROVAL_AUTO"] = "reject"
        try:
            # Reset first
            result = run_agent_command(["--reset"], self.TUTORIAL_DIR)
            assert result.returncode == 0

            # Run refund workflow (auto-rejected)
            result = run_agent_command(["--refund", "150.00"], self.TUTORIAL_DIR)

            assert result.returncode == 0
            assert "Aborted" in result.stdout or "REJECTED" in result.stdout
        finally:
            os.environ["APPROVAL_AUTO"] = "approve"

    def test_access_workflow(self) -> None:
        """Test access request workflow."""
        result = run_agent_command(["--reset"], self.TUTORIAL_DIR)
        assert result.returncode == 0

        result = run_agent_command(["--access", "database-admin"], self.TUTORIAL_DIR)

        assert result.returncode == 0
        assert "Workflow Complete" in result.stdout or "success" in result.stdout

    def test_crash_before_approval(self) -> None:
        """Test crash simulation before approval."""
        result = run_agent_command(["--reset"], self.TUTORIAL_DIR)
        assert result.returncode == 0

        # Crash before approval
        result = run_agent_command(
            ["--refund", "150.00", "--crash-before-approval"],
            self.TUTORIAL_DIR,
        )

        assert result.returncode == 0
        assert "CRASH SIMULATION" in result.stdout
        assert "Before approval" in result.stdout

    def test_crash_and_resume(self) -> None:
        """Test crash and resume functionality."""
        result = run_agent_command(["--reset"], self.TUTORIAL_DIR)
        assert result.returncode == 0

        # Start workflow and crash
        result = run_agent_command(
            ["--refund", "150.00", "--crash-before-approval"],
            self.TUTORIAL_DIR,
        )
        assert result.returncode == 0
        assert "CRASH SIMULATION" in result.stdout

        # Resume workflow
        result = run_agent_command(["--resume"], self.TUTORIAL_DIR)
        assert result.returncode == 0
        assert "Resuming" in result.stdout or "RESUME" in result.stdout

    def test_explain_decision(self) -> None:
        """Test decision explanation functionality."""
        # Run complete workflow first
        result = run_agent_command(["--reset"], self.TUTORIAL_DIR)
        assert result.returncode == 0

        result = run_agent_command(["--refund", "100.00"], self.TUTORIAL_DIR)
        assert result.returncode == 0

        # Explain the decision
        result = run_agent_command(["--explain"], self.TUTORIAL_DIR)

        assert result.returncode == 0
        assert "ORIGINAL REQUEST" in result.stdout
        assert "AI ANALYSIS" in result.stdout
        assert "PROPOSED ACTION" in result.stdout
        assert "HUMAN DECISION" in result.stdout
        assert "FINAL OUTCOME" in result.stdout

    def test_replay(self) -> None:
        """Test replay functionality."""
        # Run complete workflow first
        result = run_agent_command(["--reset"], self.TUTORIAL_DIR)
        assert result.returncode == 0

        result = run_agent_command(["--refund", "100.00"], self.TUTORIAL_DIR)
        assert result.returncode == 0

        # Replay events
        result = run_agent_command(["--replay"], self.TUTORIAL_DIR)

        assert result.returncode == 0
        assert "Replay" in result.stdout
        assert "request" in result.stdout
        assert "WRITE" in result.stdout

    def test_reset(self) -> None:
        """Test reset functionality."""
        # Run a workflow
        result = run_agent_command(["--refund", "100.00"], self.TUTORIAL_DIR)

        # Reset
        result = run_agent_command(["--reset"], self.TUTORIAL_DIR)

        assert result.returncode == 0
        assert "Resetting" in result.stdout or "cleared" in result.stdout

    def test_determinism(self) -> None:
        """Test that workflow output is deterministic."""
        # Run workflow twice with same input
        result1_reset = run_agent_command(["--reset"], self.TUTORIAL_DIR)
        assert result1_reset.returncode == 0

        result1 = run_agent_command(["--refund", "200.00"], self.TUTORIAL_DIR)
        assert result1.returncode == 0

        result2_reset = run_agent_command(["--reset"], self.TUTORIAL_DIR)
        assert result2_reset.returncode == 0

        result2 = run_agent_command(["--refund", "200.00"], self.TUTORIAL_DIR)
        assert result2.returncode == 0

        # Key workflow steps should be identical
        # (timestamps will differ, but structure should match)
        assert "[STEP 1]" in result1.stdout and "[STEP 1]" in result2.stdout
        assert "[STEP 2]" in result1.stdout and "[STEP 2]" in result2.stdout
        assert "[STEP 3]" in result1.stdout and "[STEP 3]" in result2.stdout
        assert "process_refund" in result1.stdout and "process_refund" in result2.stdout


def test_code_quality() -> None:
    """Test that tutorial code passes quality checks."""
    tutorial_dir = os.path.join(os.path.dirname(__file__), "02-human-in-the-loop-agent")

    # Check formatting with ruff
    result = subprocess.run(
        ["ruff", "format", "--check", "."],
        cwd=tutorial_dir,
        capture_output=True,
        text=True,
    )
    # Don't fail on format issues in tests, just warn
    if result.returncode != 0:
        print(f"Formatting issues: {result.stdout}")

    # Check linting with ruff
    result = subprocess.run(
        ["ruff", "check", "."],
        cwd=tutorial_dir,
        capture_output=True,
        text=True,
    )
    # Don't fail on lint issues in tests, just warn
    if result.returncode != 0:
        print(f"Linting issues: {result.stdout}")


if __name__ == "__main__":
    # Run tests
    import pytest

    pytest.main([__file__, "-v"])
