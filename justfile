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

# Build Docker image for statehoused (default tag: statehouse-dev/statehouse:latest)
# Override: just docker-build DOCKER_IMAGE=myuser/statehouse:v0.1.0
docker-build DOCKER_IMAGE="statehouse-dev/statehouse:latest":
    docker build -t {{ DOCKER_IMAGE }} .

# Run statehoused in a container (in-memory, port 50051). Stop with: docker stop statehouse
docker-run DOCKER_IMAGE="statehouse-dev/statehouse:latest":
    docker rm -f statehouse 2>/dev/null || true
    docker run -d -p 50051:50051 --name statehouse {{ DOCKER_IMAGE }}

# Publish Docker image to Docker Hub
# Requires DOCKERHUB_USERNAME and DOCKERHUB_TOKEN in .env
# Optional: DOCKER_TAG=v0.1.0 to also push that tag
publish-docker:
    #!/usr/bin/env bash
    set -e
    [[ -f .env ]] || { echo "Missing .env"; exit 1; }
    set -a && source .env && set +a
    [[ -n "${DOCKERHUB_USERNAME:-}" ]] || { echo "DOCKERHUB_USERNAME not set in .env"; exit 1; }
    [[ -n "${DOCKERHUB_TOKEN:-}" ]] || { echo "DOCKERHUB_TOKEN not set in .env"; exit 1; }
    IMG="${DOCKERHUB_USERNAME}/statehouse"
    echo "Building ${IMG}:latest ..."
    docker build -t "${IMG}:latest" .
    echo "Pushing ${IMG}:latest ..."
    echo "$DOCKERHUB_TOKEN" | docker login -u "$DOCKERHUB_USERNAME" --password-stdin
    docker push "${IMG}:latest"
    if [[ -n "${DOCKER_TAG:-}" ]]; then
        docker tag "${IMG}:latest" "${IMG}:${DOCKER_TAG}"
        docker push "${IMG}:${DOCKER_TAG}"
        echo "Pushed ${IMG}:${DOCKER_TAG}"
    fi
    echo "Done. Pushed ${IMG}:latest"

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

# Publish only core + daemon (use when statehouse-proto is already on crates.io)
publish-cargo-core-daemon:
    #!/usr/bin/env bash
    set -e
    [[ -f .env ]] || { echo "Missing .env"; exit 1; }
    set -a && source .env && set +a
    [[ -n "${CARGO_REGISTRY_TOKEN:-}" ]] || { echo "CARGO_REGISTRY_TOKEN not set. Add it to .env"; exit 1; }
    cargo login "$CARGO_REGISTRY_TOKEN"
    cargo publish -p statehouse-core --allow-dirty
    cargo publish -p statehouse-daemon --allow-dirty
