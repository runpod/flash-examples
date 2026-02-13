# Flash Examples: AI Coding Assistant Guidelines

This document provides instructions for AI coding assistants (Claude Code, Cursor, GitHub Copilot, etc.) working on the flash-examples repository.

## Project Overview

The flash-examples repository contains production-ready examples demonstrating Flash framework capabilities. Examples are organized by category and automatically discovered by a unified FastAPI application through pattern matching.

**Key Architecture**: The root `main.py` scans category directories (`01_getting_started/`, `02_ml_inference/`, etc.) and dynamically loads all examples via APIRouter exports, creating a single unified app with auto-generated documentation.

**Important**: For full contribution guidelines, see [CONTRIBUTING.md](./CONTRIBUTING.md).

## Quick Start for Agents

Before diving deep, here's what you need to know:

### 1. Repository Structure
```
flash-examples/
├── main.py                    # Unified app with auto-discovery
├── Makefile                   # Development commands
├── scripts/
│   └── sync_example_deps.py  # Consolidates dependencies
├── 01_getting_started/        # Category directory
│   ├── 01_hello_world/       # Example directory
│   │   ├── gpu_worker.py     # Single-file worker (exports gpu_router)
│   │   ├── main.py           # Standalone FastAPI app for this example
│   │   ├── mothership.py     # Mothership endpoint config
│   │   └── pyproject.toml    # Example-specific dependencies
│   └── 03_mixed_workers/     # Complex example
│       ├── workers/
│       │   ├── gpu/__init__.py   # Exports gpu_router
│       │   └── cpu/__init__.py   # Exports cpu_router
│       ├── main.py
│       └── pyproject.toml
└── pyproject.toml            # Root dependencies (auto-generated)
```

### 2. Key Concepts

- **Unified App**: One FastAPI app serving all examples at http://localhost:8888
- **Auto-Discovery**: Examples are discovered by pattern matching, not manual registration
- **Router Naming**: Must export `{worker_type}_router` (e.g., `gpu_router`)
- **Dependency Consolidation**: Example deps → root `pyproject.toml` via `make consolidate-deps`
- **Two Testing Modes**:
  - Standalone: `cd example/ && flash run` (just that example)
  - Unified: `flash run` from root (all examples)

### 3. Your First Task? Start Here

**Reading code**:
1. Check `main.py:26-33` for category directories
2. Look at an example's `gpu_worker.py` or `workers/gpu/__init__.py`
3. Understand it exports a router with the right name

**Creating an example**:
1. `cd category_directory`
2. `flash init my_example`
3. Implement in fresh code (don't copy-paste)
4. `cd ../.. && make consolidate-deps`
5. Test with `flash run`

**Modifying code**:
1. Understand the pattern (single-file vs directory workers)
2. Make changes
3. Test with `flash run` from root
4. Run `make format && make lint`

## How Auto-Discovery Works

Understanding the discovery mechanism is crucial when creating examples:

1. **Category Scanning**: The root `main.py:26-33` defines category directories to scan
2. **Pattern Matching**: For each example directory, it looks for:
   - **Single-file workers**: `{worker_type}_worker.py` files (e.g., `gpu_worker.py`, `cpu_worker.py`) (main.py:59-112)
   - **Directory workers**: `workers/{worker_type}/__init__.py` files (main.py:115-184)
   - **Context routes**: Direct routes in example's `main.py` app (main.py:187-274)
3. **Router Naming**: Must export `{worker_type}_router` (e.g., `gpu_router`, `cpu_router`)
4. **URL Prefixes**: Routes are automatically prefixed with `/{example_name}/{worker_type}`
5. **Tagging**: All routes get tagged with "Category > Example Name" for OpenAPI docs

**Critical**: If your router isn't discovered, check:
- File naming matches patterns above
- Router variable is named correctly (`gpu_router`, not `router`)
- Example directory is in a scanned category
- No Python import errors in your module

## Critical: Use flash init for New Examples ⚠️

### The Rule
**Always use `flash init` to create new examples. Never copy-paste or duplicate existing example directories.**

### Why
- `flash init` generates the correct, current project structure
- Copy-pasting perpetuates outdated patterns and structure issues
- Ensures consistency across all examples
- Provides clean boilerplate aligned with Flash's latest conventions

### Workflow

When creating a new example:

```bash
# 1. Navigate to the appropriate category
cd 03_advanced_workers

# 2. Use flash init to create clean project structure
flash init my_new_example
cd my_new_example

# 3. Review existing examples in this category to understand patterns
# (don't copy code - understand the patterns)

# 4. Implement your example with fresh code

# 5. Run make consolidate-deps to update root dependencies
cd ../..
make consolidate-deps
```

### Study Without Copying

- Review existing examples to understand patterns and best practices
- Study how `@remote` decorator is configured
- Examine APIRouter setup and error handling
- Look at input validation patterns
- **But**: Generate your own implementation, don't duplicate code

## Flash-Specific Patterns

### Understanding @remote Functions

The `@remote` decorator is the core of Flash. It enables functions to run on remote Runpod infrastructure:

**Critical Constraints**:
- Functions decorated with `@remote` are serialized and sent to remote workers
- They can **ONLY** access their local scope (parameters and locally defined variables)
- All imports must be **inside the function**
- All helper functions must be **defined inside the function**
- No access to module-level variables, functions, or classes

**Why this matters**: When your function runs remotely, it doesn't have access to the module it was defined in - only the function code itself is sent.

### Remote Worker Decorator

```python
from runpod_flash import remote, LiveServerless, GpuGroup

# Configure resource requirements
# Naming convention: {category}_{example}_{worker_type}
gpu_config = LiveServerless(
    name="01_01_getting_started_gpu",
    gpus=[GpuGroup.ANY],
    workersMin=0,
    workersMax=3,
    idleTimeout=300,
)

@remote(resource_config=gpu_config)
async def process_image(input_data: dict) -> dict:
    """Process an image with GPU support."""
    # ✅ CORRECT: All imports inside the function
    import logging
    from PIL import Image
    import requests

    # ✅ CORRECT: Helper functions defined locally
    def download_image(url: str) -> Image.Image:
        response = requests.get(url)
        return Image.open(BytesIO(response.content))

    # Now use them
    logger = logging.getLogger(__name__)
    image_url = input_data.get("image_url")
    image = download_image(image_url)

    return {"status": "success", "size": image.size}
```

**Anti-pattern** (❌ This will fail):
```python
# Module-level imports - NOT accessible in @remote
import requests
from PIL import Image

# Module-level helper - NOT accessible in @remote
def download_image(url: str) -> Image.Image:
    response = requests.get(url)
    return Image.open(BytesIO(response.content))

@remote(resource_config=gpu_config)
async def process_image(input_data: dict) -> dict:
    # ❌ FAILS: download_image and imports not available remotely
    image = download_image(input_data["url"])
    return {"size": image.size}
```

Key points:
- Imports are from `runpod_flash`, not `flash`
- Create a config object (`LiveServerless` or `CpuLiveServerless`) for GPU/CPU workers
- Pass config via `resource_config` parameter to `@remote` decorator
- Use `async/await` for all worker functions
- Return serializable data (dict, list, str, etc.)
- Include comprehensive docstrings
- **All imports and helpers inside the function**

### APIRouter Export Pattern

**IMPORTANT**: Routers must follow the naming pattern `{worker_type}_router` (e.g., `gpu_router`, `cpu_router`). The unified app discovery system explicitly looks for this pattern.

**Single-file workers** (e.g., `gpu_worker.py`):
```python
from fastapi import APIRouter
from pydantic import BaseModel

class MyRequest(BaseModel):
    input_data: str

class MyResponse(BaseModel):
    status: str
    result: str

# Router must be named gpu_router (for gpu_worker.py)
gpu_router = APIRouter()

@gpu_router.post("/endpoint")
async def my_endpoint(request: MyRequest) -> MyResponse:
    """Handle endpoint request."""
    # implementation
    return MyResponse(status="success", result="...")
```

**Directory-based workers** (e.g., `workers/gpu/__init__.py`):
```python
from fastapi import APIRouter
from .endpoint import my_endpoint
from pydantic import BaseModel

class MyRequest(BaseModel):
    input_data: str

# Router must be named gpu_router (for workers/gpu/ directory)
gpu_router = APIRouter()

@gpu_router.post("/endpoint")
async def handle_endpoint(request: MyRequest):
    """Handle endpoint request."""
    return await my_endpoint(request)
```

The unified app auto-discovery looks for:
- **Single-file**: `{worker_type}_router` in `{worker_type}_worker.py` (e.g., `gpu_router` in `gpu_worker.py`)
- **Directory**: `{worker_type}_router` in `workers/{worker_type}/__init__.py` (e.g., `gpu_router` in `workers/gpu/__init__.py`)

### Mothership Endpoint Configuration

Every example includes a `mothership.py` file that configures the mothership endpoint - the load-balanced endpoint serving your FastAPI application routes.

```python
from runpod_flash import CpuLiveLoadBalancer

# Mothership endpoint configuration
mothership = CpuLiveLoadBalancer(
    name="01_01_hello_world-mothership",
    workersMin=1,
    workersMax=3,
)
```

**To customize:**
- Change `workersMin` and `workersMax` for scaling behavior
- Use `LiveLoadBalancer` instead of `CpuLiveLoadBalancer` for GPU
- Update the `name` parameter with appropriate endpoint name

**To disable mothership deployment:**
- Delete the `mothership.py` file, or
- Comment out the `mothership` variable

See the template `mothership.py` in your example for examples of customization.

### Input Validation with Pydantic

Always use Pydantic for request validation:

```python
from pydantic import BaseModel, Field, EmailStr

class ProcessRequest(BaseModel):
    image_url: str = Field(..., description="URL of image to process")
    quality: int = Field(default=90, ge=1, le=100)
    email: EmailStr

class ProcessResponse(BaseModel):
    status: str
    result: dict
    processing_time: float
```

Benefits:
- Automatic request validation
- Type safety
- OpenAPI documentation auto-generation
- Clear error messages

### Error Handling

```python
from fastapi import HTTPException, status

@router.post("/process")
async def process(request: ProcessRequest) -> ProcessResponse:
    try:
        result = await execute_processing(request)
        return ProcessResponse(status="success", result=result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Processing failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Processing failed. Check server logs."
        )
```

Guidelines:
- Catch specific exceptions, not bare `except`
- Provide actionable error messages
- Use appropriate HTTP status codes
- Log errors with context
- Never expose internal implementation details

## Dependency Management

### Adding Dependencies

1. Add to your example's `pyproject.toml`:
```toml
[project]
dependencies = [
    "torch>=2.0.0",
    "pillow>=10.0.0",
]
```

2. Pin specific versions for reproducibility
3. Document why each dependency is needed in your example's README

### Consolidating Dependencies

**Critical**: After adding dependencies, run:
```bash
cd /path/to/flash-examples
make consolidate-deps
```

This:
- Extracts all example dependencies to the root `pyproject.toml`
- Updates `uv.lock` with pinned versions
- Ensures all examples can be run in the unified app environment

**How it works**: The `scripts/sync_example_deps.py` script:
- Scans all category directories for example `pyproject.toml` files
- Collects all dependencies into a unified set
- Merges them with existing root dependencies
- Sorts and writes to root `pyproject.toml`
- No conflict resolution - if versions conflict, fix manually

**Never** directly edit the root `pyproject.toml` dependencies - it's auto-generated by `make consolidate-deps`.

## Code Standards

### Type Hints (Mandatory)

Every function must have type hints:

```python
# ✅ GOOD
def calculate_features(image: np.ndarray, threshold: float) -> dict[str, float]:
    """Extract image features."""
    pass

# ❌ BAD
def calculate_features(image, threshold):
    """Extract image features."""
    pass
```

### Early Returns / Guard Clauses

```python
# ✅ GOOD - Handle edge cases first
async def process_image(url: str) -> dict:
    if not url:
        raise ValueError("URL is required")

    if not url.startswith(("http://", "https://")):
        raise ValueError("Invalid URL scheme")

    # Main logic follows
    image = await download_image(url)
    return extract_features(image)

# ❌ BAD - Nested conditions
async def process_image(url: str) -> dict:
    if url:
        if url.startswith(("http://", "https://")):
            image = await download_image(url)
            return extract_features(image)
        else:
            raise ValueError("Invalid URL scheme")
    else:
        raise ValueError("URL is required")
```

### Logging (Not Print Statements)

```python
import logging

logger = logging.getLogger(__name__)

# ✅ GOOD
logger.info("Processing started", extra={"image_url": url, "user_id": user_id})
logger.error("Download failed", exc_info=True, extra={"url": url})

# ❌ BAD
print(f"Processing {url}")
print("ERROR: Download failed")
```

### No Hardcoded Credentials

```python
# ✅ GOOD - Use environment variables
import os
api_key = os.getenv("API_KEY")

# ❌ BAD - Hardcoded
api_key = "sk-1234567890abcdef"
```

## Testing Requirements

### Must Pass `flash run`

Your example must run successfully in the unified app:
```bash
flash run
# Visit http://localhost:8888/docs to test all endpoints
```

### Complete Testing Workflow

When you've finished implementing an example, follow this workflow:

**1. Local Functionality Test**
```bash
# From repository root
flash run

# Check discovery logs
# Should see: "Loaded {example_name}/{worker_type} from {file}"

# Verify in browser
open http://localhost:8888
# Your example should be listed

open http://localhost:8888/docs
# Your endpoints should appear under the category tag
```

**2. Endpoint Testing**

Test via Swagger UI at `/docs`:
- Click on your endpoint
- Click "Try it out"
- Enter test data
- Execute
- Verify response

Or via curl:
```bash
# Example for a GPU worker endpoint
curl -X POST http://localhost:8888/01_getting_started/my_example/gpu/process \
  -H "Content-Type: application/json" \
  -d '{"input": "test data"}'

# Verify successful response
```

**3. Code Quality Checks**
```bash
# Run all quality checks
make quality-check

# If it fails:
make format      # Fix formatting
make lint-fix    # Fix auto-fixable lint issues
make lint        # Check remaining issues

# For strict mode (includes type checking)
make quality-check-strict
```

**4. Dependency Verification**
```bash
# Ensure dependencies are consolidated
make check-deps

# If it fails, consolidate:
make consolidate-deps
uv sync
```

**5. Clean Build Test**
```bash
# Clean environment and rebuild
make clean
make clean-venv
make setup
flash run

# Ensures your example works in fresh environment
```

### Test in Unified Context

When testing locally, ensure your routes work with the unified app's auto-discovery:
- Your routes are prefixed with your example directory name
- Example: `/03_advanced_workers/my_example/endpoint`
- Test via the Swagger UI at `/docs`

### Async Testing with pytest-asyncio

```python
import pytest

@pytest.mark.asyncio
async def test_process_image():
    # Arrange
    url = "https://example.com/image.jpg"

    # Act
    result = await process_image(url)

    # Assert
    assert result["status"] == "success"
    assert "features" in result
```

### VS Code Debugging

Examples include `.vscode/launch.json` for debugging endpoints directly in VS Code.

### Definition of Done Checklist

Before considering your example complete, verify:

**Discovery & Routing**:
- [ ] Example appears on http://localhost:8888 home page
- [ ] Endpoints appear in `/docs` under correct category tag
- [ ] Routes have correct prefix: `/{example_name}/{worker_type}/...`
- [ ] All endpoints return expected responses

**Code Quality**:
- [ ] `make quality-check` passes
- [ ] `make check-deps` passes
- [ ] No Python import errors
- [ ] All functions have type hints
- [ ] No hardcoded credentials

**Documentation**:
- [ ] README.md is comprehensive
- [ ] All endpoints documented with request/response examples
- [ ] Docstrings on all functions and classes

**Testing**:
- [ ] Manual testing via `/docs` successful
- [ ] Tested in clean environment (`make clean-venv && make setup`)
- [ ] Works in unified app context

**Git Hygiene**:
- [ ] No auto-generated files committed (`flash_manifest.json`, example `uv.lock`)
- [ ] `.gitignore` includes flash build artifacts
- [ ] Only relevant files staged for commit

## Documentation Standards

### README.md Structure

Create a comprehensive `README.md` with these sections:

```markdown
# Example Name

Brief description of what this example demonstrates.

## Overview

Longer explanation of the use case and key learnings.

## What You'll Learn

- Key concept 1
- Key concept 2
- Key concept 3

## Architecture

Diagram or description of how this example works.

## Quick Start

### Prerequisites
- Python 3.10+
- Flash SDK

### Installation

```bash
cd path/to/this/example
flash run
```

### Test the Endpoint

```bash
curl -X POST http://localhost:8888/endpoint \
  -H "Content-Type: application/json" \
  -d '{"input": "value"}'
```

## API Endpoints

### POST /endpoint

**Description**: What this endpoint does.

**Request**:
```json
{
  "input": "string"
}
```

**Response**:
```json
{
  "status": "success",
  "result": "..."
}
```

**Error Handling**:
- 400 Bad Request: When input validation fails
- 500 Internal Server Error: When processing fails

## Deployment

Instructions for deploying to Runpod or other platforms.

## Cost Estimates

Approximate monthly costs for running this example in production.

## Common Issues

Troubleshooting section with solutions.

## References

- Flash documentation
- External libraries documentation


### Code Comments

- Comment complex logic only
- Prefer clear code over clever code
- Document non-obvious design decisions
- Docstrings for all functions and classes

## Project Structure

Your example directory should follow one of these patterns:

### Pattern 1: Single-file Workers

Use for simple examples with a single worker type and minimal logic.

```
example_name/
├── README.md
├── main.py                 # FastAPI app for local development
├── mothership.py           # Mothership endpoint configuration
├── gpu_worker.py          # Exports router (GPU worker)
├── cpu_worker.py          # Exports router (CPU worker) [optional]
├── pyproject.toml         # Dependencies and metadata
├── requirements.txt       # Pin dependencies for reproducibility
├── .env.example           # Environment variables template
├── .gitignore            # Git ignore patterns
├── .flashignore          # Flash build ignore patterns
└── .python-version       # Python version (optional)
```

**Example**: `01_getting_started/01_hello_world/`, `01_getting_started/02_cpu_worker/`

### Pattern 2: Directory-based Workers

Use for complex examples with multiple worker types, shared utilities, or extensive logic.

```
example_name/
├── README.md
├── main.py                # FastAPI app for local development
├── mothership.py          # Mothership endpoint configuration
├── pyproject.toml         # Dependencies and metadata
├── requirements.txt       # Pin dependencies for reproducibility
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore patterns
├── .flashignore          # Flash build ignore patterns
├── .python-version       # Python version (optional)
└── workers/
    ├── __init__.py
    ├── gpu/
    │   ├── __init__.py    # Exports gpu_router
    │   └── endpoint.py    # @remote functions
    └── cpu/
        ├── __init__.py    # Exports cpu_router
        └── endpoint.py    # @remote functions
```

**Example**: `01_getting_started/03_mixed_workers/`, `03_advanced_workers/05_load_balancer/`

### Files That Should NOT Be Committed

These files are auto-generated and should be ignored:

- `flash_manifest.json` - Generated by flash build
- `uv.lock` - Generated by uv sync (included in root uv.lock)

These are already added to `.gitignore` patterns.

## Pre-Commit Checklist

Before submitting an example:

- [ ] Used `flash init` to create the structure
- [ ] `mothership.py` is present (or intentionally deleted if not deploying mothership)
- [ ] `.gitignore` includes Flash auto-generated files (flash_manifest.json, uv.lock)
- [ ] All functions have type hints
- [ ] All endpoints have input validation (Pydantic models)
- [ ] Error handling is implemented
- [ ] No hardcoded credentials or secrets
- [ ] Using logging, not print statements
- [ ] **@remote functions only access local scope**
  - All imports are inside the function
  - All helper functions defined inside the function
  - No references to module-level variables or functions
- [ ] `flash run` executes without errors
- [ ] All endpoints tested via `/docs` Swagger UI
- [ ] README.md is comprehensive and accurate
- [ ] Dependencies added to pyproject.toml
- [ ] `make consolidate-deps` has been run
- [ ] No auto-generated files are tracked by git (flash_manifest.json, uv.lock)
- [ ] Code follows the standards in this guide

## Common Mistakes to Avoid

1. **Accessing external scope in @remote functions (CRITICAL)**: Only local variables, parameters, and internal imports work
   - ❌ Don't call functions or access variables defined outside the function
   - ❌ Don't use module-level imports
   - ✅ Import and define everything inside the function
2. **Copying existing examples**: Always use `flash init`
3. **Missing type hints**: Every parameter and return value
4. **Hardcoded values**: Use environment variables
5. **No error handling**: All external operations need try/except
6. **Print instead of logging**: Use the logging module
7. **Bare except clauses**: Always catch specific exceptions
8. **No input validation**: Use Pydantic models
9. **Not running consolidate-deps**: Critical for shared environment
10. **Routes not exporting router**: Unified app won't discover them
11. **Mutable default arguments**: Use None and initialize in function
12. **Wrong router variable name**: Must be `{worker_type}_router` (e.g., `gpu_router`, `cpu_router`)
13. **Committing auto-generated files**: Never commit `flash_manifest.json` or example-level `uv.lock`

## Troubleshooting Guide

### Example Not Showing in Unified App

**Symptoms**: Your example doesn't appear at http://localhost:8888 or `/docs`

**Diagnostics**:
```bash
# 1. Check the logs when starting flash run
flash run 2>&1 | grep -i "loaded\|error\|warning"

# 2. Verify your router naming
grep -n "router" your_example/gpu_worker.py
# Should see: gpu_router = APIRouter()

# 3. Check for Python errors
python -c "import sys; sys.path.insert(0, 'path/to/your_example'); import gpu_worker"

# 4. Verify file structure matches expected patterns
ls your_example/
```

**Common Causes**:
- Router variable named `router` instead of `gpu_router`
- Python import errors in your module
- File not named `gpu_worker.py` or `workers/gpu/__init__.py`
- Example directory not in scanned categories (see main.py:26-33)

### Routes Have Wrong Prefix

**Symptoms**: Endpoint is `/gpu/process` instead of `/my_example/gpu/process`

**Cause**: You're testing the example's standalone `main.py` instead of the unified app

**Solution**: Always test via the root-level unified app:
```bash
cd /path/to/flash-examples  # Root directory
flash run  # Not from inside example directory
```

### Dependencies Not Available

**Symptoms**: `ModuleNotFoundError` when running unified app

**Solution**:
```bash
# 1. Ensure dependency is in your example's pyproject.toml
cat path/to/example/pyproject.toml

# 2. Consolidate to root
make consolidate-deps

# 3. Sync dependencies
uv sync  # or: poetry install, pipenv sync, etc.

# 4. Verify installation
uv run python -c "import your_module"
```

### flash run Fails with Import Errors

**Common Issue**: Circular imports or missing `__init__.py`

**Solution**:
- Add `__init__.py` to all directories with Python files
- Check for circular imports between modules
- Ensure `sys.path` modifications are correct

### Mothership Endpoint Not Deploying

**Symptoms**: `flash deploy` doesn't create a mothership endpoint

**Check**:
```bash
# 1. Verify mothership.py exists
ls your_example/mothership.py

# 2. Check it exports a configured endpoint
grep -A 5 "mothership" your_example/mothership.py

# 3. Ensure variable is named 'mothership'
python -c "from your_example.mothership import mothership; print(mothership)"
```

### Code Quality Checks Failing in CI

**Symptoms**: GitHub Actions fails on `make quality-check`

**Local Fix**:
```bash
# 1. Run the same checks locally
make quality-check

# 2. Auto-fix formatting issues
make format

# 3. Auto-fix some lint issues
make lint-fix

# 4. Check dependencies are consolidated
make check-deps

# 5. Re-run quality checks
make quality-check
```

## Repository Navigation Tips

### Finding Examples

```bash
# List all example categories
ls -d 0*/

# List examples in a category
ls 01_getting_started/

# Find all GPU workers
find . -name "gpu_worker.py" -o -path "*/workers/gpu/__init__.py"

# Find all examples with certain dependencies
grep -r "torch" --include="pyproject.toml"
```

### Testing Your Example

```bash
# Run the unified app from root
flash run
# or with uv
uv run flash run

# Visit the home page
open http://localhost:8888

# Visit API docs
open http://localhost:8888/docs

# Test a specific endpoint
curl -X POST http://localhost:8888/01_getting_started/01_hello_world/gpu/process \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

### Common Development Workflows

**Creating a new example**:
```bash
cd 01_getting_started
flash init my_new_example
cd my_new_example
# ... implement your example ...
cd ../..
make consolidate-deps
flash run  # Test in unified app
```

**Updating dependencies**:
```bash
# Edit your example's pyproject.toml
cd 01_getting_started/my_example
vim pyproject.toml  # Add your dependency

# Consolidate to root
cd ../..
make consolidate-deps
uv sync  # Install new dependencies
```

**Debugging discovery issues**:
```bash
# Check if your example is discovered
flash run
# Look for log lines like:
# "Loaded 01_getting_started/my_example/gpu from gpu_worker.py"

# If not discovered, check:
# 1. Python import errors
python -c "import sys; sys.path.insert(0, '01_getting_started/my_example'); import gpu_worker"

# 2. Router naming
grep "router" 01_getting_started/my_example/gpu_worker.py
# Should see: gpu_router = APIRouter()
```

## Makefile Commands Reference

The repository includes a sophisticated Makefile with auto-detected package manager support:

### Most Common Commands

- `make setup` - One-time setup, creates venv and installs everything
- `make verify-setup` - Check that environment is configured correctly
- `make consolidate-deps` - **Critical** - Run after adding dependencies
- `make lint` - Check code quality with ruff
- `make format` - Auto-format code with ruff
- `make clean` - Remove build artifacts

### Package Manager Detection

The Makefile auto-detects your package manager in this priority order:
1. uv (recommended)
2. poetry
3. pipenv
4. pip
5. conda

Override with: `PKG_MANAGER=pip make setup`

### Quality Checks (CI)

- `make quality-check` - Essential checks (format + lint)
- `make quality-check-strict` - Strict checks (format + lint + typecheck + deps)
- `make check-deps` - Verify dependencies are consolidated (fails if not)

## Agent-Specific Tips

### Efficient Code Navigation

When asked to work on this repository, use these strategies:

**Understanding existing patterns**:
```bash
# Find all examples with GPU workers
find . -name "gpu_worker.py" -o -path "*/workers/gpu/__init__.py"

# See how @remote is used across examples
grep -r "@remote" --include="*.py" -A 5

# Find examples using specific dependencies
grep -r "torch\|transformers\|pillow" --include="pyproject.toml"

# Understand APIRouter patterns
grep -r "APIRouter()" --include="*.py"
```

**When asked to create a similar example**:
1. Use `find` to locate similar examples
2. Read them to understand patterns
3. Use `flash init` to create fresh structure
4. Implement with your own code

**When asked to debug**:
1. Check logs first: `flash run 2>&1 | grep -i error`
2. Verify imports: `python -c "import module_name"`
3. Check router naming: `grep "router" file.py`
4. Verify discovery: Look for "Loaded..." in flash run output

### Common Request Patterns

**"Add a new example for X"**:
1. Ask which category (or suggest based on complexity)
2. Run `flash init` in that category
3. Implement following patterns from CLAUDE.md
4. Test with `flash run`
5. Run `make consolidate-deps`
6. Verify with checklist

**"Fix example X"**:
1. Read the example code
2. Run it to reproduce issue
3. Check common mistakes section
4. Make targeted fix
5. Test with `flash run`
6. Run quality checks

**"Add feature Y to example X"**:
1. Read existing example
2. Understand its structure (single-file vs directory)
3. Make changes following same patterns
4. Update README.md if user-facing
5. Test thoroughly
6. Quality checks

**"Update dependencies"**:
1. Edit example's `pyproject.toml`
2. Run `make consolidate-deps`
3. Run `uv sync`
4. Test example still works

### What to Read First

When starting work on a new task:

**Creating examples**: Read in this order:
1. This file (CLAUDE.md) - patterns and rules
2. `main.py:26-184` - understand discovery
3. An example in same category - see patterns in practice
4. CONTRIBUTING.md - submission guidelines

**Debugging issues**: Read in this order:
1. Troubleshooting Guide (this file)
2. `main.py` discovery logic for your issue
3. Similar working examples for comparison
4. Error logs and traceback

**Modifying structure**: Read in this order:
1. `main.py` - understand discovery and registration
2. `scripts/sync_example_deps.py` - dependency management
3. `Makefile` - build and quality workflows
4. CONTRIBUTING.md - architectural guidelines

### Avoiding Over-Engineering

This repository values simplicity:

**Don't add these unless explicitly requested**:
- Extra error handling for impossible cases
- Feature flags or configuration systems
- Abstract base classes for one-time use
- Helper utilities for single-use operations
- Extensive logging for every operation
- Backwards compatibility hacks

**Do add these**:
- Type hints (mandatory)
- Input validation (Pydantic models)
- Error handling for external operations (network, files, etc.)
- Clear docstrings
- README documentation

### Performance Considerations

**Tool Usage**:
- Prefer `Glob` for finding files over `find` command
- Use `Grep` with appropriate output_mode for searching code
- Read files in parallel when checking multiple examples
- Use `Task` tool for complex multi-step exploration

**When Exploring**:
- Don't read entire codebase - focus on relevant category
- Use discovery logic in `main.py` as single source of truth
- Check 1-2 examples, not all of them
- Trust the patterns are consistent

## Getting Help

1. Check existing examples in the same category
2. Review CONTRIBUTING.md for additional guidelines
3. See Flash documentation at https://docs.runpod.io
4. Check repository issues and discussions
5. Use `make help` to see all available commands
6. Search this file (CLAUDE.md) for keywords related to your issue
