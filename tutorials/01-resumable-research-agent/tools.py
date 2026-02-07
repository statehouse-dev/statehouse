"""
Tool registry for the research agent.

All tools are deterministic - same input always produces same output.
This ensures replay produces identical results.
"""

from typing import List, Any


class ToolRegistry:
    """
    Registry of tools available to the research agent.

    All tools are mock implementations for the tutorial.
    Replace with real implementations in production.
    """

    def __init__(self):
        """Initialize the tool registry."""
        self.tools = {
            "search": self.search,
            "calculator": self.calculator,
            "get_time": self.get_time,
            "read_file": self.read_file,
        }

    def search(self, query: str) -> List[str]:
        """
        Mock search tool - returns fixed results.

        Args:
            query: Search query

        Returns:
            List of search result strings
        """
        # Deterministic mock results based on query content
        query_lower = query.lower()

        if "raft" in query_lower:
            return [
                "Raft: A consensus algorithm designed for understandability",
                "Raft vs Paxos: comparison of consensus protocols",
                "Raft implementation in etcd and Consul",
            ]

        elif "paxos" in query_lower:
            return [
                "Paxos: The classic consensus algorithm",
                "Understanding Paxos with simple examples",
            ]

        elif "statehouse" in query_lower:
            return [
                "Statehouse: strongly consistent state for agents",
                "Statehouse provides deterministic replay and crash recovery",
            ]

        elif "rust" in query_lower:
            return [
                "Rust programming language: memory safety without garbage collection",
                "Rust in production: performance and reliability",
            ]

        elif any(word in query_lower for word in ["python", "code", "programming"]):
            return [
                "Python: high-level programming for rapid development",
                "Python for AI: popular frameworks and libraries",
            ]

        else:
            # Generic results
            return [
                f"Result 1 for query: {query[:50]}",
                f"Result 2 for query: {query[:50]}",
            ]

    def calculator(self, expression: str) -> float:
        """
        Calculate a mathematical expression.

        Args:
            expression: Math expression (e.g., "42 * 137")

        Returns:
            Calculation result
        """
        try:
            # Safe evaluation of simple math expressions
            # Parse manually to avoid eval() security issues
            expression = expression.strip()

            # Handle simple binary operations
            for op in ["*", "/", "+", "-"]:
                if op in expression:
                    parts = expression.split(op)
                    if len(parts) == 2:
                        left = float(parts[0].strip())
                        right = float(parts[1].strip())

                        if op == "*":
                            return left * right
                        elif op == "/":
                            return left / right if right != 0 else float("inf")
                        elif op == "+":
                            return left + right
                        elif op == "-":
                            return left - right

            # Single number
            return float(expression)

        except (ValueError, AttributeError):
            return 0.0

    def get_time(self) -> str:
        """
        Get current timestamp.

        Returns:
            ISO 8601 formatted timestamp
        """
        from datetime import datetime

        return datetime.utcnow().isoformat() + "Z"

    def read_file(self, path: str) -> str:
        """
        Mock file reader - returns fixed content.

        Args:
            path: File path

        Returns:
            File content string
        """
        # Mock filesystem
        mock_files = {
            "README.md": "# Research Agent Tutorial\nA tutorial on building resumable agents.",
            "config.json": '{"daemon": "localhost:50051", "namespace": "default"}',
            "data.txt": "Sample data for testing.\nLine 2\nLine 3",
        }

        # Return content if file exists, otherwise error message
        return mock_files.get(path, f"[ERROR] File not found: {path}")

    def list_tools(self) -> List[str]:
        """
        List all available tools.

        Returns:
            List of tool names
        """
        return list(self.tools.keys())

    def call_tool(self, tool_name: str, *args, **kwargs) -> Any:
        """
        Call a tool by name.

        Args:
            tool_name: Name of tool to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Tool result

        Raises:
            ValueError: If tool not found
        """
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        return self.tools[tool_name](*args, **kwargs)


# Example usage
if __name__ == "__main__":
    tools = ToolRegistry()

    print("=== Tool Examples ===\n")

    # Search
    print("Search for 'Raft consensus':")
    results = tools.search("Raft consensus")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result}")
    print()

    # Calculator
    print("Calculate 42 * 137:")
    result = tools.calculator("42 * 137")
    print(f"  Result: {result}")
    print()

    # Time
    print("Get current time:")
    timestamp = tools.get_time()
    print(f"  {timestamp}")
    print()

    # File read
    print("Read README.md:")
    content = tools.read_file("README.md")
    print(f"  {content[:50]}...")
    print()
