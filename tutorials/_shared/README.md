# Shared Tutorial Utilities

This directory contains common utilities used across multiple Statehouse tutorials.

## Purpose

Rather than duplicating code across tutorials, shared utilities are centralized here. This includes:

- Mock LLM providers for offline testing
- Logging configuration helpers
- Test fixtures and helpers
- Common data structures
- Utility functions

## Structure

```
_shared/
  README.md           # This file
  mock_llm.py        # Mock LLM provider implementations
  helpers.py         # Common utility functions
  logging_config.py  # Structured logging setup
  test_helpers.py    # Testing utilities
```

## Usage in Tutorials

To use shared utilities in a tutorial:

```python
import sys
from pathlib import Path

# Add _shared to Python path
shared_dir = Path(__file__).parent.parent / "_shared"
sys.path.insert(0, str(shared_dir))

# Now import utilities
from mock_llm import MockLLMProvider
from helpers import format_timestamp, generate_id
```

## Mock LLM Provider

The mock LLM provider allows tutorials to run completely offline without API keys:

```python
from mock_llm import MockLLMProvider

# Create mock provider with predefined responses
llm = MockLLMProvider(responses=[
    "First response",
    "Second response",
    "Third response"
])

# Use like a real provider
response = llm.complete("What is 2+2?")
print(response)  # "First response"
```

See `mock_llm.py` for full API.

## Helpers

Common utility functions:

```python
from helpers import (
    format_timestamp,    # Format Unix timestamp as ISO string
    generate_id,         # Generate unique IDs
    truncate_string,     # Safely truncate long strings
    safe_json_dumps,     # JSON serialization with error handling
)
```

## Logging Configuration

Consistent logging setup across tutorials:

```python
from logging_config import setup_logging

# Setup structured logging
logger = setup_logging(
    name="tutorial-01",
    level="INFO",
    show_timestamps=True,
    show_colors=True
)

logger.info("Tutorial started", agent_id="agent-1")
```

## Test Helpers

Utilities for testing tutorial code:

```python
from test_helpers import (
    with_temp_state,      # Context manager for isolated state
    assert_state_equals,  # Compare state values
    capture_replay,       # Capture replay events for testing
)

# Example usage
with with_temp_state() as client:
    # Run tutorial code
    # State is automatically cleaned up
    pass
```

## Adding New Utilities

When adding new shared utilities:

1. **Keep it general**: Only add utilities needed by multiple tutorials
2. **Document clearly**: Include docstrings and examples
3. **Test thoroughly**: Add tests to verify correctness
4. **Keep dependencies minimal**: Avoid heavy dependencies
5. **Follow Python conventions**: Use type hints, dataclasses, etc.

## Guidelines

- **No tutorial-specific code**: Keep utilities general-purpose
- **Stable API**: Changes to shared utilities affect all tutorials
- **Backward compatibility**: Don't break existing tutorials
- **Minimal dependencies**: Only standard library + Statehouse SDK
- **Self-documenting**: Clear function names and docstrings

## See Also

- [Tutorial README](../README.md)
- [Python Style Guide](../../docs/dev/python-style.md)
- [Contributing Guide](../../CONTRIBUTING.md)
