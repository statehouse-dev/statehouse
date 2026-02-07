"""
Shared utilities for Statehouse tutorials.

This module contains minimal helper functions used across multiple tutorials.
Each function is self-contained and well-documented.
"""

import time
from typing import Any, Dict


def format_timestamp(ts: int) -> str:
    """
    Format a Unix timestamp (seconds) for display.
    
    Args:
        ts: Unix timestamp in seconds
        
    Returns:
        Human-readable timestamp string
    """
    from datetime import datetime
    dt = datetime.fromtimestamp(ts)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def wait_for_daemon(client, max_attempts: int = 10, delay: float = 1.0) -> bool:
    """
    Wait for Statehouse daemon to be ready.
    
    Args:
        client: Statehouse client instance
        max_attempts: Maximum connection attempts
        delay: Delay between attempts in seconds
        
    Returns:
        True if daemon is ready, False otherwise
    """
    for attempt in range(max_attempts):
        try:
            status = client.health()
            if status == "ok":
                return True
        except Exception:
            pass
        
        if attempt < max_attempts - 1:
            time.sleep(delay)
    
    return False


def print_section(title: str, width: int = 60) -> None:
    """
    Print a formatted section header.
    
    Args:
        title: Section title
        width: Total width of the header line
    """
    print()
    print("=" * width)
    print(f" {title}")
    print("=" * width)
    print()


def print_state(state_dict: Dict[str, Any], indent: int = 2) -> None:
    """
    Pretty-print a state dictionary.
    
    Args:
        state_dict: Dictionary to print
        indent: Indentation level
    """
    import json
    print(json.dumps(state_dict, indent=indent))
