#!/usr/bin/env python3
"""
Integration test for Tutorial 01: Resumable Research Agent

This test verifies that the tutorial:
- Runs successfully from start to finish
- Produces deterministic output (tools are deterministic)
- Can resume after simulated crashes
- Can replay history correctly
- Runs fully offline (no external dependencies)
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def test_tutorial_basic_execution():
    """Test that tutorial runs successfully with a simple task."""
    tutorial_dir = Path(__file__).parent / "01-resumable-research-agent"

    # Reset state first
    returncode, stdout, stderr = run_command(
        ["python3", "agent.py", "--reset"], tutorial_dir
    )

    assert returncode == 0, f"Reset failed: {stderr}"

    # Run the agent with a simple calculation
    returncode, stdout, stderr = run_command(
        ["python3", "agent.py", "--task", "What is 42 * 137?"], tutorial_dir
    )

    assert returncode == 0, f"Agent execution failed: {stderr}"
    assert "5754" in stdout or "5,754" in stdout, f"Expected answer 5754 not found in: {stdout}"
    assert "Starting Research Agent" in stdout, "Expected start marker"

    print("✓ Basic execution test passed")


def test_tutorial_tools_deterministic():
    """Test that tools produce deterministic output."""
    tutorial_dir = Path(__file__).parent / "01-resumable-research-agent"

    # Import and test tools directly
    import sys
    sys.path.insert(0, str(tutorial_dir))
    from tools import ToolRegistry

    tools = ToolRegistry()

    # Test calculator (pure deterministic)
    result1 = tools.calculator("42 * 137")
    result2 = tools.calculator("42 * 137")
    assert result1 == result2 == 5754.0, f"Calculator not deterministic: {result1}, {result2}"

    # Test search (mock data, deterministic)
    search1 = tools.search("Raft consensus")
    search2 = tools.search("Raft consensus")
    assert search1 == search2, "Search not deterministic"
    assert len(search1) > 0, "Search returned no results"

    # Test read_file (mock data, deterministic)
    file1 = tools.read_file("README.md")
    file2 = tools.read_file("README.md")
    assert file1 == file2, "File read not deterministic"

    print("✓ Tool determinism test passed")


def test_tutorial_crash_resume():
    """Test that tutorial can handle crash and resume."""
    tutorial_dir = Path(__file__).parent / "01-resumable-research-agent"

    # Reset state
    run_command(["python3", "agent.py", "--reset"], tutorial_dir)

    # Run with crash at step 2
    returncode, stdout, stderr = run_command(
        ["python3", "agent.py", "--task", "What is 42 * 137?", "--crash-at-step", "2"],
        tutorial_dir,
    )

    assert returncode == 0, f"Crash simulation failed: {stderr}"
    assert "CRASH SIMULATION" in stdout, "Expected crash message"
    assert "step 2" in stdout, "Expected crash at step 2"

    # Resume should work
    returncode, stdout, stderr = run_command(
        ["python3", "agent.py", "--resume"], tutorial_dir
    )

    assert returncode == 0, f"Resume failed: {stderr}"
    assert "Resuming Research Agent" in stdout, "Expected resume message"

    print("✓ Crash/resume test passed")


def test_tutorial_replay():
    """Test that tutorial replay functionality works."""
    tutorial_dir = Path(__file__).parent / "01-resumable-research-agent"

    # Reset and run a task
    run_command(["python3", "agent.py", "--reset"], tutorial_dir)
    returncode, stdout, stderr = run_command(
        ["python3", "agent.py", "--task", "What is 42 * 137?"], tutorial_dir
    )

    assert returncode == 0, f"Task execution failed: {stderr}"

    # Replay should show history
    returncode, stdout, stderr = run_command(
        ["python3", "agent.py", "--replay"], tutorial_dir
    )

    assert returncode == 0, f"Replay failed: {stderr}"
    assert "agent=tutorial-agent-1" in stdout, "Expected agent ID in replay"
    assert "WRITE" in stdout, "Expected WRITE operations in replay"
    assert "key=" in stdout, "Expected key= in replay output"

    print("✓ Replay test passed")


def test_tutorial_offline():
    """Test that tutorial runs completely offline (no network)."""
    tutorial_dir = Path(__file__).parent / "01-resumable-research-agent"

    # Import tools to verify they work offline
    import sys
    sys.path.insert(0, str(tutorial_dir))
    from tools import ToolRegistry

    tools = ToolRegistry()

    # All tools should work without external network
    # Search uses mock data
    results = tools.search("test query")
    assert len(results) > 0, "Mock search failed"

    # Calculator is pure math
    calc_result = tools.calculator("10 + 5")
    assert calc_result == 15.0, "Calculator failed"

    # get_time uses local time
    timestamp = tools.get_time()
    assert "Z" in timestamp, "Timestamp format incorrect"

    # read_file uses mock filesystem
    content = tools.read_file("README.md")
    assert "Tutorial" in content, "Mock file read failed"

    print("✓ Offline mode test passed")


def test_tutorial_code_quality():
    """Test that tutorial code passes linting."""
    tutorial_dir = Path(__file__).parent / "01-resumable-research-agent"

    # Check if ruff is available
    try:
        result = subprocess.run(
            ["ruff", "--version"], capture_output=True, check=False
        )
        if result.returncode != 0:
            print("⚠ ruff not available, skipping code quality check")
            return
    except FileNotFoundError:
        print("⚠ ruff not installed, skipping code quality check")
        return

    # Check formatting
    returncode, stdout, stderr = run_command(
        ["ruff", "format", "--check", "."], tutorial_dir
    )

    if returncode != 0:
        print(f"✗ Format check failed: {stdout}{stderr}")
        raise AssertionError("Code formatting check failed")

    # Check linting
    returncode, stdout, stderr = run_command(
        ["ruff", "check", "."], tutorial_dir
    )

    if returncode != 0:
        print(f"✗ Lint check failed: {stdout}{stderr}")
        raise AssertionError("Code linting check failed")

    print("✓ Code quality test passed")


def main():
    """Run all integration tests."""
    print("=== Tutorial 01 Integration Tests ===\n")

    tests = [
        test_tutorial_basic_execution,
        test_tutorial_tools_deterministic,
        test_tutorial_crash_resume,
        test_tutorial_replay,
        test_tutorial_offline,
        test_tutorial_code_quality,
    ]

    failed = []

    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed.append(test.__name__)
        except Exception as e:
            print(f"✗ {test.__name__} errored: {e}")
            failed.append(test.__name__)

    print()

    if failed:
        print(f"=== {len(failed)} test(s) failed ===")
        for name in failed:
            print(f"  - {name}")
        sys.exit(1)
    else:
        print("=== All tests passed! ===")
        sys.exit(0)


if __name__ == "__main__":
    main()
