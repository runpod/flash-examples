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
uv sync

# Authenticate
uv run flash login
# Or create .env file with RUNPOD_API_KEY=your_api_key_here

# Run
uv run flash run
```

## Dependency Types

### 1. Python Dependencies

Specified in the `Endpoint` decorator:

```python
@Endpoint(
    name="my-worker",
    gpu=GpuGroup.ADA_24,
    dependencies=[
        "requests==2.32.3",  # Exact version
        "Pillow>=10.0.0",    # Minimum version
        "python-dateutil<3.0.0",  # Maximum version
        "httpx",             # Latest version
    ]
)
async def my_function(data: dict) -> dict:
    import httpx
    import requests
    # your code here
```

Note: `torch` is already baked into the default GPU base image, so you generally should not add it to `dependencies` unless you intentionally need to override the bundled version.

### 2. System Dependencies

Install apt packages:

```python
@Endpoint(
    name="my-worker",
    gpu=GpuGroup.AMPERE_16,
    dependencies=["opencv-python"],
    system_dependencies=["ffmpeg", "libgl1", "graphviz"],
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
@Endpoint(name="my-worker", cpu="cpu3c-1-2")
async def simple_function(data: dict) -> dict:
    # only Python stdlib
    import json
    import re
    from datetime import datetime
    return {"result": "processed"}
```

## Version Constraints

### Exact Version (==)
```python
"requests==2.32.3"  # Exactly 2.32.3
```
**Use when:** You need reproducible builds

### Minimum Version (>=)
```python
"Pillow>=10.0.0"  # 10.0.0 or higher
```
**Use when:** You need specific features introduced in a version

### Maximum Version (<)
```python
"python-dateutil<3.0.0"  # Below 3.0.0
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
@Endpoint(
    name="worker",
    gpu=GpuGroup.ADA_24,
    dependencies=[
        "requests==2.32.3",
        "transformers==4.35.2",
        "numpy==1.26.2",
    ],
)

# Bad - Unpredictable
@Endpoint(
    name="worker",
    gpu=GpuGroup.ADA_24,
    dependencies=[
        "requests",  # Version changes over time
        "transformers",
        "numpy",
    ],
)
```

### 2. Minimize Dependencies

```python
# Good - Only what's needed
@Endpoint(name="fetcher", cpu="cpu3c-1-2", dependencies=["requests"])
async def fetch_data(url: str):
    import requests
    return requests.get(url).json()

# Bad - Unnecessary bloat
@Endpoint(
    name="fetcher",
    cpu="cpu3c-1-2",
    dependencies=["requests", "pandas", "numpy", "scipy"],
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
@Endpoint(
    name="worker",
    gpu=GpuGroup.ADA_24,
    dependencies=[
        "requests==2.32.3",  # API calls
        "Pillow>=10.0.0",    # Image processing
        "python-dateutil<3.0.0",  # Date parsing compatibility
    ]
)
async def process_image(data: dict):
    """Process image with Pillow and lightweight utility libraries."""
    pass
```

## Troubleshooting

### Import Error

```
ModuleNotFoundError: No module named 'PIL'
```

**Solution:** Add to dependencies:
```python
dependencies=["Pillow>=10.0.0"]
```

### Version Conflict

```
ERROR: Cannot install requests==2.25.0 and urllib3==2.2.1
because these package versions have conflicting dependencies.
```

**Solution:** Check compatibility matrix, adjust versions:
```python
dependencies=[
    "requests>=2.32.0",
    "urllib3>=2.2.0",
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
3. Keep workers warm (`workers=(1, 3)`)

## Cold Start Times

| Dependencies | Cold Start Time |
|-------------|-----------------|
| None | ~5-10 seconds |
| Small (1-2 packages) | ~15-30 seconds |
| Medium (3-5 packages) | ~30-60 seconds |
| Large (transformers, diffusers) | ~60-120 seconds |

## Requirements.txt

For local development, create `requirements.txt`:

```txt
runpod-flash
transformers==4.35.2
Pillow>=10.0.0
numpy==1.26.2
```

**Note:** Worker dependencies in the `Endpoint` decorator are deployed automatically. `requirements.txt` is for local development only.

## Advanced: External Docker Images

For complex dependencies, deploy a pre-built image:

```python
from runpod_flash import Endpoint, GpuGroup

vllm = Endpoint(
    name="vllm-service",
    image="vllm/vllm-openai:latest",
    gpu=GpuGroup.ADA_24,
)

# call it as an API client
result = await vllm.post("/v1/completions", {"prompt": "hello"})
```

## Next Steps

- **02_ml_inference** - Deploy real ML models
- **03_advanced_workers** - Caching and optimization
- **04_scaling_performance** - Production patterns

## Resources

- [PyPI Package Index](https://pypi.org/)
- [Ubuntu Package Search](https://packages.ubuntu.com/)
- [Runpod Docker Images](https://github.com/runpod/containers)
