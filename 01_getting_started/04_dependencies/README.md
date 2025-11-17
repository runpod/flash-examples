# 04 - Dependency Management

Learn how to manage Python packages and system dependencies in Flash workers.

## What This Demonstrates

- **Python dependencies** - Installing packages with version constraints
- **System dependencies** - Installing apt packages (ffmpeg, libgl1, etc.)
- **Version pinning** - Reproducible builds with exact versions
- **Dependency optimization** - Minimizing cold start time
- **Input validation** - Using Pydantic field validators for data quality

## Quick Start

**Prerequisites**: Complete the [repository setup](../../README.md#quick-start) first (clone, `make dev`, set API key).

### Run This Example

```bash
cd 01_getting_started/04_dependencies
flash run
```

Server starts at http://localhost:8888

### Alternative: Standalone Setup

If you haven't run the repository-wide setup:

```bash
# Install dependencies
pip install -r requirements.txt

# Set API key (choose one):
export RUNPOD_API_KEY=your_api_key_here
# OR create .env file:
echo "RUNPOD_API_KEY=your_api_key_here" > .env

# Run
flash run
```

## Dependency Types

### 1. Python Dependencies

Specified in `@remote` decorator:

```python
@remote(
    resource_config=config,
    dependencies=[
        "torch==2.1.0",      # Exact version
        "Pillow>=10.0.0",    # Minimum version
        "numpy<2.0.0",       # Maximum version
        "requests",          # Latest version
    ]
)
async def my_function(data: dict) -> dict:
    import torch
    import PIL
    # Your code here
```

### 2. System Dependencies

Install apt packages:

```python
@remote(
    resource_config=config,
    dependencies=["opencv-python"],
    system_dependencies=["ffmpeg", "libgl1", "graphviz"]
)
async def process_video(data: dict) -> dict:
    import cv2
    import subprocess
    
    # FFmpeg available
    subprocess.run(["ffmpeg", "-version"])
    
    # OpenCV works (needs libgl1)
    cap = cv2.VideoCapture("video.mp4")
```

### 3. No Dependencies

Fastest cold start:

```python
@remote(resource_config=config)  # No dependencies!
async def simple_function(data: dict) -> dict:
    # Only Python stdlib
    import json
    import re
    from datetime import datetime
    return {"result": "processed"}
```

## Input Validation with Pydantic

Flash uses FastAPI and Pydantic for request validation. Validate inputs at the API layer before they reach your worker functions.

### Why Validate?

- **Prevent errors** - Catch invalid data before processing
- **Better error messages** - Clear feedback to API consumers
- **Type safety** - Enforce data structure and types
- **Documentation** - Pydantic models auto-generate API docs

### Basic Validation

Define request models with type hints:

```python
from pydantic import BaseModel

class DataRequest(BaseModel):
    """Request model with automatic validation."""
    data: list[list[int]]  # List of lists of integers
    threshold: float = 0.5   # Optional with default
```

FastAPI automatically:
- Validates types (returns 422 if invalid)
- Generates OpenAPI docs
- Provides helpful error messages

### Field Validators

Use `@field_validator` for custom validation logic:

```python
from pydantic import BaseModel, field_validator

class DataRequest(BaseModel):
    data: list[list[int]]

    @field_validator("data")
    @classmethod
    def validate_two_columns(cls, v):
        if not v:
            raise ValueError("Data cannot be empty")

        # Require at least 2 rows for statistics
        if len(v) < 2:
            raise ValueError(
                f"Need at least 2 rows to compute statistics, got {len(v)}. "
                f'Example: {{"data": [[1, 2], [3, 4]]}}'
            )

        # Check each row has exactly 2 columns
        for i, row in enumerate(v):
            if len(row) != 2:
                raise ValueError(
                    f"Row {i} has {len(row)} columns, expected exactly 2. "
                    f'Example: {{"data": [[1, 2], [3, 4]]}}'
                )

        return v
```

This example (from `workers/cpu/__init__.py:14-30`) validates:
1. Data is not empty
2. At least 2 rows (prevents NaN in statistics)
3. Each row has exactly 2 columns

### Validation in FastAPI Router

Connect request models to endpoints:

```python
from fastapi import APIRouter
from pydantic import BaseModel, field_validator

router = APIRouter()

class DataRequest(BaseModel):
    data: list[list[int]]

    @field_validator("data")
    @classmethod
    def validate_structure(cls, v):
        # Custom validation logic
        return v

@router.post("/data")
async def process_endpoint(request: DataRequest):
    """FastAPI validates request automatically."""
    result = await process_data({"data": request.data})
    return result
```

### Testing Validation

Valid requests:
```bash
curl -X POST http://localhost:8888/cpu/data \
  -H "Content-Type: application/json" \
  -d '{"data": [[1, 2], [3, 4], [5, 6]]}'
```

Invalid requests return 422 with helpful errors:

```bash
# Too few rows
curl -X POST http://localhost:8888/cpu/data \
  -H "Content-Type: application/json" \
  -d '{"data": [[1, 2]]}'

# Response:
{
  "detail": [
    {
      "type": "value_error",
      "msg": "Value error, Need at least 2 rows to compute statistics, got 1. Example: {\"data\": [[1, 2], [3, 4]]}"
    }
  ]
}
```

```bash
# Wrong column count
curl -X POST http://localhost:8888/cpu/data \
  -H "Content-Type: application/json" \
  -d '{"data": [[1, 2, 3], [4, 5, 6]]}'

# Response:
{
  "detail": [
    {
      "type": "value_error",
      "msg": "Value error, Row 0 has 3 columns, expected exactly 2. Example: {\"data\": [[1, 2], [3, 4]]}"
    }
  ]
}
```

### Validation Best Practices

**1. Validate early** - At the API layer, not in worker functions

```python
# ✅ GOOD - Validation in Pydantic model
class DataRequest(BaseModel):
    data: list[list[int]]

    @field_validator("data")
    @classmethod
    def validate_data(cls, v):
        # Validation logic here
        return v

@router.post("/process")
async def endpoint(request: DataRequest):
    result = await worker(request.data)  # Already validated
    return result

# ❌ BAD - Validation in worker function
@remote(resource_config=config)
async def worker(input_data: dict):
    data = input_data["data"]
    if not data or not all(len(row) == 2 for row in data):
        return {"status": "error", "error": "Invalid data"}
    # Process data...
```

**2. Provide helpful error messages**

```python
# ✅ GOOD - Clear, actionable message
raise ValueError(
    f"Row {i} has {len(row)} columns, expected exactly 2. "
    f'Example: {{"data": [[1, 2], [3, 4]]}}'
)

# ❌ BAD - Vague message
raise ValueError("Invalid data format")
```

**3. Validate constraints, not just types**

```python
from pydantic import BaseModel, field_validator, Field

class ImageRequest(BaseModel):
    width: int = Field(gt=0, le=4096)    # 1-4096
    height: int = Field(gt=0, le=4096)   # 1-4096
    quality: int = Field(ge=1, le=100)   # 1-100

    @field_validator("width", "height")
    @classmethod
    def validate_dimensions(cls, v):
        if v % 8 != 0:
            raise ValueError(f"Dimension must be divisible by 8, got {v}")
        return v
```

**4. Use multiple validators for complex validation**

```python
class DataRequest(BaseModel):
    data: list[list[float]]
    normalize: bool = False

    @field_validator("data")
    @classmethod
    def validate_not_empty(cls, v):
        if not v:
            raise ValueError("Data cannot be empty")
        return v

    @field_validator("data")
    @classmethod
    def validate_dimensions(cls, v):
        # Check all rows have same length
        if len(set(len(row) for row in v)) > 1:
            raise ValueError("All rows must have same length")
        return v
```

### Common Validation Patterns

**Range validation:**
```python
from pydantic import Field

class Request(BaseModel):
    temperature: float = Field(ge=0.0, le=1.0)  # 0.0 to 1.0
    max_tokens: int = Field(gt=0, le=4096)      # 1 to 4096
```

**String validation:**
```python
from pydantic import field_validator
import re

class TextRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        if len(v) < 10:
            raise ValueError("Text must be at least 10 characters")
        if len(v) > 10000:
            raise ValueError("Text must not exceed 10,000 characters")
        return v
```

**List validation:**
```python
class BatchRequest(BaseModel):
    items: list[str]

    @field_validator("items")
    @classmethod
    def validate_batch_size(cls, v):
        if len(v) == 0:
            raise ValueError("Batch cannot be empty")
        if len(v) > 100:
            raise ValueError("Batch size cannot exceed 100 items")
        return v
```

**Enum validation:**
```python
from enum import Enum
from pydantic import BaseModel

class OutputFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    PARQUET = "parquet"

class ExportRequest(BaseModel):
    data: list[dict]
    format: OutputFormat  # Only accepts "json", "csv", or "parquet"
```

### Resources

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [FastAPI Request Validation](https://fastapi.tiangolo.com/tutorial/body/)
- [Field Validators Guide](https://docs.pydantic.dev/latest/concepts/validators/)

## Version Constraints

### Exact Version (==)
```python
"torch==2.1.0"  # Exactly 2.1.0
```
**Use when:** You need reproducible builds

### Minimum Version (>=)
```python
"Pillow>=10.0.0"  # 10.0.0 or higher
```
**Use when:** You need specific features introduced in a version

### Maximum Version (<)
```python
"numpy<2.0.0"  # Below 2.0.0
```
**Use when:** Avoiding breaking changes

### Compatible Release (~=)
```python
"requests~=2.31.0"  # >=2.31.0, <2.32.0
```
**Use when:** You want patch updates but not minor updates

### Latest Version
```python
"pandas"  # Latest available
```
**Use when:** You always want the newest version (not recommended for production)

## Common Dependencies

### ML/AI
```python
dependencies=[
    "torch==2.1.0",
    "transformers>=4.35.0",
    "diffusers",
    "accelerate",
    "safetensors",
]
```

### Data Science
```python
dependencies=[
    "pandas==2.1.3",
    "numpy==1.26.2",
    "scipy>=1.11.0",
    "matplotlib",
    "scikit-learn",
]
```

### Computer Vision
```python
dependencies=["opencv-python", "Pillow"]
system_dependencies=["libgl1", "libglib2.0-0"]
```

### Audio Processing
```python
dependencies=["librosa", "soundfile"]
system_dependencies=["ffmpeg", "libsndfile1"]
```

### NLP
```python
dependencies=[
    "transformers>=4.35.0",
    "tokenizers",
    "sentencepiece",
    "spacy",
]
```

## System Dependencies

Common apt packages:

| Package | Purpose |
|---------|---------|
| `ffmpeg` | Video/audio processing |
| `libgl1` | OpenCV requirement |
| `graphviz` | Graph visualization |
| `libsndfile1` | Audio file I/O |
| `git` | Git operations |
| `wget` | File downloads |

Example:
```python
system_dependencies=["ffmpeg", "libgl1", "wget"]
```

## Best Practices

### 1. Pin Versions for Production

```python
# ✅ GOOD - Reproducible
dependencies=[
    "torch==2.1.0",
    "transformers==4.35.2",
    "numpy==1.26.2",
]

# ❌ BAD - Unpredictable
dependencies=[
    "torch",  # Version changes over time
    "transformers",
    "numpy",
]
```

### 2. Minimize Dependencies

```python
# ✅ GOOD - Only what's needed
@remote(
    dependencies=["requests"]  # Just one package
)
async def fetch_data(url: str):
    import requests
    return requests.get(url).json()

# ❌ BAD - Unnecessary bloat
@remote(
    dependencies=[
        "requests",
        "pandas",  # Not used
        "numpy",   # Not used
        "scipy",   # Not used
    ]
)
async def fetch_data(url: str):
    import requests
    return requests.get(url).json()
```

### 3. Test Dependency Compatibility

```bash
# Test locally first
python -m workers.gpu.endpoint
python -m workers.cpu.endpoint
```

### 4. Document Dependencies

```python
@remote(
    resource_config=config,
    dependencies=[
        "torch==2.1.0",      # GPU operations
        "Pillow>=10.0.0",    # Image processing
        "requests",          # API calls
    ]
)
async def process_image(data: dict):
    """Process image with PyTorch and Pillow."""
    pass
```

## Troubleshooting

### Import Error

```
ModuleNotFoundError: No module named 'torch'
```

**Solution:** Add to dependencies:
```python
dependencies=["torch"]
```

### Version Conflict

```
ERROR: Cannot install torch==2.1.0 and torchvision==0.16.0
because these package versions have conflicting dependencies.
```

**Solution:** Check compatibility matrix, adjust versions:
```python
dependencies=[
    "torch==2.1.0",
    "torchvision==0.16.0+cu121",  # Compatible CUDA version
]
```

### System Package Missing

```
ImportError: libGL.so.1: cannot open shared object file
```

**Solution:** Add system dependency:
```python
system_dependencies=["libgl1"]
```

### Slow Cold Start

Dependencies take long to install?

**Solutions:**
1. Minimize dependencies
2. Use custom Docker image (advanced)
3. Keep workers warm (workersMin=1)

## Cold Start Times

| Dependencies | Cold Start Time |
|-------------|-----------------|
| None | ~5-10 seconds |
| Small (1-2 packages) | ~15-30 seconds |
| Medium (3-5 packages) | ~30-60 seconds |
| Large (torch, transformers) | ~60-120 seconds |

## Requirements.txt

For local development, create `requirements.txt`:

```txt
tetra_rp
torch==2.1.0
transformers==4.35.2
Pillow>=10.0.0
numpy==1.26.2
```

**Note:** Worker dependencies in `@remote` decorator are deployed automatically. `requirements.txt` is for local development only.

## Advanced: Custom Docker Images

For complex dependencies, consider custom images:

```python
from tetra_rp import ServerlessEndpoint

custom_config = ServerlessEndpoint(
    name="custom_image_worker",
    dockerImage="myregistry/my-image:v1.0",
    gpuIds=["NVIDIA GeForce RTX 4090"],
)

@remote(resource_config=custom_config)
async def process(data: dict):
    # All dependencies pre-installed in image
    pass
```

See [02_ml_inference/04_custom_images](../../02_ml_inference/04_custom_images/) for details.

## Next Steps

- **02_ml_inference** - Deploy real ML models
- **03_advanced_workers** - Caching and optimization
- **04_scaling_performance** - Production patterns

## Resources

- [PyPI Package Index](https://pypi.org/)
- [Ubuntu Package Search](https://packages.ubuntu.com/)
- [Runpod Docker Images](https://github.com/runpod/containers)
