# Python Style Guide

This document defines the Python code quality standards for Statehouse.

## Philosophy

Code written for Statehouse should be:

1. **Readable** - Optimized for human understanding, not cleverness
2. **Explicit** - Clear control flow without hidden behavior
3. **Typed** - Type hints for public APIs and complex logic
4. **Tested** - Covered by automated tests
5. **Formatted** - Consistent style via automated tooling

## Target Audience

This codebase is written for **AI engineers** - practitioners who:
- Build agents and AI systems
- Read code to understand patterns
- Adapt examples for their own use cases
- Debug issues in production systems

Code should be understandable without extensive documentation.

## Tools

### Ruff

We use [Ruff](https://github.com/astral-sh/ruff) for both formatting and linting.

Install:
```bash
pip install ruff
```

Format code:
```bash
ruff format python/ tutorials/
```

Check linting:
```bash
ruff check python/ tutorials/
```

Auto-fix issues:
```bash
ruff check --fix python/ tutorials/
```

### Pytest

We use pytest for testing.

Install:
```bash
pip install pytest
```

Run tests:
```bash
cd python
pytest tests/
```

## Style Guidelines

### 1. Readable Over Clever

**Bad** - Clever but unclear:
```python
def process(items):
    return [x for sublist in (f(i) for i in items if pred(i)) for x in sublist]
```

**Good** - Clear and explicit:
```python
def process(items):
    results = []
    for item in items:
        if should_process(item):
            processed = process_item(item)
            results.extend(processed)
    return results
```

### 2. Explicit Control Flow

**Bad** - Hidden behavior:
```python
class Agent:
    def __init__(self):
        self._setup_hooks()  # What does this do?
    
    def _setup_hooks(self):
        # Magic registration happening here
        register_global_handler(self.handle)
```

**Good** - Explicit dependencies:
```python
class Agent:
    def __init__(self, client: Statehouse):
        self.client = client
        self.memory = AgentMemory(agent_id=self.id, client=client)
```

### 3. Type Hints for Public APIs

**Required** - Public functions and methods:
```python
def get_state(self, agent_id: str, key: str) -> StateResult:
    """Get state value."""
    # ...
```

**Optional** - Internal utilities (but encouraged):
```python
def _format_key(key):
    # Simple internal helper - types optional
    return key.strip().lower()
```

### 4. Dataclasses for Simple Models

**Good** - Use dataclasses for data structures:
```python
from dataclasses import dataclass

@dataclass
class StateResult:
    value: Optional[Dict[str, Any]]
    version: int
    commit_ts: int
    exists: bool
```

**Avoid** - Dictionaries for structured data:
```python
# BAD - no type safety
def get_state(...) -> dict:
    return {
        "value": value,
        "version": version,
        "commit_ts": ts,
        "exists": exists
    }
```

### 5. Clear Variable Names

**Bad** - Abbreviated or unclear:
```python
def proc_tx(t, ops):
    r = []
    for o in ops:
        r.append(apply(o, t))
    return r
```

**Good** - Descriptive names:
```python
def process_transaction(transaction: Transaction, operations: List[Operation]):
    results = []
    for operation in operations:
        result = apply_operation(operation, transaction)
        results.append(result)
    return results
```

### 6. Docstrings for Public APIs

**Required** - All public classes, functions, methods:
```python
def begin_transaction(self) -> Transaction:
    """
    Begin a new transaction.
    
    Returns:
        Transaction object for writing state
        
    Raises:
        ConnectionError: If daemon is unreachable
    """
    # ...
```

### 7. Error Handling

**Good** - Explicit error types:
```python
from .exceptions import TransactionError

def commit(self):
    try:
        response = self._stub.Commit(request)
    except grpc.RpcError as e:
        raise TransactionError(f"Commit failed: {e}")
```

**Avoid** - Broad exception catching:
```python
def commit(self):
    try:
        response = self._stub.Commit(request)
    except Exception as e:  # Too broad
        pass
```

## Tutorial Code Standards

Tutorial code has additional requirements:

### 1. Self-Documenting

Code should be understandable without reading docs:

```python
# Good - purpose is clear
def save_task(self, task: str) -> None:
    """Store the research task."""
    with self.client.begin_transaction() as tx:
        tx.write(agent_id=self.agent_id, key="task", value={"description": task})
```

### 2. Avoid Abstraction Layers

**Bad** - Unnecessary abstraction:
```python
class BaseAgent(ABC):
    @abstractmethod
    def execute(self): pass

class ResearchAgent(BaseAgent):
    def execute(self):
        self.pre_execute()
        self.do_execute()
        self.post_execute()
```

**Good** - Direct implementation:
```python
class ResearchAgent:
    def run(self, task: str):
        self.memory.save_task(task)
        for step in range(1, self.max_steps):
            self.execute_step(step, task)
```

### 3. Prefer Clarity Over Conciseness

**Bad** - Too concise:
```python
result = self.client.get_state(a, k) if k in keys else None
```

**Good** - Clear intent:
```python
if key in keys:
    result = self.client.get_state(agent_id, key)
else:
    result = None
```

## Pre-Commit Checklist

Before committing Python code:

- [ ] Run `ruff format` on changed files
- [ ] Run `ruff check` and fix all issues  
- [ ] Run `pytest` - all tests passing
- [ ] Add type hints to new public functions
- [ ] Add docstrings to new public APIs
- [ ] Ensure tutorial code is self-explanatory

## Running All Checks

Use the provided scripts:

```bash
# Lint check
./scripts/py_lint.sh

# Test suite
./scripts/py_test.sh
```

## CI Integration

All Python code is checked in CI:
- Formatting (ruff format --check)
- Linting (ruff check)
- Tests (pytest)
- Type checking (future - mypy)

Pull requests must pass all checks.

## See Also

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [pytest Documentation](https://docs.pytest.org/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
