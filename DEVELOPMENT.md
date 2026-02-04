# Development Guide

This guide covers environment setup, development workflow, and tooling for contributing to flash-examples.

## Table of Contents

- [Environment Setup](#environment-setup)
- [Makefile Commands](#makefile-commands)
- [Development Workflow](#development-workflow)
- [Code Quality](#code-quality)
- [Testing](#testing)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

## Environment Setup

### Prerequisites

- Python 3.10+ (3.12 recommended)
- One of: uv, pip, poetry, conda, or pipenv
- Git

### Quick Setup

The project Makefile auto-detects your package manager and sets up the environment:

```bash
git clone https://github.com/runpod/flash-examples.git
cd flash-examples
make setup
```

This works with any of these package managers:

#### uv (Recommended)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup project
make setup
```

**What it does:**
- Creates `.venv` if not exists
- Syncs all dependency groups from `uv.lock`
- Installs package in editable mode

#### pip + venv

```bash
# Setup project (creates venv automatically)
make setup
```

**What it does:**
- Creates `.venv` using `python -m venv`
- Installs from `requirements.txt` (or generates it)
- Installs package in editable mode

#### poetry

```bash
# Install poetry
curl -sSL https://install.python-poetry.org | python3 -

# Setup project
make setup
```

**What it does:**
- Uses poetry's virtual environment management
- Installs dev dependencies
- Installs package in editable mode

#### conda

```bash
# Setup project
make setup
```

**What it does:**
- Creates conda environment at `./.venv`
- Installs dependencies via pip
- Installs package in editable mode

#### pipenv

```bash
# Install pipenv
pip install pipenv

# Setup project
make setup
```

**What it does:**
- Creates pipenv environment
- Installs dev dependencies
- Installs package in editable mode

### Environment Manager Override

Force a specific package manager:

```bash
PKG_MANAGER=pip make setup
PKG_MANAGER=conda make setup
```

### Verify Your Setup

Check that everything is configured correctly:

```bash
make verify-setup
```

**Output:**
```
═══════════════════════════════════════════════════════════════
  Flash Examples - Setup Verification
═══════════════════════════════════════════════════════════════

→ Checking Python version...
  ✓ Python 3.12.1 (>= 3.10 required)

→ Checking virtual environment...
  ✓ Virtual environment exists (.venv)

→ Checking Flash CLI...
  ✓ Flash CLI installed (flash, version 0.1.0)

→ Checking RUNPOD_API_KEY...
  ✓ RUNPOD_API_KEY set in environment

═══════════════════════════════════════════════════════════════
  Setup verification complete!
═══════════════════════════════════════════════════════════════
```

### Check Environment Manager Status

```bash
make venv-info
```

**Output:**
```
Package Manager: uv
Python Runner: uv run
Virtual Environment: Active (.venv exists)
Python Version: Python 3.12.10
```

## Makefile Commands

### Help

```bash
make help
```

Shows all available commands with your detected environment manager.

### Environment Management

| Command | Description |
|---------|-------------|
| `make setup` | Setup development environment (auto-detects package manager) |
| `make verify-setup` | Verify environment is configured correctly |
| `make venv-info` | Display environment manager and venv status |
| `make clean-venv` | Remove `.venv` directory |
| `make update-deps` | Update dependencies to latest versions |

### Dependency Files

| Command | Description |
|---------|-------------|
| `make requirements.txt` | Generate `requirements.txt` from `pyproject.toml` |
| `make environment.yml` | Generate conda `environment.yml` |
| `make sync-deps` | Generate all dependency files |

**When to use:**
- `requirements.txt` - For pip users, Docker builds, CI/CD
- `environment.yml` - For conda users
- After updating `pyproject.toml` dependencies

### Code Quality

| Command | Description |
|---------|-------------|
| `make lint` | Check code with ruff |
| `make lint-fix` | Auto-fix linting issues |
| `make format` | Format code with ruff |
| `make format-check` | Check formatting without changes |
| `make typecheck` | Run mypy type checker |

### Quality Gates

| Command | Description | Use Case |
|---------|-------------|----------|
| `make quality-check` | Format check + lint | Fast pre-commit check |
| `make quality-check-strict` | Format + lint + typecheck | Thorough validation |
| `make ci-quality-github` | CI with GitHub Actions formatting | GitHub Actions only |

### Cleanup

| Command | Description |
|---------|-------------|
| `make clean` | Remove build artifacts, `__pycache__`, `.pyc` files |
| `make clean-venv` | Remove virtual environment |

## Development Workflow

### 1. Initial Setup

```bash
# Clone and setup
git clone https://github.com/runpod/flash-examples.git
cd flash-examples
make setup

# Verify setup
make venv-info
```

### 2. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 3. Make Changes

Follow these principles:
- Test-driven development (TDD)
- Single responsibility per function
- Type hints are mandatory
- Early returns for guard clauses

### 4. Run Quality Checks

```bash
# Before committing
make quality-check

# For stricter validation
make quality-check-strict
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: your descriptive commit message"
```

**Commit message format:**
```
type(scope): subject

Longer description if needed
- Bullet points for multiple changes

Types: feat, fix, refactor, test, docs, perf, chore
```

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

## Code Quality

### Ruff (Linting & Formatting)

**Check issues:**
```bash
make lint
```

**Auto-fix:**
```bash
make lint-fix
make format
```

**Configuration:** `pyproject.toml`

### Mypy (Type Checking)

**Run type checker:**
```bash
make typecheck
```

Type hints are mandatory:

```python
# Good
def process_data(items: list[dict[str, Any]]) -> pd.DataFrame:
    """Process items and return DataFrame."""
    pass

# Bad
def process_data(items):
    """Process items and return DataFrame."""
    pass
```

### Pre-commit Workflow

Before every commit:

```bash
make quality-check
```

If it fails:
1. Fix issues manually or use `make lint-fix` + `make format`
2. Re-run `make quality-check`
3. Commit

## Testing

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Stop on first failure
pytest -xvs

# With coverage
pytest --cov=src --cov-report=html
```

### Test Structure

Follow Arrange-Act-Assert pattern:

```python
def test_user_creation():
    # Arrange
    user_data = {"email": "test@example.com", "name": "Test User"}

    # Act
    user = User.create(**user_data)

    # Assert
    assert user.email == user_data["email"]
    assert user.id is not None
```

### Test Guidelines

- Test behavior, not implementation
- Use fixtures for reusable setup
- Mock external services, not internal code
- Test unhappy paths thoroughly

## Common Tasks

### Adding Dependencies

**1. Edit `pyproject.toml`:**

```toml
[project]
dependencies = [
    "runpod-flash",
    "new-package>=1.0.0",
]
```

**2. Sync environment:**

```bash
# With uv
uv sync

# With other managers
make setup
```

**3. Generate dependency files:**

```bash
make sync-deps
```

### Updating Dependencies

```bash
make update-deps
```

Then review and test changes before committing.

### Creating New Examples

**1. Create directory structure:**

```bash
mkdir -p 01_getting_started/05_new_example/workers/{gpu,cpu}
cd 01_getting_started/05_new_example
```

**2. Create files:**

```bash
touch README.md main.py .env.example
touch workers/gpu/__init__.py workers/gpu/endpoint.py
touch workers/cpu/__init__.py workers/cpu/endpoint.py
```

**3. Generate dependencies:**

```bash
# Create pyproject.toml with dependencies
# Then generate requirements.txt
cd ../../  # Back to root
make requirements.txt
cp requirements.txt 01_getting_started/05_new_example/
```

**4. Follow example structure** (see README.md)

### Cleaning Up

**Remove build artifacts:**
```bash
make clean
```

**Remove virtual environment:**
```bash
make clean-venv
```

**Fresh start:**
```bash
make clean-venv
make setup
```

## Troubleshooting

### Package Manager Not Detected

**Symptom:**
```
make: *** No package manager found
```

**Solution:**
Install one of: uv, pip, poetry, conda, or pipenv

```bash
# Easiest: pip (comes with Python)
python -m ensurepip

# Recommended: uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Virtual Environment Issues

**Wrong Python version in venv:**

```bash
make clean-venv
make setup
```

**Dependencies out of sync:**

```bash
# With uv
uv sync

# With pip
pip install -r requirements.txt

# Or recreate
make clean-venv
make setup
```

### Quality Checks Failing

**Formatting issues:**

```bash
make format
```

**Linting issues:**

```bash
make lint-fix
```

**Type errors:**

Review mypy output and add type hints:

```bash
make typecheck
```

### Makefile Commands Not Working

**Check which environment manager is detected:**

```bash
make venv-info
```

**Force specific manager:**

```bash
PKG_MANAGER=pip make setup
```

**Run commands directly:**

You can either use package manager prefixes or activate the environment first:

```bash
# Option 1: Use package manager prefix
uv run ruff check .          # With uv
poetry run ruff check .      # With poetry

# Option 2: Activate environment first (works with all managers)
source .venv/bin/activate   # Unix/macOS
.venv\Scripts\activate      # Windows
ruff check .
```

### Import Errors

**Package not installed in editable mode:**

```bash
# With uv
uv pip install -e .

# With pip
pip install -e .

# Or use Makefile
make setup
```

**Wrong virtual environment activated:**

```bash
# Deactivate current
deactivate

# Use Makefile (auto-detects)
make lint

# Or activate correct venv
source .venv/bin/activate  # Unix
.venv\Scripts\activate     # Windows
```

## CI/CD Integration

### GitHub Actions

The project includes quality checks optimized for GitHub Actions:

```yaml
- name: Run quality checks
  run: make ci-quality-github
```

This produces collapsible output groups in GitHub Actions logs.

### Local CI Simulation

Test what CI will run:

```bash
make quality-check-strict
```

This runs the same checks as CI (format + lint + typecheck).

## Editor Integration

### VS Code

Install extensions:
- Python (ms-python.python)
- Ruff (charliermarsh.ruff)
- Mypy Type Checker (ms-python.mypy-type-checker)

### PyCharm

Enable external tools:
- Settings → Tools → External Tools
- Add Makefile commands

### Vim/Neovim

Use ALE or null-ls with ruff and mypy configured.

## Additional Resources

- [Contributing Guidelines](./CONTRIBUTING.md) - Contribution process
- [README](./README.md) - Project overview

## Getting Help

- Check existing issues: https://github.com/runpod/flash-examples/issues
- Join Discord: https://discord.gg/runpod
- Read docs: https://docs.runpod.io
