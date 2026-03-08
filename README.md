# Runpod Flash Examples

A collection of example applications showcasing Runpod Flash - a framework for building production-ready AI applications with distributed GPU and CPU computing.

## What is Flash?

Flash is a Python framework that lets you run functions on Runpod's Serverless infrastructure with a single decorator. Write code locally, deploy globally—Flash handles provisioning, scaling, and routing automatically.

```python
from runpod_flash import Endpoint, GpuType

@Endpoint(name="image-gen", gpu=GpuType.NVIDIA_GEFORCE_RTX_4090, dependencies=["torch", "diffusers"])
async def generate_image(prompt: str) -> bytes:
    # This runs on a cloud GPU, not your laptop
    ...
```

**Key features:**
- **`@Endpoint` decorator**: Mark any async function to run on serverless infrastructure
- **Auto-scaling**: Scale to zero when idle, scale up under load
- **Local development**: `flash run` starts a local server with hot reload
- **One-command deploy**: `flash deploy` packages and ships your code

## Prerequisites

- **Python 3.10+**
- **uv**: Install with `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Runpod account**: [Sign up here](https://runpod.io/console/signup)

### Python version in deployed workers

Your local Python version does not affect what runs in the cloud. `flash build` downloads wheels for the container's Python version automatically.

- **GPU workers**: Python 3.12 only. The GPU base image ships multiple interpreters (3.9-3.14) for interactive pod use, but torch and CUDA libraries are installed only for 3.12.
- **CPU workers**: Python 3.10, 3.11, or 3.12. Configurable via `PYTHON_VERSION` build arg.

## Quick Start

```bash
# Clone and install
git clone https://github.com/runpod/flash-examples.git
cd flash-examples
uv sync && uv pip install -e .

# Authenticate with Runpod
uv run flash login

# Run all examples locally
uv run flash run
```

Open **http://localhost:8888/docs** to explore all endpoints.

> **Using pip, poetry, or conda?** See [DEVELOPMENT.md](./DEVELOPMENT.md) for alternative setups.

## Examples

| Category | Example | Description |
|----------|---------|-------------|
| **Getting Started** | [01_hello_world](./01_getting_started/01_hello_world/) | Basic GPU worker |
| | [02_cpu_worker](./01_getting_started/02_cpu_worker/) | CPU-only worker |
| | [03_mixed_workers](./01_getting_started/03_mixed_workers/) | GPU + CPU pipeline |
| | [04_dependencies](./01_getting_started/04_dependencies/) | Dependency management |
| **ML Inference** | [01_text_to_speech](./02_ml_inference/01_text_to_speech/) | Qwen3-TTS model serving |
| **Advanced** | [05_load_balancer](./03_advanced_workers/05_load_balancer/) | HTTP routing with load balancer |
| **Scaling** | [01_autoscaling](./04_scaling_performance/01_autoscaling/) | Worker autoscaling configuration |
| **Data** | [01_network_volumes](./05_data_workflows/01_network_volumes/) | Persistent storage with network volumes |

More examples coming soon in each category.

## CLI Commands

```bash
flash login              # Authenticate with Runpod (opens browser)
flash run                # Run development server (localhost:8888)
flash build              # Build deployment package
flash deploy --env <name># Build and deploy to environment
flash undeploy <name>    # Delete deployed endpoint
```

See **[CLI-REFERENCE.md](./CLI-REFERENCE.md)** for complete documentation.

## Key Concepts

### Endpoint

The `Endpoint` class configures functions for execution on Runpod's serverless infrastructure:

**Queue-based (one function = one endpoint):**

```python
from runpod_flash import Endpoint, GpuType

@Endpoint(name="my-worker", gpu=GpuType.NVIDIA_GEFORCE_RTX_4090, workers=(0, 3), dependencies=["torch"])
async def process(data: dict) -> dict:
    import torch
    # this code runs on Runpod GPUs
    return {"result": "processed"}
```

**Load-balanced (multiple routes, shared workers):**

```python
from runpod_flash import Endpoint

api = Endpoint(name="my-api", cpu="cpu3c-1-2", workers=(1, 3))

@api.get("/health")
async def health():
    return {"status": "ok"}

@api.post("/compute")
async def compute(data: dict) -> dict:
    return {"result": data}
```

**Client mode (connect to an existing endpoint):**

```python
from runpod_flash import Endpoint

ep = Endpoint(id="ep-abc123")
job = await ep.run({"prompt": "hello"})
await job.wait()
print(job.output)
```

### Resource Types

**GPU Workers** (`gpu=`):
| Type | Use Case |
|------|----------|
| `GpuType.NVIDIA_GEFORCE_RTX_4090` | RTX 4090 (24GB) |
| `GpuType.NVIDIA_RTX_6000_ADA_GENERATION` | RTX 6000 Ada (48GB) |
| `GpuType.NVIDIA_A100_80GB_PCIe` | A100 (80GB) |

**CPU Workers** (`cpu=`):
| Type | Specs |
|------|-------|
| `cpu3g-2-8` | 2 vCPU, 8GB RAM |
| `cpu3c-4-8` | 4 vCPU, 8GB RAM (Compute) |
| `cpu5c-4-16` | 4 vCPU, 16GB RAM (Latest) |

### Auto-Scaling

Workers automatically scale based on demand:
- `workers=(0, 3)` - Scale from 0 to 3 workers (cost-efficient)
- `workers=(1, 5)` - Keep 1 warm, scale up to 5
- `idle_timeout=5` - Seconds before scaling down

## Resources

- [Flash documentation](https://docs.runpod.io/flash/overview)
- [Community Discord](https://discord.gg/runpod)

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for contribution guidelines and [DEVELOPMENT.md](./DEVELOPMENT.md) for development setup.

## License

MIT License - see [LICENSE](./LICENSE) for details.
