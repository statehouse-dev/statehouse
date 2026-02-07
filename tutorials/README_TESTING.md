# Tutorial Testing

This directory contains integration tests for Statehouse tutorials.

## Running Tests

Each tutorial has integration tests that verify:
- Basic execution works
- Tools produce deterministic output
- Crash/resume functionality works
- Replay functionality works
- Code runs fully offline (no external dependencies)
- Code passes linting checks

### Tutorial 01: Resumable Research Agent

```bash
# Start the daemon first
STATEHOUSE_USE_MEMORY=1 statehoused

# In another terminal, run the tests
cd tutorials
python3 test_tutorial_01.py
```

## Test Requirements

- Statehouse daemon must be running (in-memory mode recommended for tests)
- Python SDK must be installed: `cd python && pip install -e .`
- Optional: `ruff` for code quality checks: `pip install ruff`

## Continuous Integration

The `.github/workflows/python-quality.yml` workflow runs these tests automatically:
- On every push to main that modifies Python code
- On every pull request that modifies Python code

The CI workflow:
1. Builds the Statehouse daemon in release mode
2. Starts the daemon in in-memory mode
3. Runs tutorial integration tests
4. Checks code formatting and linting
5. Runs SDK unit tests

## Adding New Tutorial Tests

To add tests for a new tutorial:

1. Create `tutorials/test_tutorial_NN.py` (where NN is the tutorial number)
2. Follow the same structure as `test_tutorial_01.py`
3. Test at minimum:
   - Basic execution
   - Tool determinism (if applicable)
   - Offline operation
   - Code quality

4. Update `.github/workflows/python-quality.yml` to include the new test file

## Philosophy

Tutorial tests serve multiple purposes:

1. **Correctness**: Verify tutorials work as documented
2. **Determinism**: Ensure tools produce consistent output for replay
3. **Offline Operation**: Tutorials should work without external dependencies
4. **Code Quality**: Maintain high standards for tutorial code (it's a teaching tool)
5. **Regression Prevention**: Catch breaking changes early

All tests should be fast (<30 seconds total) and reliable.
