# Runpod Flash Examples

A collection of example applications showcasing Runpod Flash - a framework for building production-ready AI applications with distributed GPU and CPU computing.

## What is Flash?

Flash is a CLI tool and framework from the `tetra_rp` package that enables you to build FastAPI applications with workers that run on Runpod's serverless infrastructure. Write your code locally, and Flash handles deployment, scaling, and resource management.

## Prerequisites

- Python 3.11+ (3.12 recommended)
- [Runpod Account](https://console.runpod.io/signup)
- [Runpod API Key](https://docs.runpod.io/get-started/api-keys)
- Flash CLI: `pip install tetra_rp`

## Quick Start

```bash
# Clone the repository
git clone https://github.com/runpod/flash-examples.git
cd flash-examples

# Navigate to an example
cd 01_getting_started/01_hello_world

# Install dependencies
pip install -r requirements.txt

# Set your API key
echo "RUNPOD_API_KEY=your_key_here" > .env

# Run locally
flash run

# Visit http://localhost:8000/docs
```

## Examples by Category

### 01 - Getting Started
Learn the fundamentals of Flash applications.

- **[01_hello_world](./sample_getting_started/)** - Simplest GPU and CPU workers with FastAPI
- 02_cpu_worker - CPU-only worker example _(coming soon)_
- 03_mixed_workers - Combining GPU and CPU workers _(coming soon)_
- 04_dependencies - Managing Python and system dependencies _(coming soon)_

### 02 - ML Inference
Deploy machine learning models as APIs.

- 01_text_generation - LLM inference (Llama, Mistral, etc.) _(coming soon)_
- 02_image_generation - Stable Diffusion image generation _(coming soon)_
- 03_embeddings - Text embeddings API _(coming soon)_
- 04_multimodal - Vision-language models _(coming soon)_

### 03 - Advanced Workers
Production-ready worker patterns.

- 01_streaming - Streaming responses (SSE/WebSocket) _(coming soon)_
- 02_batch_processing - Batch inference optimization _(coming soon)_
- 03_caching - Model and result caching strategies _(coming soon)_
- 04_custom_images - Custom Docker images _(coming soon)_

### 04 - Scaling & Performance
Optimize for production workloads.

- 01_autoscaling - Worker autoscaling configuration _(coming soon)_
- 02_gpu_optimization - GPU memory management _(coming soon)_
- 03_concurrency - Async patterns and concurrency _(coming soon)_
- 04_monitoring - Logging, metrics, and observability _(coming soon)_

### 05 - Data Workflows
Handle data storage and processing.

- 01_network_volumes - Persistent storage with network volumes _(coming soon)_
- 02_file_upload - Handling file uploads _(coming soon)_
- 03_data_pipelines - ETL workflows _(coming soon)_
- 04_s3_integration - Cloud storage integration _(coming soon)_

### 06 - Real World Applications
Complete production-ready applications.

- 01_chatbot_api - Production chatbot service _(coming soon)_
- 02_image_api - Image processing service _(coming soon)_
- 03_audio_transcription - Whisper transcription service _(coming soon)_
- 04_multimodel_pipeline - Complex multi-stage workflows _(coming soon)_

## Learning Path

**New to Flash?** Start here:
1. [01_getting_started/01_hello_world](./sample_getting_started/) - Understand the basics
2. 02_ml_inference/01_text_generation - Deploy your first model
3. 04_scaling_performance/01_autoscaling - Learn production patterns

**Coming from Modal?**
Flash is FastAPI-centric for building production applications, while Modal focuses on standalone functions. Flash provides structured application development with built-in routing and deployment management.

**Production Deployment?**
1. Review examples in `04_scaling_performance/`
2. Study `06_real_world/` for complete architectures
3. Check deployment docs in each example's README

## Flash CLI Commands

```bash
flash init              # Create new Flash project
flash run              # Run development server (default: localhost:8000)
flash build            # Build application for deployment
flash deploy new <env> # Create deployment environment
flash deploy send <env># Deploy to Runpod
```

## Example Structure

Each example follows this structure:

```
example_name/
├── README.md              # Documentation and deployment guide
├── main.py               # FastAPI application entry point
├── workers/              # Remote worker functions
│   ├── gpu/              # GPU workers
│   │   ├── __init__.py   # FastAPI router
│   │   └── endpoint.py   # @remote decorated functions
│   └── cpu/              # CPU workers
│       ├── __init__.py
│       └── endpoint.py
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Project configuration
└── .env.example          # Environment variable template
```

## Key Concepts

### Remote Workers

The `@remote` decorator marks functions for execution on Runpod's serverless infrastructure:

```python
from tetra_rp import remote, LiveServerless, GpuGroup

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

**GPU Workers** (`LiveServerless`):
- `GpuGroup.ADA_24` - RTX 4090 (24GB)
- `GpuGroup.ADA_48_PRO` - RTX 6000 Ada, L40 (48GB)
- `GpuGroup.AMPERE_80` - A100 (80GB)

**CPU Workers** (`CpuLiveServerless`):
- `CpuInstanceType.CPU3G_2_8` - 2 vCPU, 8GB RAM
- `CpuInstanceType.CPU3C_4_8` - 4 vCPU, 8GB RAM (Compute)
- `CpuInstanceType.CPU5G_4_16` - 4 vCPU, 16GB RAM (Latest)

### Auto-Scaling

Workers automatically scale based on demand:
- `workersMin=0` - Scale to zero when idle (cost-efficient)
- `workersMax=N` - Maximum concurrent workers
- `idleTimeout=5` - Minutes before scaling down

## Contributing

We welcome contributions! See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

To add a new example:
1. Follow the standard example structure
2. Include comprehensive README with deployment steps
3. Add tests for critical functionality
4. Ensure all dependencies are pinned in requirements.txt
5. Test deployment with `flash deploy`

## Resources

- [Flash CLI Documentation](https://github.com/runpod/tetra-rp)
- [Runpod Serverless Docs](https://docs.runpod.io/serverless/overview)
- [Tetra SDK Reference](https://github.com/runpod/tetra-rp)
- [Community Discord](https://discord.gg/runpod)

## Testing

All examples are continuously tested against Python 3.12 to ensure correctness. See [.github/workflows/test-examples.yml](./.github/workflows/test-examples.yml) for details.

## License

MIT License - see [LICENSE](./LICENSE) for details.

