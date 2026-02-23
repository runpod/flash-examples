# Custom Docker Images

Deploy pre-built Docker images to RunPod's serverless infrastructure using Flash's `ServerlessEndpoint` resource type.

## Overview

Flash provides two deployment modes:

1. **Managed** (`LiveServerless`): Flash packages your code and dependencies automatically. Best for most use cases.
2. **Custom Docker** (`ServerlessEndpoint`): Bring your own Docker image. Best when you need specific system libraries, CUDA versions, or pre-built model caches.

This example demonstrates both approaches side-by-side.

## What You'll Learn

- Using `ServerlessEndpoint` with `dockerImage` for custom containers
- Configuring environment variables for Docker-based workers
- Choosing between managed and custom Docker deployment
- Using RunPod's official Docker images (PyTorch, vLLM, etc.)

## Quick Start

### Prerequisites

- Python 3.10+
- RunPod API key ([get one here](https://docs.runpod.io/get-started/api-keys))

### Setup

```bash
cd 03_advanced_workers/02_docker_images
cp .env.example .env
# Add your RUNPOD_API_KEY to .env
```

### Run

```bash
flash run
```

Server starts at http://localhost:8888. Visit http://localhost:8888/docs for interactive API documentation.

### Test Endpoints

```bash
# Managed infrastructure worker
curl -X POST http://localhost:8888/gpu_worker/run_sync \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello from managed worker!"}'

# Custom Docker image worker
curl -X POST http://localhost:8888/gpu_worker/run_sync \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is serverless?", "max_tokens": 128}'

# Custom CUDA image - GPU info
curl -X POST http://localhost:8888/gpu_worker/run_sync \
  -H "Content-Type: application/json" \
  -d '{"operation": "info"}'

# Custom CUDA image - matrix multiply benchmark
curl -X POST http://localhost:8888/gpu_worker/run_sync \
  -H "Content-Type: application/json" \
  -d '{"operation": "matmul", "size": 2048}'
```

## When to Use Custom Docker Images

| Scenario | Approach | Resource Type |
|----------|----------|---------------|
| Standard Python dependencies | Managed | `LiveServerless` |
| Need specific CUDA version | Custom Docker | `ServerlessEndpoint` |
| Pre-built model weights in image | Custom Docker | `ServerlessEndpoint` |
| Complex system libraries (FFmpeg, OpenCV, etc.) | Either | Either |
| Using RunPod worker images (vLLM, TGI, etc.) | Custom Docker | `ServerlessEndpoint` |
| Rapid prototyping | Managed | `LiveServerless` |

## Configuration Reference

### ServerlessEndpoint (Custom Docker)

```python
from runpod_flash import ServerlessEndpoint, remote

config = ServerlessEndpoint(
    name="my_worker",                                    # Unique name
    dockerImage="runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04",  # Docker image
    gpuIds=["NVIDIA GeForce RTX 4090"],                 # GPU type(s)
    workersMin=0,                                        # Min workers (0 = scale to zero)
    workersMax=3,                                        # Max concurrent workers
    idleTimeout=300,                                     # Seconds before scale-down
    env={                                                # Environment variables
        "MODEL_NAME": "my-model",
        "CUDA_VISIBLE_DEVICES": "0",
    },
)

@remote(resource_config=config)
async def my_function(input_data: dict) -> dict:
    # Code runs inside the Docker container
    pass
```

### LiveServerless (Managed)

```python
from runpod_flash import GpuGroup, LiveServerless, remote

config = LiveServerless(
    name="my_worker",
    gpus=[GpuGroup.ADA_24],       # GPU selection
    workersMin=0,
    workersMax=3,
    idleTimeout=5,
)

@remote(resource_config=config, dependencies=["torch", "transformers"])
async def my_function(input_data: dict) -> dict:
    # Flash packages and deploys your code automatically
    pass
```

## RunPod Official Docker Images

RunPod provides official images for common workloads:

| Image | Use Case |
|-------|----------|
| `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04` | PyTorch with CUDA |
| `runpod/worker-v1-vllm-v1:stable-cuda12.8.1` | vLLM inference server |
| `runpod/stable-diffusion:web-automatic` | Stable Diffusion (Automatic1111) |

Browse all images at [Docker Hub: runpod](https://hub.docker.com/u/runpod) or [GitHub: runpod-workers](https://github.com/runpod-workers).

## Building Your Own Docker Image

For a custom Docker image to work with RunPod serverless, it must implement the RunPod handler protocol:

```dockerfile
FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

# Install your dependencies
RUN pip install transformers accelerate

# Copy your handler
COPY handler.py /handler.py

# RunPod entry point
CMD ["python", "-u", "/handler.py"]
```

The handler uses the `runpod` Python package:

```python
import runpod

def handler(job):
    input_data = job["input"]
    # Your inference logic here
    return {"result": "processed"}

runpod.serverless.start({"handler": handler})
```

See [RunPod Worker Documentation](https://docs.runpod.io/serverless/workers/overview) for details.

## Deployment

```bash
# Build the application
flash build

# Deploy to RunPod
flash deploy
```

For custom Docker images, Flash creates endpoints using your specified image instead of building one from your code.

## Cost Estimates

- Workers scale to 0 when idle (no charges)
- Pay only for GPU time during active requests
- Cold start: 30-60s (pulling Docker image on first run)
- Subsequent requests: depends on model and image size

## Common Issues

- **Image pull timeout**: Large Docker images (>10GB) may time out on first pull. Use smaller base images or pre-cache models in network volumes.
- **Handler not found**: Ensure your Docker image implements the RunPod handler protocol with `runpod.serverless.start()`.
- **GPU mismatch**: The `gpuIds` must match available GPU types in your RunPod account. Check the [GPU Types](https://docs.runpod.io/references/gpu-types) documentation.
- **Environment variables not set**: Verify `env` dict keys/values in `ServerlessEndpoint` config. Check endpoint logs in the RunPod console.

## Project Structure

```
02_docker_images/
├── gpu_worker.py        # Three workers: managed, custom Docker, custom CUDA
├── pyproject.toml       # Project metadata
└── README.md            # This file
```

## Next Steps

- See [02_ml_inference/02_vllm](../../02_ml_inference/02_vllm/) for a vLLM-specific Docker image example
- See [05_data_workflows/01_network_volumes](../../05_data_workflows/01_network_volumes/) for mounting shared storage
- See [03_advanced_workers/05_load_balancer](../05_load_balancer/) for custom HTTP routing

## References

- [RunPod Docker Hub](https://hub.docker.com/u/runpod)
- [RunPod Worker Images](https://github.com/runpod-workers)
- [RunPod Serverless Workers](https://docs.runpod.io/serverless/workers/overview)
- [Flash Documentation](https://docs.runpod.io)
