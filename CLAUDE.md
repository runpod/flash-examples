# Flash Examples: AI Coding Assistant Guidelines

Instructions for AI coding assistants working on the flash-examples repository.

## Project Overview

Production-ready examples demonstrating Flash framework capabilities. Each example is a flat directory of standalone worker files auto-discovered by `flash run`.

## Architecture: Flat-File Pattern

No FastAPI boilerplate, no routers, no `main.py`, no `mothership.py`. Each worker is a self-contained file with a `@remote` decorator.

```
example_name/
├── README.md
├── gpu_worker.py      # @remote decorated functions
├── cpu_worker.py      # Optional CPU worker
└── pipeline.py        # Optional cross-worker orchestration
```

### Worker File Pattern

```python
from runpod_flash import GpuGroup, LiveServerless, remote

gpu_config = LiveServerless(
    name="01_01_gpu_worker",
    gpus=[GpuGroup.ANY],
    workersMin=0,
    workersMax=3,
    idleTimeout=5,
)

@remote(resource_config=gpu_config)
async def my_function(input_data: dict) -> dict:
    """All imports inside the function body."""
    import torch
    # implementation
    return {"status": "success"}
```

Key rules:
- Imports from `runpod_flash`, not `flash`
- Config object at module level (`LiveServerless`, `CpuLiveLoadBalancer`, `CpuLiveServerless`)
- All runtime imports inside the `@remote` function body
- Return serializable data (dict, list, str)
- Worker naming convention: `{category}_{example}_{worker_type}` (e.g., `01_01_gpu_worker`)

### Resource Types

| Type | Import | Use Case |
|------|--------|----------|
| `LiveServerless` | `from runpod_flash import LiveServerless, GpuGroup` | GPU workers |
| `CpuLiveLoadBalancer` | `from runpod_flash import CpuLiveLoadBalancer` | CPU workers, pipelines |
| `CpuLiveServerless` | `from runpod_flash import CpuLiveServerless` | CPU serverless |

### Cross-Worker Orchestration

Pipeline files import functions from other workers and chain them:

```python
from cpu_worker import preprocess_text
from gpu_worker import gpu_inference
from runpod_flash import CpuLiveLoadBalancer, remote

pipeline_config = CpuLiveLoadBalancer(name="pipeline", workersMin=1)

@remote(resource_config=pipeline_config, method="POST", path="/classify")
async def classify(text: str) -> dict:
    result = await preprocess_text({"text": text})
    return await gpu_inference(result)
```

## Creating New Examples

Always use `flash init`:

```bash
cd 01_getting_started
flash init my_new_example
```

Never copy-paste existing examples.

## Development Workflow

```bash
flash run                    # Start local dev server (localhost:8888)
# Visit http://localhost:8888/docs for interactive API docs
python gpu_worker.py         # Test a single worker directly
```

## Quality Gates

```bash
make quality-check           # Required before every commit
make lint                    # Ruff linter
make format-check            # Ruff format check
```

## Code Standards

- Type hints on all function signatures
- Early returns / guard clauses over nested conditions
- No hardcoded credentials (use `os.getenv()`)
- No `print()` in production code (logging module or skip for examples)
- Catch specific exceptions, never bare `except:`

## Common Mistakes

1. **Accessing external scope in @remote functions** -- only local variables, parameters, and internal imports work
2. **Module-level imports of heavy libraries** -- import torch, numpy, etc. inside the function body
3. **Missing `if __name__ == "__main__"` test block** -- each worker should be independently testable
4. **Mutable default arguments** -- use `None` and initialize in function body
