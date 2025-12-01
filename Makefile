.PHONY: help venv-info dev sync-deps update-deps clean clean-venv lint lint-fix format format-check typecheck quality-check quality-check-strict ci-quality-github

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

# Detect which package manager to use (can be overridden with ENV_MANAGER=pip)
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
	@echo "Available make commands:"
	@echo ""
	@awk 'BEGIN {FS = ":.*# "; printf "  %-25s %s\n", "Target", "Description"} /^[a-zA-Z_-]+:.*# / {printf "  %-25s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Override detected manager: ENV_MANAGER=pip make dev"
	@echo "═══════════════════════════════════════════════════════════════"

# ============================================================================
# Environment Setup
# ============================================================================

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

dev: # Install development dependencies and package in editable mode
	@echo "Setting up development environment with $(PKG_MANAGER)..."
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
		conda run -p ./.venv pip install tetra-rp; \
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
		.venv/bin/pip install tetra-rp; \
	fi
	.venv/bin/pip install -e .
endif
	@echo "✓ Development environment ready!"
	@echo ""
	@echo "Next steps:"
ifeq ($(PKG_MANAGER),uv)
	@echo "  1. Run the unified Flash examples:  uv run flash run"
	@echo "  2. Visit:                           http://localhost:8888"
else ifeq ($(PKG_MANAGER),poetry)
	@echo "  1. Run the unified Flash examples:  poetry run flash run"
	@echo "  2. Visit:                           http://localhost:8888"
else ifeq ($(PKG_MANAGER),pipenv)
	@echo "  1. Run the unified Flash examples:  pipenv run flash run"
	@echo "  2. Visit:                           http://localhost:8888"
else ifeq ($(PKG_MANAGER),conda)
	@echo "  1. Run the unified Flash examples:  conda run -p ./.venv flash run"
	@echo "  2. Visit:                           http://localhost:8888"
else
	@echo "  1. Activate environment:            source .venv/bin/activate"
	@echo "  2. Run the unified Flash examples:  flash run"
	@echo "  3. Visit:                           http://localhost:8888"
endif
	@echo ""
	@echo "Additional commands:"
	@echo "  make help       - Show all available commands"
	@echo "  make lint       - Check code quality"
	@echo "  make format     - Format code"

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
	@echo "tetra-rp" > requirements.txt
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
	@echo "    - tetra-rp" >> environment.yml
	@echo "✓ environment.yml created"

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
	conda run -p ./.venv pip install --upgrade tetra-rp
else ifeq ($(PKG_MANAGER),pip)
	.venv/bin/pip install --upgrade tetra-rp
endif
	@echo "✓ Dependencies updated"

# ============================================================================
# Cleanup
# ============================================================================

clean: # Remove build artifacts and cache files
	rm -rf dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pkl" -delete
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

quality-check-strict: format-check lint typecheck # Strict quality gate with type checking
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
