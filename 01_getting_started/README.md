# 01 - Getting Started

Fundamental concepts for building Flash applications. Start here if you're new to Runpod Flash.

## Examples

### [01_hello_world](./01_hello_world/)
The simplest Flash application with GPU workers

**What you'll learn:**
- Basic Flash application structure
- Creating GPU workers
- Using the `@Endpoint` decorator
- Running Flash applications locally
- Testing endpoints with Swagger docs

**Concepts:**
- `Endpoint` with `gpu=` parameter for GPU workers
- Worker auto-scaling via `workers=(min, max)`

### [02_cpu_worker](./02_cpu_worker/)
CPU-only worker example for non-GPU workloads.

**What you'll learn:**
- When to use CPU-only workers
- Cost optimization with CPU instances
- CPU instance type selection
- Handling API requests without GPU overhead

### [03_mixed_workers](./03_mixed_workers/)
Mixed GPU/CPU workers for cost-effective ML pipelines.

**What you'll learn:**
- Mixed worker architecture (CPU preprocessing → GPU inference → CPU postprocessing)
- Cost optimization (85% savings vs GPU-only pipeline)
- Pipeline orchestration patterns
- Fail-fast validation before expensive GPU operations

**Concepts:**
- CPU `Endpoint` for preprocessing and postprocessing
- Pipeline orchestration with load-balanced endpoints

### [04_dependencies](./04_dependencies/)
Managing Python packages and system dependencies.

**What you'll learn:**
- Python dependency versioning and constraints
- System package installation (ffmpeg, libgl1)
- Version constraints (==, >=, <, ~=)
- Minimizing cold start time
- Best practices for reproducible builds

**Concepts:**
- `dependencies` parameter for Python packages
- `system_dependencies` parameter for apt packages
- Version pinning for reproducibility
- Dependency optimization strategies

### [05_local_modules](./05_local_modules/)
Factoring endpoint logic across local (non-pip) Python files.

**What you'll learn:**
- Importing a local sibling module from an endpoint
- Importing a local package whose `__init__` re-exports from a submodule
- Why endpoint imports belong inside the function body
- How the build path resolves and bundles local modules

**Concepts:**
- Local-module resolution: the endpoint's import closure ships alongside the function
- In-function imports as a requirement on the live path, and a no-op on the deploy path
- Endpoint imports override the build's ignore filter

## Learning Path

1. Start with **01_hello_world** to understand the basics
2. Explore **03_mixed_workers** for cost optimization and validation patterns
3. Move to **02_cpu_worker** to learn CPU-only patterns
4. Master **04_dependencies** for production readiness
5. Finish with **05_local_modules** to split an endpoint across your own files

## Next Steps

After completing this section:
- Explore [02_ml_inference](../02_ml_inference/) to deploy ML models
- Learn [04_scaling_performance](../04_scaling_performance/) for production patterns
- Build complete applications in [06_real_world](../06_real_world/)
