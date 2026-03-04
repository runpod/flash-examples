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

> **Don't have uv?** Install it with `curl -LsSf https://astral.sh/uv/install.sh | sh` or see [DEVELOPMENT.md](./DEVELOPMENT.md) for pip/poetry/conda alternatives.

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

### Remote Workers

The `@remote` decorator marks functions for execution on Runpod's serverless infrastructure:

```python
from runpod_flash import remote, LiveServerless, GpuGroup

config = LiveServerless(
    name="my_worker",
    gpus=[GpuGroup.ADA_24],  # RTX 4090
    workersMin=0,            # Scale to zero when idle
    workersMax=3,            # Maximum concurrent workers
)

@remote(resource_config=config, dependencies=["torch"])
async def process(data: dict) -> dict:
    import torch
    # This code runs on Runpod GPUs
    return {"result": "processed"}
```

### Resource Types

| Type | Use Case |
|------|----------|
| `LiveServerless` + `GpuGroup` | GPU workers (ADA_24, ADA_48_PRO, AMPERE_80) |
| `CpuLiveServerless` + `CpuInstanceType` | CPU-only workers |
| `LiveLoadBalancer` / `CpuLiveLoadBalancer` | Load-balanced endpoints |

### Auto-Scaling

Workers automatically scale based on demand:
- `workersMin=0` - Scale to zero when idle (cost-efficient)
- `workersMax=N` - Maximum concurrent workers
- `idleTimeout=5` - Minutes before scaling down

## Resources

- [Flash Documentation](https://docs.runpod.io)
- [Runpod Serverless Docs](https://docs.runpod.io/serverless/overview)
- [Community Discord](https://discord.gg/runpod)

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for contribution guidelines and [DEVELOPMENT.md](./DEVELOPMENT.md) for development setup.

## License

MIT License - see [LICENSE](./LICENSE) for details.
