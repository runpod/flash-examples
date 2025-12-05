# Contributing to Flash Examples

Thank you for your interest in contributing to Runpod Flash Examples! This guide will help you create high-quality examples that benefit the community.

## Table of Contents

- [Types of Contributions](#types-of-contributions)
- [Example Standards](#example-standards)
- [Submission Process](#submission-process)
- [Example Structure](#example-structure)
- [Documentation Requirements](#documentation-requirements)
- [Testing Guidelines](#testing-guidelines)
- [Code Style](#code-style)

## Types of Contributions

### New Examples
Add examples that demonstrate:
- Common use cases not yet covered
- Novel ML model deployments
- Production patterns and best practices
- Integration with third-party services
- Performance optimization techniques

### Improvements to Existing Examples
- Bug fixes
- Performance optimizations
- Documentation improvements
- Additional features
- Better error handling

### Documentation
- Clarifying existing documentation
- Adding diagrams and visualizations
- Improving deployment guides
- Adding troubleshooting sections

## Example Standards

All examples must meet these standards:

### 1. Functional Requirements
- [ ] Runs successfully with `flash run`
- [ ] All endpoints return correct responses
- [ ] Error handling is implemented
- [ ] Environment variables are documented
- [ ] Dependencies are pinned in pyproject.toml
- [ ] Dependencies consolidated to root with `make consolidate-deps`
- [ ] Example loads in unified app (`flash run` from root)

### 2. Code Quality
- [ ] Clear, readable code
- [ ] Type hints for function signatures
- [ ] Async functions where appropriate
- [ ] No hardcoded credentials
- [ ] Proper logging (not print statements)

### 3. Documentation
- [ ] Comprehensive README.md
- [ ] Code comments for complex logic
- [ ] API endpoint documentation
- [ ] Deployment instructions
- [ ] Cost estimates (if applicable)

### 4. Production Readiness
- [ ] Input validation
- [ ] Error handling with meaningful messages
- [ ] Resource configuration (workers, timeout)
- [ ] Graceful degradation
- [ ] Security best practices

## Submission Process

### 1. Choose the Right Category

Place your example in the appropriate directory:

- `01_getting_started/` - Basic concepts, simple examples
- `02_ml_inference/` - ML model serving
- `03_advanced_workers/` - Worker patterns and optimizations
- `04_scaling_performance/` - Production scaling patterns
- `05_data_workflows/` - Data handling and pipelines
- `06_real_world/` - Complete applications
- `misc/` - Experimental or specialized examples

### 2. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/flash-examples.git
cd flash-examples
```

### 3. Create Your Example

Follow the [standard example structure](#example-structure).

### 4. Test Locally

```bash
cd your_category/your_example
flash run
# Test all endpoints
```

### 5. Consolidate Dependencies to Root

**Important**: The unified app loads all examples dynamically, so all example dependencies must be available in the root environment.

After adding your example with its dependencies, consolidate them to the root:

```bash
# From the repository root
make consolidate-deps  # Consolidates your example's deps to root pyproject.toml
uv sync                # Installs the new dependencies
```

The consolidation script:
- Automatically scans your example's `pyproject.toml`
- Merges all dependencies into the root configuration
- Lets pip/uv handle version resolution

If pip/uv reports version conflicts, resolve them manually in the root `pyproject.toml`.

**Verification**: Run `flash run` from the repository root to ensure your example loads without import errors.

### 6. Create Pull Request

```bash
git checkout -b add-example-name
git add .
git commit -m "Add example: your_example_name"
git push origin add-example-name
```

Create a PR with:
- Clear title: "Add example: [name]"
- Description of what the example demonstrates
- Any special requirements or considerations
- Screenshots/output examples (if applicable)

## Example Structure

### Standard Structure

```
your_example/
├── README.md              # Required: comprehensive documentation
├── main.py               # Required: FastAPI application
├── workers/              # Required: remote worker functions
│   ├── gpu/
│   │   ├── __init__.py
│   │   └── endpoint.py
│   └── cpu/
│       ├── __init__.py
│       └── endpoint.py
├── requirements.txt      # Required: pinned dependencies
├── pyproject.toml        # Required: project metadata
├── .env.example          # Required: environment template
├── .gitignore           # Required: ignore .env, .venv, etc.
├── .flashignore         # Optional: files to exclude from deployment
├── tests/               # Recommended: test files
│   ├── test_endpoints.py
│   └── conftest.py
└── assets/              # Optional: images, diagrams, etc.
    └── architecture.png
```

### Minimal main.py

```python
from fastapi import FastAPI
from workers.gpu import gpu_router
from workers.cpu import cpu_router

app = FastAPI(
    title="Your Example",
    description="Brief description",
    version="0.1.0",
)

app.include_router(gpu_router, prefix="/gpu", tags=["GPU Workers"])
app.include_router(cpu_router, prefix="/cpu", tags=["CPU Workers"])

@app.get("/")
def home():
    return {
        "message": "Your Example API",
        "docs": "/docs",
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.getenv("PORT", 8888))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

### Minimal Worker (endpoint.py)

```python
from tetra_rp import remote, LiveServerless, GpuGroup

config = LiveServerless(
    name="your_worker",
    gpus=[GpuGroup.ADA_24],
    workersMin=0,
    workersMax=3,
    idleTimeout=5,
)

@remote(resource_config=config, dependencies=["torch"])
async def your_function(input_data: dict) -> dict:
    """
    Clear docstring explaining what this function does.

    Args:
        input_data: Description of expected input

    Returns:
        Description of output format
    """
    import torch

    # Your implementation
    result = process(input_data)

    return {"status": "success", "result": result}

# Test locally
if __name__ == "__main__":
    import asyncio

    test_data = {"key": "value"}
    result = asyncio.run(your_function(test_data))
    print(result)
```

## Documentation Requirements

### README.md Template

Your example's README.md must include:

```markdown
# Example Name

Brief one-line description.

## What This Demonstrates

- Concept 1
- Concept 2
- Concept 3

## Prerequisites

- Python 3.12+
- Runpod API key
- Any special requirements

## Quick Start

1. Install dependencies
2. Configure environment
3. Run locally
4. Test endpoints

## Architecture

Explain the design and data flow.

## Configuration

Document all environment variables and settings.

## Endpoints

Document each API endpoint with examples.

## Deployment

Step-by-step deployment instructions.

## Cost Estimates

Provide rough cost estimates for running this example.

## Troubleshooting

Common issues and solutions.

## Next Steps

Suggestions for extending the example.
```

### Code Comments

- Document why, not what
- Explain non-obvious decisions
- Add references to external docs
- Note performance considerations
- Highlight security concerns

## Testing Guidelines

### Local Testing

Test your example thoroughly:

```bash
# Run the application
flash run

# Test health endpoint
curl http://localhost:8888/health

# Test your endpoints
curl -X POST http://localhost:8888/your/endpoint \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# Check API docs
open http://localhost:8888/docs
```

### VS Code Debugging

The repository includes VS Code debug configurations for endpoint development:

**Setup:**

1. Copy the root `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Add your Runpod API key to `.env`:
   ```bash
   RUNPOD_API_KEY=your_actual_api_key_here
   ```

3. Ensure you have the Python extension installed in VS Code

**Debugging:**

Two debug configurations are available:

- **Python Debugger: Current File** - Debug any Python file
- **Flash Worker: Debug Endpoint** - Debug worker endpoint files with async support

To debug an endpoint:
1. Open any `endpoint.py` file (e.g., `01_getting_started/01_hello_world/workers/gpu/endpoint.py`)
2. Set breakpoints in your worker functions
3. Press F5 or select "Debug: Start Debugging"
4. Choose the appropriate debug configuration
5. The debugger will execute the `if __name__ == "__main__"` test block

The `.env` file is automatically loaded, so your `RUNPOD_API_KEY` is available during debugging.

### Unit Tests (Recommended)

Add tests for your worker functions:

```python
# tests/test_endpoints.py
import pytest
from workers.gpu.endpoint import your_function

@pytest.mark.asyncio
async def test_your_function():
    input_data = {"key": "value"}
    result = await your_function(input_data)

    assert result["status"] == "success"
    assert "result" in result
```

Run tests:
```bash
pytest tests/
```

### Deployment Testing

Test deployment to verify it works on Runpod:

```bash
flash build
flash deploy new staging
flash deploy send staging
# Test the deployed endpoints
```

## Code Style

### Python Style

- Follow PEP 8
- Use type hints
- Prefer async/await over callbacks
- Use descriptive variable names
- Keep functions focused and small

### File Organization

- Group related functionality
- Separate concerns (routing, logic, config)
- Use clear module names
- Avoid circular imports

### Environment Variables

```python
# Good
import os
from dotenv import load_dotenv

load_dotenv()

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
if not RUNPOD_API_KEY:
    raise ValueError("RUNPOD_API_KEY is required")

# Bad
RUNPOD_API_KEY = "hardcoded_key"  # Never do this!
```

### Error Handling

```python
# Good
from fastapi import HTTPException

@router.post("/process")
async def process(data: dict):
    try:
        result = await worker_function(data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Bad
@router.post("/process")
async def process(data: dict):
    result = await worker_function(data)  # No error handling
    return result
```

## Dependencies

### Requirements.txt

Pin all dependencies:

```txt
tetra_rp==1.2.3
fastapi==0.104.1
uvicorn[standard]==0.24.0
torch==2.1.0
transformers==4.35.0
```

Generate with:
```bash
pip freeze > requirements.txt
```

### pyproject.toml

Include project metadata:

```toml
[project]
name = "your-example"
version = "0.1.0"
description = "Brief description"
requires-python = ">=3.12"
dependencies = [
    "tetra_rp>=1.2.0",
    "fastapi>=0.104.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## Security Best Practices

1. **Never commit secrets**
   - Use `.env` files (gitignored)
   - Provide `.env.example` templates
   - Document all required environment variables

2. **Validate inputs**
   - Use Pydantic models
   - Sanitize user input
   - Set reasonable limits

3. **Authentication**
   - Document if authentication is needed
   - Provide example implementation
   - Use secure token handling

4. **Dependencies**
   - Keep dependencies up to date
   - Review security advisories
   - Pin versions to avoid surprises

## Review Process

Pull requests will be reviewed for:

1. **Functionality**: Does it work as described?
2. **Code Quality**: Is it clean and maintainable?
3. **Documentation**: Is it well documented?
4. **Standards**: Does it follow guidelines?
5. **Security**: Are there security concerns?
6. **Value**: Does it add value to the repository?

Reviews typically take 2-7 days. Be patient and responsive to feedback.

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Chat**: Join the [Runpod Discord](https://discord.gg/runpod)
- **Docs**: Check [Flash Documentation](https://github.com/runpod/tetra-rp)

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to Flash Examples! Your examples help the community build better AI applications.
