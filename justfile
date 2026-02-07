# Statehouse project tasks
# Run with: just <task>   e.g.  just publish-python

_pyproject := "python/pyproject.toml"

# Bump version in python/pyproject.toml (major.minor.patch)
bump-major:
    #!/usr/bin/env bash
    set -e
    v=$(grep '^version = ' {{ _pyproject }} | sed 's/.*"\([0-9]*\)\.\([0-9]*\)\.\([0-9]*\)".*/\1 \2 \3/')
    read -r major minor patch <<< "$v"
    new="$((major+1)).0.0"
    sed -i.bak "s/^version = .*/version = \"$new\"/" {{ _pyproject }} && rm -f {{ _pyproject }}.bak
    echo "Bumped to $new"

bump-minor:
    #!/usr/bin/env bash
    set -e
    v=$(grep '^version = ' {{ _pyproject }} | sed 's/.*"\([0-9]*\)\.\([0-9]*\)\.\([0-9]*\)".*/\1 \2 \3/')
    read -r major minor patch <<< "$v"
    new="$major.$((minor+1)).0"
    sed -i.bak "s/^version = .*/version = \"$new\"/" {{ _pyproject }} && rm -f {{ _pyproject }}.bak
    echo "Bumped to $new"

bump-patch:
    #!/usr/bin/env bash
    set -e
    v=$(grep '^version = ' {{ _pyproject }} | sed 's/.*"\([0-9]*\)\.\([0-9]*\)\.\([0-9]*\)".*/\1 \2 \3/')
    read -r major minor patch <<< "$v"
    new="$major.$minor.$((patch+1))"
    sed -i.bak "s/^version = .*/version = \"$new\"/" {{ _pyproject }} && rm -f {{ _pyproject }}.bak
    echo "Bumped to $new"

# Build the Python package (sdist + wheel) into python/dist/
build-python:
    ./scripts/publish_python.sh

# Build and push the Python package to PyPI (prompts for token)
publish-python:
    ./scripts/publish_python.sh --upload

# Build and push to Test PyPI
publish-python-test:
    ./scripts/publish_python.sh --test

# Publish Rust crates to crates.io (order: proto → core → daemon)
# Requires CARGO_REGISTRY_TOKEN in .env (get token: https://crates.io/settings/tokens)
publish-cargo:
    #!/usr/bin/env bash
    set -e
    [[ -f .env ]] || { echo "Missing .env"; exit 1; }
    set -a && source .env && set +a
    [[ -n "${CARGO_REGISTRY_TOKEN:-}" ]] || { echo "CARGO_REGISTRY_TOKEN not set. Add it to .env"; exit 1; }
    cargo login "$CARGO_REGISTRY_TOKEN"
    cargo publish -p statehouse-proto --allow-dirty || true
    cargo publish -p statehouse-core --allow-dirty
    cargo publish -p statehouse-daemon --allow-dirty
