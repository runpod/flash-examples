# Runpod Flash Examples

A collection of example applications showcasing Runpod Flash - a framework for building production-ready AI applications with distributed GPU and CPU computing.

## What is Flash?

Flash is a CLI tool and framework from the `runpod_flash` package that enables you to build FastAPI applications with workers that run on Runpod's serverless infrastructure. Write your code locally, and Flash handles deployment, scaling, and resource management.

## Prerequisites

- Python 3.10+ (3.12 recommended)
- [Runpod Account](https://console.runpod.io/signup)
- [Runpod API Key](https://docs.runpod.io/get-started/api-keys)
- Flash CLI: `pip install runpod_flash`

## Quick Start

```bash
# Clone the repository
git clone https://github.com/runpod/flash-examples.git
cd flash-examples

# Setup development environment (auto-detects package manager)
make setup

# The setup will:
# - Create virtual environment
# - Install all dependencies
# - Create .env file from template
# - Verify your setup

# Add your API key to .env file
# Get your key from: https://www.runpod.io/console/user/settings
nano .env  # or use your preferred editor

# Run all examples from the unified app (recommended)
flash run

# Visit http://localhost:8888/docs
```

**Verification:**
After setup, verify your environment is correct:
```bash
make verify-setup
```

This checks:
- Python version (3.10+ required)
- Virtual environment exists
- Flash CLI is installed
- API key is configured

**Alternative Setup Methods:**
- **With Makefile**: `make setup` (auto-detects your package manager)
- **With uv**: `uv sync && uv pip install -e .`
- **With pip**: `pip install -e .`
- **With poetry**: `poetry install`

**Using Different Package Managers:**

The setup automatically detects and uses your available package manager in this order:
1. uv
2. poetry
3. pipenv
4. pip (standard Python package manager)
5. conda

To explicitly use a specific package manager:

```bash
# Force pip usage
PKG_MANAGER=pip make setup

# Force poetry
PKG_MANAGER=poetry make setup

# Force conda
PKG_MANAGER=conda make setup
```

**Running Flash Examples:**

After `make setup` completes, you can run Flash in two ways:

**Option A: Using Package Manager Prefix (recommended for uv/poetry/pipenv/conda)**

With uv, poetry, pipenv, or conda, run commands with the package manager prefix without activation:

```bash
# With uv
uv run flash run

# With poetry
poetry run flash run

# With pipenv
pipenv run flash run

# With conda
conda run -p ./.venv flash run
```

**Option B: Activate Virtual Environment (works with all managers)**

Alternatively, activate the virtual environment first:

```bash
# Unix/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate

# Then run normally
flash run
```

Once activated, you can run Flash and other commands directly without a prefix.

**Note**: After running `make setup`, all example dependencies are installed. You can navigate to any example directory and run `flash run` immediately. The `make setup` command will show you the recommended next steps based on your detected package manager.

For detailed development instructions, see [DEVELOPMENT.md](./DEVELOPMENT.md).

## Examples by Category

### 01 - Getting Started
Learn the fundamentals of Flash applications.

- **[01_hello_world](./01_getting_started/01_hello_world/)** - The simplest Flash application with GPU workers
- **[02_cpu_worker](./01_getting_started/02_cpu_worker/)** - CPU-only worker example
- **[03_mixed_workers](./01_getting_started/03_mixed_workers/)** - Mixed GPU/CPU workers with cost optimization and validation
- **[04_dependencies](./01_getting_started/04_dependencies/)** - Managing Python and system dependencies

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
- **[05_load_balancer](./03_advanced_workers/05_load_balancer/)** - Load-balancer endpoints with custom HTTP routes

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
1. [01_getting_started/01_hello_world](./01_getting_started/01_hello_world/) - Understand the basics
2. [01_getting_started/03_mixed_workers](./01_getting_started/03_mixed_workers/) - Learn cost optimization and validation patterns
3. 02_ml_inference/01_text_generation - Deploy your first model

**Coming from Modal?**
Flash is FastAPI-centric for building production applications, while Modal focuses on standalone functions. Flash provides structured application development with built-in routing and deployment management.

**Production Deployment?**
1. Review examples in `04_scaling_performance/`
2. Study `06_real_world/` for complete architectures
3. Check deployment docs in each example's README

## Flash CLI Commands

The Flash CLI provides a complete toolkit for building, testing, and deploying distributed inference applications.

### Core Commands

```bash
flash init [project]         # Create new Flash project
flash run                    # Run development server (localhost:8888)
flash build                  # Build deployment package
flash deploy --env <name>    # Build and deploy to environment
flash undeploy <name>        # Delete deployed endpoint
```

### Environment Management

```bash
flash env list               # Show all environments
flash env create <name>      # Create new environment (dev, staging, prod)
flash env get <name>         # Show environment details
flash env delete <name>      # Delete environment
```

### Application Management

```bash
flash app list               # List all Flash apps
flash app create <name>      # Create new app
flash app get <name>         # Show app details
flash app delete --app <name># Delete app and all resources
```

### Command Options

Many commands support additional options for customization:

```bash
flash run --host 0.0.0.0 --port 9000     # Custom host and port
flash build --exclude torch,torchvision   # Exclude packages (reduce size)
flash deploy --env prod --preview         # Local preview before deploying
flash undeploy --all --force              # Remove all endpoints
```

### Full Documentation

**[Complete CLI Reference](CLI-REFERENCE.md)** - Comprehensive guide with all commands, options, and examples

**Step-by-Step Guides:**
- [Getting Started (5 minutes)](docs/cli/getting-started.md) - Your first Flash project
- [Command Reference](docs/cli/commands.md) - Exhaustive documentation for all commands
- [Workflows](docs/cli/workflows.md) - Common development workflows
- [Troubleshooting](docs/cli/troubleshooting.md) - Solutions to common problems

### Quick Start

```bash
# 1. Create project
flash init my-api && cd my-api

# 2. Run locally
flash run
# Visit http://localhost:8888/docs

# 3. Create environment and deploy
flash env create production
flash deploy --env production
```

## Testing Your Application

After running `flash run`, you can test your API in two ways:

**Option A: Using the Interactive UI**

Visit **http://localhost:8888/docs** to use FastAPI's built-in Swagger UI where you can:
- See all available endpoints
- Test requests directly in your browser
- View request/response schemas

**Option B: Using curl**

Test endpoints from the command line:
```bash
curl -X POST http://localhost:8888/endpoint \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'
```

See individual example READMEs for specific endpoint examples.

## Unified App Architecture

The root [main.py](main.py) provides a programmatic discovery system that automatically finds and loads all examples:

**Discovery Process**:
1. Scans all example category directories (`01_getting_started/`, `02_ml_inference/`, etc.)
2. Detects two patterns:
   - **Single-file workers**: `gpu_worker.py`, `cpu_worker.py` with `APIRouter` exports
   - **Directory-based workers**: `workers/gpu/__init__.py`, `workers/cpu/__init__.py` with `APIRouter` exports
3. Dynamically imports and registers all routers with unique prefixes (e.g., `/01_hello_world/gpu/`)
4. Generates metadata and documentation automatically

**Benefits**:
- Add new examples without modifying the unified app
- Consistent routing across all examples
- Single entry point for exploring all functionality
- Automatic discovery eliminates manual registration

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

### Dependency Management

The unified app automatically discovers and loads all examples at runtime, which requires all example dependencies to be installed in the root environment.

**Automatic Dependency Syncing**:

When adding a new example with additional dependencies:

1. Define dependencies in your example's `pyproject.toml`
2. Run `make sync-example-deps` to update the root dependencies
3. Run `uv sync --all-groups` to install the new packages
4. Run `make requirements.txt` to regenerate the lockfile

The sync script automatically:
- Scans all example directories for `pyproject.toml` files
- Merges dependencies into the root configuration
- Filters out transitive dependencies already provided by `runpod-flash`
- Detects version conflicts and uses the most permissive constraint
- Preserves essential root dependencies (numpy, torch, runpod-flash)

**Example**:

```bash
# After adding a new example with pillow and structlog dependencies
make sync-example-deps  # Syncs example deps to root pyproject.toml
uv sync --all-groups    # Installs new dependencies
make requirements.txt   # Regenerates lockfile
```

This automation ensures that `flash run` from the root directory always has access to all required dependencies for dynamic example loading.

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

We welcome contributions! See [CONTRIBUTING.md](./CONTRIBUTING.md) for contribution guidelines and [DEVELOPMENT.md](./DEVELOPMENT.md) for development setup.

To add a new example:
1. Follow the standard example structure
2. Include comprehensive README with deployment steps
3. Add tests for critical functionality
4. Ensure all dependencies are pinned in requirements.txt
5. Run `make quality-check` before committing
6. Test deployment with `flash deploy`

## Resources

- [Flash CLI Documentation](https://github.com/runpod/runpod-flash)
- [Runpod Serverless Docs](https://docs.runpod.io/serverless/overview)
- [Flash SDK Reference](https://github.com/runpod/runpod-flash)
- [Community Discord](https://discord.gg/runpod)

## Testing

All examples are continuously tested against Python 3.10-3.14 to ensure compatibility across all supported versions. See [.github/workflows/](./.github/workflows/) for CI configuration.

## License

MIT License - see [LICENSE](./LICENSE) for details.

