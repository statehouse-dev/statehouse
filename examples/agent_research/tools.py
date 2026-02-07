"""
Tool implementations for the research agent.

This module provides a registry of tools that the agent can use,
including search, calculator, and file operations.
"""

import asyncio
import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class Tool(ABC):
    """Base class for agent tools."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass
    
    @abstractmethod
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool.
        
        Args:
            args: Tool arguments
            
        Returns:
            Tool result
        """
        pass


class SearchTool(Tool):
    """
    Mock search tool.
    
    In a real implementation, this would call a search API.
    For the demo, it returns mock results.
    """
    
    @property
    def name(self) -> str:
        return "search"
    
    @property
    def description(self) -> str:
        return "Search for information on the internet"
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        query = args.get("query", "")

        # Simulate API delay
        await asyncio.sleep(0.5)

        # Mock search: no real network. For demo, return Statehouse facts when query mentions it.
        q = query.lower()
        if "statehouse" in q:
            results = [
                {
                    "title": "Statehouse - state engine for AI agents",
                    "url": "https://statehouse.dev",
                    "snippet": "Statehouse is a strongly consistent state and memory engine for AI agents. It provides durable, versioned, replayable state with clear semantics so agent-based systems can be debugged, audited, and trusted in production. Self-hosted, not a cloud service.",
                },
                {
                    "title": "Statehouse architecture",
                    "url": "https://statehouse.dev/docs",
                    "snippet": "Built in Rust (daemon), with a gRPC API and Python SDK. Single-writer, append-only event log, transactional writes, snapshotting, and replay for full auditability.",
                },
            ]
            summary = "Found 2 results about Statehouse (mock search; in production, plug in a real search API)."
        else:
            results = [
                {
                    "title": f"Result 1 for: {query}",
                    "url": "https://example.com/1",
                    "snippet": f'Mock result for "{query}". This example uses mock tools—replace with a real search API for production.',
                },
                {
                    "title": f"Result 2 for: {query}",
                    "url": "https://example.com/2",
                    "snippet": f'Additional mock information about "{query}".',
                },
            ]
            summary = f'Found 2 results for "{query}" (mock; no real search).'

        return {
            "query": query,
            "results": results,
            "summary": summary,
            "source": "mock_search_api",
        }


class CalculatorTool(Tool):
    """
    Calculator tool for mathematical expressions.
    
    Safely evaluates mathematical expressions.
    """
    
    @property
    def name(self) -> str:
        return "calculator"
    
    @property
    def description(self) -> str:
        return "Evaluate mathematical expressions"
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        expression = args.get('expression', '')
        
        try:
            # Safe eval with limited builtins
            # In production, use a proper math parser
            allowed_names = {
                'abs': abs,
                'min': min,
                'max': max,
                'sum': sum,
                'round': round,
                'pow': pow
            }
            
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            
            return {
                'expression': expression,
                'result': result,
                'summary': f'{expression} = {result}',
                'source': 'calculator'
            }
        
        except Exception as e:
            return {
                'expression': expression,
                'error': str(e),
                'summary': f'Error evaluating: {expression}',
                'source': 'calculator'
            }


class WriteFileTool(Tool):
    """
    Tool to write content to a file.
    
    Useful for saving research results.
    """
    
    @property
    def name(self) -> str:
        return "write_file"
    
    @property
    def description(self) -> str:
        return "Write content to a file"
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        filepath = args.get('filepath', '')
        content = args.get('content', '')
        mode = args.get('mode', 'w')  # 'w' or 'a'
        
        if not filepath:
            return {
                'error': 'filepath is required',
                'summary': 'Failed to write file: no filepath provided'
            }
        
        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
            
            # Write file
            with open(filepath, mode) as f:
                f.write(content)
            
            size = os.path.getsize(filepath)
            
            return {
                'filepath': filepath,
                'size': size,
                'mode': mode,
                'summary': f'Wrote {size} bytes to {filepath}',
                'source': 'file_system'
            }
        
        except Exception as e:
            return {
                'filepath': filepath,
                'error': str(e),
                'summary': f'Error writing to {filepath}: {str(e)}',
                'source': 'file_system'
            }


class ReadFileTool(Tool):
    """
    Tool to read content from a file.
    
    Useful for loading context or previous results.
    """
    
    @property
    def name(self) -> str:
        return "read_file"
    
    @property
    def description(self) -> str:
        return "Read content from a file"
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        filepath = args.get('filepath', '')
        
        if not filepath:
            return {
                'error': 'filepath is required',
                'summary': 'Failed to read file: no filepath provided'
            }
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            size = len(content)
            
            return {
                'filepath': filepath,
                'content': content,
                'size': size,
                'summary': f'Read {size} bytes from {filepath}',
                'source': 'file_system'
            }
        
        except FileNotFoundError:
            return {
                'filepath': filepath,
                'error': 'File not found',
                'summary': f'File not found: {filepath}',
                'source': 'file_system'
            }
        except Exception as e:
            return {
                'filepath': filepath,
                'error': str(e),
                'summary': f'Error reading {filepath}: {str(e)}',
                'source': 'file_system'
            }


class ToolRegistry:
    """
    Registry for managing available tools.
    """
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """
        Register a tool.
        
        Args:
            tool: Tool instance to register
        """
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)
    
    def list_tools(self) -> Dict[str, str]:
        """
        List all available tools.
        
        Returns:
            Dict mapping tool names to descriptions
        """
        return {
            name: tool.description
            for name, tool in self._tools.items()
        }
    
    def to_json(self) -> str:
        """
        Export tools as JSON for LLM function calling.
        
        Returns:
            JSON string describing all tools
        """
        tools_spec = []
        
        for name, tool in self._tools.items():
            tools_spec.append({
                'name': name,
                'description': tool.description
            })
        
        return json.dumps(tools_spec, indent=2)
