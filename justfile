# Statehouse project tasks
# Run with: just <task>   e.g.  just publish-python

# Build the Python package (sdist + wheel) into python/dist/
build-python:
    ./scripts/publish_python.sh

# Build and push the Python package to PyPI (prompts for token)
publish-python:
    ./scripts/publish_python.sh --upload

# Build and push to Test PyPI
publish-python-test:
    ./scripts/publish_python.sh --test
