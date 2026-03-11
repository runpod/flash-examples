# Runpod Flash Examples

A collection of example applications showcasing Runpod Flash - a framework for building production-ready AI applications with distributed GPU and CPU computing.

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

- **Python 3.10-3.12**
- **uv**: Install with `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Runpod account**: [Sign up here](https://runpod.io/console/signup)

## Resources

- [Flash documentation](https://docs.runpod.io/flash/overview)
- [Community Discord](https://discord.gg/runpod)

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for contribution guidelines and [DEVELOPMENT.md](./DEVELOPMENT.md) for development setup.

## License

MIT License - see [LICENSE](./LICENSE) for details.
