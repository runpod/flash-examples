"""
Unified Flash Examples Application

This file automatically discovers and consolidates all Flash examples into one FastAPI application.
Run `flash run` from the root directory to access all examples from a single server.

The discovery system automatically finds:
1. Single-file worker patterns (e.g., gpu_worker.py, cpu_worker.py)
2. Directory-based worker patterns (e.g., workers/gpu/__init__.py)
"""

import importlib.util
import logging
import os
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
EXAMPLES_DIRS = [
    BASE_DIR / "01_getting_started",
    BASE_DIR / "02_ml_inference",
    BASE_DIR / "03_advanced_workers",
    BASE_DIR / "04_scaling_performance",
    BASE_DIR / "05_data_workflows",
    BASE_DIR / "06_real_world",
]

app = FastAPI(
    title="Runpod Flash Examples - Unified Demo",
    description="All Flash examples automatically discovered and unified in one FastAPI application",
    version="1.0.0",
)


def load_module_from_path(module_name: str, file_path: Path) -> Any:
    """Dynamically load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def discover_single_file_routers(example_path: Path, example_name: str) -> list[dict]:
    """
    Discover routers from single-file worker patterns.

    Looks for files like gpu_worker.py, cpu_worker.py that export APIRouters.
    """
    routers = []
    worker_files = list(example_path.glob("*_worker.py"))

    for worker_file in worker_files:
        worker_type = worker_file.stem.replace("_worker", "")  # e.g., 'gpu' or 'cpu'
        module_name = f"{example_name}_{worker_type}_worker"

        try:
            module = load_module_from_path(module_name, worker_file)
            if module is None:
                continue

            # Look for router (common naming: gpu_router, cpu_router, etc.)
            router_name = f"{worker_type}_router"
            if hasattr(module, router_name):
                router = getattr(module, router_name)
                if isinstance(router, APIRouter):
                    routers.append({
                        "router": router,
                        "prefix": f"/{example_name}/{worker_type}",
                        "tags": [f"{example_name.replace('_', ' ').title()} - {worker_type.upper()}"],
                        "worker_type": worker_type,
                    })
                    logger.info(f"Loaded {example_name}/{worker_type} from {worker_file.name}")
        except Exception as e:
            logger.warning(f"Could not load {worker_file}: {e}")

    return routers


def discover_directory_routers(example_path: Path, example_name: str) -> list[dict]:
    """
    Discover routers from directory-based worker patterns.

    Looks for workers/gpu/__init__.py, workers/cpu/__init__.py that export APIRouters.
    """
    routers = []
    workers_dir = example_path / "workers"

    if not workers_dir.exists() or not workers_dir.is_dir():
        return routers

    # Add workers directory to path for imports
    workers_dir_str = str(workers_dir.parent)
    if workers_dir_str not in sys.path:
        sys.path.insert(0, workers_dir_str)

    # Look for worker type directories (gpu, cpu, etc.)
    for worker_dir in workers_dir.iterdir():
        if not worker_dir.is_dir() or worker_dir.name.startswith("_"):
            continue

        init_file = worker_dir / "__init__.py"
        if not init_file.exists():
            continue

        worker_type = worker_dir.name
        module_name = f"{example_name}_workers_{worker_type}"

        try:
            module = load_module_from_path(module_name, init_file)
            if module is None:
                continue

            # Look for router (common naming: gpu_router, cpu_router, etc.)
            router_name = f"{worker_type}_router"
            if hasattr(module, router_name):
                router = getattr(module, router_name)
                if isinstance(router, APIRouter):
                    routers.append({
                        "router": router,
                        "prefix": f"/{example_name}/{worker_type}",
                        "tags": [f"{example_name.replace('_', ' ').title()} - {worker_type.upper()}"],
                        "worker_type": worker_type,
                    })
                    logger.info(f"Loaded {example_name}/{worker_type} from workers/{worker_type}")
        except Exception as e:
            logger.warning(f"Could not load {worker_dir}: {e}")

    return routers


def discover_example_routers(example_path: Path) -> list[dict]:
    """
    Discover all routers from an example directory.

    Tries both single-file and directory-based patterns.
    """
    example_name = example_path.name
    routers = []

    # Try single-file pattern
    routers.extend(discover_single_file_routers(example_path, example_name))

    # Try directory-based pattern
    routers.extend(discover_directory_routers(example_path, example_name))

    return routers


def register_all_examples() -> dict[str, dict]:
    """
    Discover and register all examples.

    Returns a dictionary of example metadata for the home endpoint.
    """
    examples_metadata = {}

    for examples_dir in EXAMPLES_DIRS:
        if not examples_dir.exists() or not examples_dir.is_dir():
            continue

        # Iterate through example directories
        for example_path in sorted(examples_dir.iterdir()):
            if not example_path.is_dir() or example_path.name.startswith("."):
                continue

            example_name = example_path.name
            routers = discover_example_routers(example_path)

            if routers:
                # Register routers with FastAPI
                for router_info in routers:
                    app.include_router(
                        router_info["router"],
                        prefix=router_info["prefix"],
                        tags=router_info["tags"],
                    )

                # Build metadata
                examples_metadata[example_name] = {
                    "description": f"Example: {example_name.replace('_', ' ').title()}",
                    "endpoints": {
                        router_info["worker_type"]: f"{router_info['prefix']}/*"
                        for router_info in routers
                    },
                }

    return examples_metadata


# Discover and register all examples
examples_metadata = register_all_examples()


@app.get("/", tags=["Info"])
def home():
    """Home endpoint with links to all automatically discovered examples."""
    return {
        "message": "Runpod Flash Examples - Unified Demo",
        "description": "All Flash examples automatically discovered and unified",
        "docs": "/docs",
        "examples": examples_metadata,
        "navigation": {
            "interactive_docs": "/docs",
            "health": "/health",
        },
        "discovery": {
            "total_examples": len(examples_metadata),
            "note": "Examples are automatically discovered from the codebase",
        },
    }


@app.get("/health", tags=["Info"])
def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "examples_loaded": {name: True for name in examples_metadata},
        "total_examples": len(examples_metadata),
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8888))
    logger.info(f"Starting unified Flash examples server on port {port}")
    logger.info(f"Discovered {len(examples_metadata)} examples")

    uvicorn.run(app, host="0.0.0.0", port=port)
