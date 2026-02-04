.PHONY: help venv-info setup dev verify-setup consolidate-deps check-deps sync-deps update-deps clean clean-venv lint lint-fix format format-check typecheck quality-check quality-check-strict ci-quality-github

# ============================================================================
# Environment Manager Auto-Detection
# Priority: uv → poetry → pipenv → pip → conda
# ============================================================================

# Check for available package managers
HAS_UV := $(shell command -v uv 2> /dev/null)
HAS_POETRY := $(shell command -v poetry 2> /dev/null)
HAS_PIPENV := $(shell command -v pipenv 2> /dev/null)
HAS_PIP := $(shell command -v pip 2> /dev/null)
HAS_CONDA := $(shell command -v conda 2> /dev/null)

# Detect which package manager to use (can be overridden with PKG_MANAGER=pip)
ifndef PKG_MANAGER
ifdef HAS_UV
PKG_MANAGER := uv
else ifdef HAS_POETRY
PKG_MANAGER := poetry
else ifdef HAS_PIPENV
PKG_MANAGER := pipenv
else ifdef HAS_PIP
PKG_MANAGER := pip
else ifdef HAS_CONDA
PKG_MANAGER := conda
else
$(error "No package manager found. Please install uv, pip, poetry, pipenv, or conda")
endif
endif

# Determine the Python command based on environment
ifeq ($(PKG_MANAGER),uv)
PYTHON_RUN := uv run
PYTHON := uv run python
else ifeq ($(PKG_MANAGER),poetry)
PYTHON_RUN := poetry run
PYTHON := poetry run python
else ifeq ($(PKG_MANAGER),pipenv)
PYTHON_RUN := pipenv run
PYTHON := pipenv run python
else ifeq ($(PKG_MANAGER),conda)
ifneq (,$(wildcard ./.venv))
PYTHON_RUN := conda run -p ./.venv
PYTHON := conda run -p ./.venv python
else
PYTHON_RUN := python
PYTHON := python
endif
else
# pip/venv - check for active venv
ifneq (,$(wildcard ./.venv/bin/python))
PYTHON_RUN := ./.venv/bin/
PYTHON := ./.venv/bin/python
else
PYTHON_RUN :=
PYTHON := python
endif
endif

# ============================================================================
# Help - Show available commands
# ============================================================================

help: # Show this help menu with detected environment
	@echo "═══════════════════════════════════════════════════════════════"
	@echo "  Flash Examples - Makefile Commands"
	@echo "═══════════════════════════════════════════════════════════════"
	@echo ""
	@echo "Detected Package Manager: $(PKG_MANAGER)"
	@echo ""
	@echo "Getting Started:"
	@echo "  make setup          - Setup development environment (recommended)"
	@echo "  make verify-setup   - Verify environment is configured correctly"
	@echo ""
	@echo "Available make commands:"
	@echo ""
	@awk 'BEGIN {FS = ":.*# "; printf "  %-25s %s\n", "Target", "Description"} /^[a-zA-Z_-]+:.*# / {printf "  %-25s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Override detected manager: PKG_MANAGER=pip make setup"
	@echo "═══════════════════════════════════════════════════════════════"

# ============================================================================
# Environment Setup
# ============================================================================

.setup-env: # Internal: Setup .env file from .env.example if needed
	@if [ ! -f ".env" ] && [ -f ".env.example" ]; then \
		echo "→ Creating .env file from .env.example..."; \
		cp .env.example .env; \
		echo "  ✓ .env file created"; \
		echo ""; \
		echo "  ⚠ IMPORTANT: Add your Runpod API key to .env file"; \
		echo "    Get your key from: https://www.runpod.io/console/user/settings"; \
		echo "    Edit .env and replace 'your_api_key_here' with your actual key"; \
		echo ""; \
	elif [ -f ".env" ]; then \
		echo "  ✓ .env file already exists"; \
	fi

verify-setup: # Verify development environment is correctly configured
	@echo "═══════════════════════════════════════════════════════════════"
	@echo "  Flash Examples - Setup Verification"
	@echo "═══════════════════════════════════════════════════════════════"
	@echo ""
	@echo "→ Checking Python version..."
	@python_version=$$($(PYTHON) --version 2>&1 | awk '{print $$2}'); \
	major=$$(echo "$$python_version" | cut -d. -f1); \
	minor=$$(echo "$$python_version" | cut -d. -f2); \
	if [ "$$major" -gt 3 ] || ([ "$$major" -eq 3 ] && [ "$$minor" -ge 10 ]); then \
		echo "  ✓ Python $$python_version (>= 3.10 required)"; \
	else \
		echo "  ✗ Python $$python_version (>= 3.10 required)"; \
		echo "    Please upgrade Python to 3.10 or later"; \
		exit 1; \
	fi
	@echo ""
	@echo "→ Checking virtual environment..."
	@if [ -d ".venv" ]; then \
		echo "  ✓ Virtual environment exists (.venv)"; \
	else \
		echo "  ✗ Virtual environment not found"; \
		echo "    Run 'make setup' to create it"; \
		exit 1; \
	fi
	@echo ""
	@echo "→ Checking Flash CLI..."
	@if $(PYTHON_RUN) flash --version > /dev/null 2>&1; then \
		flash_version=$$($(PYTHON_RUN) flash --version 2>&1); \
		echo "  ✓ Flash CLI installed ($$flash_version)"; \
	else \
		echo "  ✗ Flash CLI not available"; \
		echo "    Run 'make setup' to install it"; \
		exit 1; \
	fi
	@echo ""
	@echo "→ Checking RUNPOD_API_KEY..."
	@if [ -n "$$RUNPOD_API_KEY" ]; then \
		echo "  ✓ RUNPOD_API_KEY set in environment"; \
	elif [ -f ".env" ] && grep -q "RUNPOD_API_KEY=" .env && ! grep -q "RUNPOD_API_KEY=your_api_key_here" .env; then \
		echo "  ✓ RUNPOD_API_KEY found in .env file"; \
	else \
		echo "  ⚠ RUNPOD_API_KEY not configured"; \
		echo "    Set it with: export RUNPOD_API_KEY=your_key_here"; \
		echo "    Or add to .env file"; \
		echo "    Get key from: https://www.runpod.io/console/user/settings"; \
	fi
	@echo ""
	@echo "═══════════════════════════════════════════════════════════════"
	@echo "  Setup verification complete!"
	@echo "═══════════════════════════════════════════════════════════════"

venv-info: # Display environment manager and virtual environment status
	@echo "Package Manager: $(PKG_MANAGER)"
	@echo "Python Runner: $(PYTHON_RUN)"
	@if [ -d ".venv" ]; then \
		echo "Virtual Environment: Active (.venv exists)"; \
		if [ -x ".venv/bin/python" ]; then \
			echo "Python Version: $$(.venv/bin/python --version)"; \
		fi \
	else \
		echo "Virtual Environment: Not found"; \
	fi

setup: .setup-env # Setup development environment with verification
	@echo "Setting up development environment with $(PKG_MANAGER)..."
	@echo ""
ifeq ($(PKG_MANAGER),uv)
	@if [ ! -d ".venv" ]; then uv venv; fi
	uv sync --all-groups
	uv pip install -e .
else ifeq ($(PKG_MANAGER),poetry)
	poetry install --with dev
	poetry run pip install -e .
else ifeq ($(PKG_MANAGER),pipenv)
	pipenv install --dev
	pipenv run pip install -e .
else ifeq ($(PKG_MANAGER),conda)
	@if [ ! -d ".venv" ]; then \
		echo "Creating conda environment at ./.venv..."; \
		conda create -p ./.venv python=3.11 -y; \
	fi
	@if [ -f "requirements.txt" ]; then \
		conda run -p ./.venv pip install -r requirements.txt; \
	else \
		conda run -p ./.venv pip install runpod-flash; \
	fi
	conda run -p ./.venv pip install -e .
else ifeq ($(PKG_MANAGER),pip)
	@if [ ! -d ".venv" ]; then \
		echo "Creating virtual environment..."; \
		python -m venv .venv; \
	fi
	@if [ -f "requirements.txt" ]; then \
		.venv/bin/pip install -r requirements.txt; \
	else \
		.venv/bin/pip install runpod-flash; \
	fi
	.venv/bin/pip install -e .
endif
	@echo "✓ Development environment ready!"
	@echo ""
	@$(MAKE) verify-setup
	@echo ""
	@echo "Next steps:"
ifeq ($(PKG_MANAGER),uv)
	@echo "  1. Edit .env and add your RUNPOD_API_KEY"
	@echo "  2. Run the unified Flash examples:  uv run flash run"
	@echo "  3. Visit:                           http://localhost:8888"
else ifeq ($(PKG_MANAGER),poetry)
	@echo "  1. Edit .env and add your RUNPOD_API_KEY"
	@echo "  2. Run the unified Flash examples:  poetry run flash run"
	@echo "  3. Visit:                           http://localhost:8888"
else ifeq ($(PKG_MANAGER),pipenv)
	@echo "  1. Edit .env and add your RUNPOD_API_KEY"
	@echo "  2. Run the unified Flash examples:  pipenv run flash run"
	@echo "  3. Visit:                           http://localhost:8888"
else ifeq ($(PKG_MANAGER),conda)
	@echo "  1. Edit .env and add your RUNPOD_API_KEY"
	@echo "  2. Run the unified Flash examples:  conda run -p ./.venv flash run"
	@echo "  3. Visit:                           http://localhost:8888"
else
	@echo "  1. Edit .env and add your RUNPOD_API_KEY"
	@echo "  2. Activate environment:            source .venv/bin/activate"
	@echo "  3. Run the unified Flash examples:  flash run"
	@echo "  4. Visit:                           http://localhost:8888"
endif
	@echo ""
	@echo "Additional commands:"
	@echo "  make help           - Show all available commands"
	@echo "  make verify-setup   - Re-run setup verification"
	@echo "  make lint           - Check code quality"
	@echo "  make format         - Format code"

dev: setup # Alias for 'make setup' (backward compatibility)

# ============================================================================
# Dependency File Generation
# ============================================================================

requirements.txt: # Generate requirements.txt from pyproject.toml
	@echo "Generating requirements.txt from pyproject.toml..."
ifeq ($(PKG_MANAGER),uv)
	uv pip compile pyproject.toml -o requirements.txt
else ifdef HAS_UV
	uv pip compile pyproject.toml -o requirements.txt
else
	@echo "runpod-flash" > requirements.txt
	@echo "✓ Basic requirements.txt created (install 'uv' for dependency resolution)"
endif

environment.yml: # Generate conda environment.yml from pyproject.toml
	@echo "Generating environment.yml for conda..."
	@echo "name: flash-examples" > environment.yml
	@echo "channels:" >> environment.yml
	@echo "  - conda-forge" >> environment.yml
	@echo "  - defaults" >> environment.yml
	@echo "dependencies:" >> environment.yml
	@echo "  - python>=3.11" >> environment.yml
	@echo "  - pip" >> environment.yml
	@echo "  - pip:" >> environment.yml
	@echo "    - runpod-flash" >> environment.yml
	@echo "✓ environment.yml created"

consolidate-deps: # Consolidate example dependencies to root pyproject.toml
	@echo "Consolidating example dependencies..."
	$(PYTHON) scripts/sync_example_deps.py

check-deps: # Verify example dependencies are consolidated (CI mode)
	@echo "Verifying dependencies are consolidated..."
	$(PYTHON) scripts/sync_example_deps.py --check

sync-deps: requirements.txt environment.yml # Generate all dependency files
	@echo "✓ All dependency files synced"

update-deps: # Update dependencies to latest versions
	@echo "Updating dependencies with $(PKG_MANAGER)..."
ifeq ($(PKG_MANAGER),uv)
	uv sync --upgrade
	uv pip compile --upgrade pyproject.toml -o requirements.txt
else ifeq ($(PKG_MANAGER),poetry)
	poetry update
else ifeq ($(PKG_MANAGER),pipenv)
	pipenv update
else ifeq ($(PKG_MANAGER),conda)
	conda run -p ./.venv pip install --upgrade runpod-flash
else ifeq ($(PKG_MANAGER),pip)
	.venv/bin/pip install --upgrade runpod-flash
endif
	@echo "✓ Dependencies updated"

# ============================================================================
# Cleanup
# ============================================================================

clean: # Remove build artifacts and cache files
	rm -rf dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Build artifacts cleaned"

clean-venv: # Remove virtual environment directory
	@if [ -d ".venv" ]; then \
		echo "Removing .venv directory..."; \
		rm -rf .venv; \
		echo "✓ Virtual environment removed"; \
	else \
		echo "No .venv directory found"; \
	fi

# ============================================================================
# Code Quality - Linting
# ============================================================================

lint: # Check code with ruff
	@echo "Running ruff linter..."
	$(PYTHON_RUN) ruff check .

lint-fix: # Fix code issues with ruff
	@echo "Fixing code issues with ruff..."
	$(PYTHON_RUN) ruff check . --fix

# ============================================================================
# Code Quality - Formatting
# ============================================================================

format: # Format code with ruff
	@echo "Formatting code with ruff..."
	$(PYTHON_RUN) ruff format .

format-check: # Check code formatting
	@echo "Checking code formatting..."
	$(PYTHON_RUN) ruff format --check .

# ============================================================================
# Code Quality - Type Checking
# ============================================================================

typecheck: # Check types with mypy
	@echo "Running mypy type checker..."
	@$(PYTHON_RUN) mypy . || { [ $$? -eq 2 ] && echo "No Python files found for type checking"; }

# ============================================================================
# Quality Gates (used in CI)
# ============================================================================

quality-check: format-check lint # Essential quality gate for CI
	@echo "✓ Quality checks passed"

quality-check-strict: format-check lint typecheck check-deps # Strict quality gate with type checking
	@echo "✓ Strict quality checks passed"

# ============================================================================
# GitHub Actions Specific
# ============================================================================

ci-quality-github: # Quality checks with GitHub Actions formatting
	@echo "::group::Code formatting check"
	$(PYTHON_RUN) ruff format --check .
	@echo "::endgroup::"
	@echo "::group::Linting"
	$(PYTHON_RUN) ruff check . --output-format=github
	@echo "::endgroup::"
