# Release Checklist

This document provides a comprehensive checklist for releasing Statehouse.

## Pre-Release Checklist

### 1. Code Quality

- [ ] All tests pass (`cargo test --workspace` and `pytest`)
- [ ] No compiler warnings (`cargo build --release`)
- [ ] Linting passes (Rust: `cargo clippy`, Python: `ruff check`)
- [ ] Code review completed for all changes
- [ ] Documentation is up-to-date

### 2. Version Management

- [ ] Version number updated in:
  - [ ] `Cargo.toml` (all crates)
  - [ ] `python/pyproject.toml`
  - [ ] `CHANGELOG.md`
- [ ] Git tag created for the release version
- [ ] CHANGELOG.md updated with release notes

### 3. Testing

- [ ] Unit tests pass (Rust)
- [ ] Integration tests pass (Python SDK)
- [ ] Manual testing completed:
  - [ ] Daemon starts successfully
  - [ ] Client can connect
  - [ ] Basic write/read operations work
  - [ ] Transaction lifecycle works
  - [ ] Replay works
  - [ ] CLI commands work
- [ ] Performance regression tests (if applicable)

### 4. Documentation

- [ ] README.md is current
- [ ] All docs in `docs/` are up-to-date:
  - [ ] architecture.md
  - [ ] grpc_architecture.md
  - [ ] api_contract.md
  - [ ] replay_semantics.md
  - [ ] FAQ.md
  - [ ] troubleshooting.md
- [ ] Python SDK docs are current
- [ ] CLI docs are current
- [ ] Example code works

### 5. Dependencies

- [ ] All dependencies are up-to-date
- [ ] Security audit completed (`cargo audit`)
- [ ] No known vulnerabilities
- [ ] License compliance verified

### 6. Build and Package

- [ ] Clean build succeeds
- [ ] Binary builds for target platforms:
  - [ ] Linux (x86_64)
  - [ ] macOS (arm64)
  - [ ] macOS (x86_64)
  - [ ] (Optional) Windows
- [ ] Package script works (`./scripts/package.sh`)
- [ ] Tarball extracts correctly
- [ ] Python package builds (`cd python && python -m build`)

## Release Process

### Step 1: Prepare Release Branch

```bash
# Create release branch
git checkout -b release/v0.1.0

# Update version numbers
# Edit Cargo.toml, python/pyproject.toml, CHANGELOG.md

# Commit version bump
git add .
git commit -m "chore: bump version to 0.1.0"

# Push to remote
git push origin release/v0.1.0
```

### Step 2: Build and Test

```bash
# Clean build
cargo clean
cargo build --release

# Run all tests
cargo test --workspace
cd python && pytest && cd ..

# Verify binary works
./target/release/statehoused --help
STATEHOUSE_USE_MEMORY=1 ./target/release/statehoused &
sleep 2
python3 -c "from statehouse import Statehouse; print(Statehouse().health())"
pkill statehoused

# Test packaging
./scripts/package.sh v0.1.0
```

### Step 3: Create Git Tag

```bash
# Create annotated tag
git tag -a v0.1.0 -m "Release v0.1.0

- Feature 1
- Feature 2
- Bug fix 3
"

# Push tag
git push origin v0.1.0
```

### Step 4: Build Release Artifacts

```bash
# Package daemon for each platform
./scripts/package.sh v0.1.0

# Build Python wheel
cd python
python -m build
cd ..

# Verify artifacts
ls -lh dist/
ls -lh python/dist/
```

### Step 5: Create GitHub Release

1. Go to GitHub Releases page
2. Click "Draft a new release"
3. Select tag: `v0.1.0`
4. Release title: `Statehouse v0.1.0`
5. Copy release notes from CHANGELOG.md
6. Attach artifacts:
   - `dist/statehouse-v0.1.0-*.tar.gz`
   - `dist/statehouse-v0.1.0-*.tar.gz.sha256`
   - `python/dist/statehouse-0.1.0.tar.gz`
   - `python/dist/statehouse-0.1.0-py3-none-any.whl`
7. Mark as "pre-release" if applicable
8. Publish release

### Step 6: Publish Python Package (Optional)

```bash
# Publish to PyPI (requires credentials)
cd python
python -m twine upload dist/*
cd ..
```

### Step 7: Update Documentation Site

- [ ] Update version in docs
- [ ] Deploy updated documentation
- [ ] Update download links

### Step 8: Merge Release Branch

```bash
# Merge to main
git checkout main
git merge release/v0.1.0
git push origin main

# Delete release branch
git branch -d release/v0.1.0
git push origin --delete release/v0.1.0
```

### Step 9: Announce Release

- [ ] Post announcement on GitHub Discussions
- [ ] Update README with release badge
- [ ] Post on social media (if applicable)
- [ ] Email mailing list (if applicable)

## Post-Release Checklist

### Verification

- [ ] Download release artifacts from GitHub
- [ ] Verify checksums match
- [ ] Test installation on clean system:
  - [ ] Extract tarball
  - [ ] Run binary
  - [ ] Install Python package
  - [ ] Run basic operations
- [ ] Check that documentation links work

### Monitoring

- [ ] Monitor GitHub issues for bug reports
- [ ] Watch for security vulnerabilities
- [ ] Track download metrics
- [ ] Collect user feedback

### Cleanup

- [ ] Delete local release branch
- [ ] Archive build artifacts (if needed)
- [ ] Update project board/roadmap

## Hotfix Process

If a critical bug is found after release:

```bash
# Create hotfix branch from tag
git checkout -b hotfix/v0.1.1 v0.1.0

# Fix the bug
# ... make changes ...

# Commit fix
git add .
git commit -m "fix: critical bug description"

# Bump version to 0.1.1
# Edit Cargo.toml, python/pyproject.toml, CHANGELOG.md

# Commit version bump
git add .
git commit -m "chore: bump version to 0.1.1"

# Create tag
git tag -a v0.1.1 -m "Hotfix v0.1.1 - fix critical bug"

# Push
git push origin hotfix/v0.1.1
git push origin v0.1.1

# Follow release process from Step 4
# ...

# Merge hotfix to main
git checkout main
git merge hotfix/v0.1.1
git push origin main

# Delete hotfix branch
git branch -d hotfix/v0.1.1
git push origin --delete hotfix/v0.1.1
```

## Rollback Process

If a release has critical issues:

1. **Immediate action**:
   - Mark GitHub release as "pre-release"
   - Add warning to release notes
   - Unpublish from PyPI (if published)

2. **Communicate**:
   - Post issue on GitHub Discussions
   - Email users (if contact info available)
   - Update documentation with warning

3. **Fix or revert**:
   - Create hotfix (see above), OR
   - Revert to previous stable version

4. **Verification**:
   - Test fix thoroughly
   - Follow release process for fixed version

## Version Numbering

Statehouse uses [Semantic Versioning](https://semver.org/):

- **MAJOR** (e.g., 1.0.0): Breaking changes to public API
- **MINOR** (e.g., 0.2.0): New features, backward compatible
- **PATCH** (e.g., 0.1.1): Bug fixes, backward compatible

Pre-release versions:
- **Alpha**: `0.1.0-alpha.1` (internal testing)
- **Beta**: `0.1.0-beta.1` (public testing)
- **RC**: `0.1.0-rc.1` (release candidate)

## Release Artifacts

Each release should include:

### Binary Packages

- `statehouse-v{VERSION}-{PLATFORM}-{ARCH}.tar.gz`
  - Contains: `statehoused` binary, sample config, README
  - Platforms: darwin-arm64, darwin-x86_64, linux-x86_64
- `statehouse-v{VERSION}-{PLATFORM}-{ARCH}.tar.gz.sha256`
  - Checksum for verification

### Python Packages

- `statehouse-{VERSION}.tar.gz` (source distribution)
- `statehouse-{VERSION}-py3-none-any.whl` (wheel)

### Documentation

- Link to docs site
- CHANGELOG.md included in release notes
- README.md included in tarball

## Contact

For questions about the release process:
- Open an issue on GitHub
- Email: maintainers@statehouse.dev (placeholder)
