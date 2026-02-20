# 04 - Dependency Management

Learn how to manage Python packages and system dependencies in Flash workers.

## What This Demonstrates

- **Python dependencies** - Installing packages with version constraints
- **System dependencies** - Installing apt packages (ffmpeg, libgl1, etc.)
- **Version pinning** - Reproducible builds with exact versions
- **Dependency optimization** - Minimizing cold start time

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
# Good - Reproducible
dependencies=[
    "torch==2.1.0",
    "transformers==4.35.2",
    "numpy==1.26.2",
]

# Bad - Unpredictable
dependencies=[
    "torch",  # Version changes over time
    "transformers",
    "numpy",
]
```

### 2. Minimize Dependencies

```python
# Good - Only what's needed
@remote(
    dependencies=["requests"]  # Just one package
)
async def fetch_data(url: str):
    import requests
    return requests.get(url).json()

# Bad - Unnecessary bloat
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
python gpu_worker.py
python cpu_worker.py
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
runpod-flash
torch==2.1.0
transformers==4.35.2
Pillow>=10.0.0
numpy==1.26.2
```

**Note:** Worker dependencies in `@remote` decorator are deployed automatically. `requirements.txt` is for local development only.

## Advanced: Custom Docker Images

For complex dependencies, consider custom images:

```python
from runpod_flash import ServerlessEndpoint

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
