# Flash Examples: AI Coding Assistant Guidelines

This document provides instructions for AI coding assistants (Claude Code, Cursor, GitHub Copilot, etc.) working on the flash-examples repository.

## Project Overview

The flash-examples repository contains production-ready examples demonstrating Flash framework capabilities. Examples are organized by category and automatically discovered by a unified FastAPI application through pattern matching.

**Key Architecture**: The root `main.py` scans category directories (`01_getting_started/`, `02_ml_inference/`, etc.) and dynamically loads all examples via APIRouter exports, creating a single unified app with auto-generated documentation.

**Important**: For full contribution guidelines, see [CONTRIBUTING.md](./CONTRIBUTING.md).

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
    image_url = input_data.get("image_url")
    # implementation
    return {"status": "success", "result": "..."}
```

Key points:
- Imports are from `runpod_flash`, not `flash`
- Create a config object (`LiveServerless` or `CpuLiveServerless`) for GPU/CPU workers
- Pass config via `resource_config` parameter to `@remote` decorator
- Use `async/await` for all worker functions
- Return serializable data (dict, list, str, etc.)
- Include comprehensive docstrings

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

**Never** directly edit the root `pyproject.toml` - it's auto-generated by `make consolidate-deps`.

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

## Getting Help

1. Check existing examples in the same category
2. Review CONTRIBUTING.md for additional guidelines
3. See Flash documentation at https://docs.runpod.io
4. Check repository issues and discussions
