# 04 - Dependency Management

Learn how to manage Python packages and system dependencies in Flash workers.

## What This Demonstrates

- **Python dependencies** - Installing packages with version constraints
- **System dependencies** - Installing apt packages (ffmpeg, libgl1, etc.)
- **GPU vs CPU packaging** - How dependencies are resolved differently per runtime
- **Shared dependencies** - GPU and CPU endpoints using the same package (numpy)
- **Version constraints** - Supported syntax for version pinning
- **Dependency optimization** - Minimizing cold start time

## Quick Start

**Prerequisites**: Complete the [repository setup](../../README.md#quick-start) first (clone, `make dev`, set API key).

### Files

| File | What it demonstrates |
|------|---------------------|
| `gpu_worker.py` | Python deps with version pins, system deps (ffmpeg, libgl1) |
| `cpu_worker.py` | Data science deps on CPU (numpy, pandas, scipy), zero-dep worker |
| `mixed_worker.py` | Same dependency (numpy) on both GPU and CPU endpoints |

> **Note:** `gpu_worker.py` uses `GpuGroup` while newer snippets in this README use `GpuType`. Both enums are supported by the SDK; `GpuType` is recommended for new code.

### Run This Example

```bash
cd 01_getting_started/04_dependencies

# Run any worker directly
python gpu_worker.py
python cpu_worker.py
python mixed_worker.py
```

First run takes 30-60 seconds (provisioning). Subsequent runs take 2-3 seconds.

### Setup (if needed)

```bash
# Install dependencies
uv sync

# Authenticate
uv run flash login
# Or create .env file with RUNPOD_API_KEY=your_api_key_here
```

### Alternative: HTTP API Testing

To test via HTTP endpoints:

```bash
uv run flash run
```

Server starts at http://localhost:8888

## GPU vs CPU Packaging

GPU and CPU endpoints use different base Docker images, which affects how dependencies are resolved:

| | GPU images (`runpod/pytorch:*`) | CPU images (`python:X.Y-slim`) |
|---|---|---|
| **Base image** | PyTorch + CUDA + numpy + triton | Python stdlib only |
| **Pre-installed** | torch, torchvision, torchaudio, numpy, triton | Nothing |
| **Build artifact** | Excludes torch ecosystem (too large for 500 MB tarball) | Includes everything declared in `dependencies` |

**What this means for you:**

- **GPU endpoints**: `torch`, `torchvision`, `torchaudio`, and `triton` are excluded from the build artifact because they already exist in the base image and would exceed the 500 MB tarball limit. All other dependencies (including `numpy`) are packaged normally.
- **CPU endpoints**: Every dependency must be in the build artifact. Nothing is pre-installed.
- **Mixed projects**: When GPU and CPU endpoints share a dependency like `numpy`, it ships in the tarball. The GPU image ignores the duplicate (its pre-installed copy takes precedence).

See `mixed_worker.py` for a working example of GPU and CPU endpoints sharing `numpy`.

**Safety net**: If a dependency is missing from the build artifact at runtime, the worker attempts to install it on-the-fly and logs a warning. This prevents crashes but adds to cold start time. Always declare your dependencies explicitly to avoid this penalty.

## Dependency Types

### 1. Python Dependencies

Specified in the `Endpoint` decorator:

```python
@Endpoint(
    name="my-worker",
    gpu=GpuType.NVIDIA_GEFORCE_RTX_4090,
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
    gpu=GpuType.NVIDIA_GEFORCE_RTX_4090,
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
**Use when:** You need reproducible builds for a specific Python version

### Minimum Version (>=)
```python
"Pillow>=10.0.0"  # 10.0.0 or higher
```
**Use when:** You need specific features introduced in a version

### Maximum Version (<)
```python
"python-dateutil<3.0.0"  # Below 3.0.0
```
**Use when:** Avoiding breaking changes in a major release

### Compatible Release (~=)
```python
"requests~=2.31.0"  # >=2.31.0, <2.32.0
```
**Use when:** You want patch updates but not minor updates

### Latest Version
```python
"pandas"  # Latest available
```
**Use when:** You want the latest compatible version (recommended for examples and prototyping)

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
    "pandas",
    "numpy",
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

### 1. Use Version Constraints Thoughtfully

```python
# Good for examples and prototyping - works across Python versions
dependencies=[
    "requests",
    "transformers",
    "numpy",
]

# Good for production - reproducible on a known Python version
dependencies=[
    "requests==2.32.3",
    "transformers==4.35.2",
    "numpy==1.26.2",
]
```

Exact pins can break across Python versions (e.g., older numpy
builds don't exist for Python 3.13+). Pin only when you control
the target Python version.

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
    gpu=GpuType.NVIDIA_GEFORCE_RTX_4090,
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

**Solutions:**
1. Drop exact pins and let pip resolve compatible versions
2. Check compatibility matrix and adjust versions:
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
numpy
```

**Note:** Worker dependencies in the `Endpoint` decorator are deployed automatically. `requirements.txt` is for local development only.

## Build Exclusions

Flash automatically excludes packages that are too large for the 500 MB build artifact limit. Currently excluded: `torch`, `torchvision`, `torchaudio`, `triton` (all CUDA-specific, pre-installed in GPU images).

You can exclude additional large packages with `--exclude`:

```bash
# Exclude tensorflow from the build artifact
flash build --exclude tensorflow
```

**Important:** Only exclude packages that are pre-installed in your target runtime. If you exclude a package that a CPU endpoint needs, the worker will attempt to install it on-the-fly at startup. This works but adds to cold start time and logs a warning:

```
WARNING - Package 'scipy' is not in the build artifact. Installing on-the-fly.
This adds to cold start time -- consider adding it to your dependencies list
to include it in the build artifact.
```

## Advanced: External Docker Images

For complex dependencies, deploy a pre-built image:

```python
from runpod_flash import Endpoint, GpuType

vllm = Endpoint(
    name="vllm-service",
    image="vllm/vllm-openai:latest",
    gpu=GpuType.NVIDIA_GEFORCE_RTX_4090,
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
