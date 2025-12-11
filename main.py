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
from urllib.parse import quote

from fastapi import APIRouter, FastAPI
from fastapi.responses import HTMLResponse

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

# Route discovery constants
SKIP_HEALTH_CHECK_PATHS = ("/", "/health")
SKIP_OPENAPI_PATHS = ("/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc")
SKIP_WORKER_TYPES = ("gpu", "cpu", "workers")

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


def discover_single_file_routers(
    example_path: Path, example_name: str, example_tag: str = ""
) -> list[dict[str, Any]]:
    """
    Discover routers from single-file worker patterns.

    Looks for files like gpu_worker.py, cpu_worker.py that export APIRouters.
    """
    routers: list[dict[str, Any]] = []
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
                    # Extract route information for deep linking
                    routes = []
                    for route in router.routes:
                        if (
                            hasattr(route, "endpoint")
                            and hasattr(route, "path")
                            and hasattr(route, "name")
                        ):
                            routes.append(
                                {
                                    "path": str(route.path),
                                    "name": str(route.name),
                                }
                            )

                    routers.append(
                        {
                            "router": router,
                            "prefix": f"/{example_name}/{worker_type}",
                            "tags": [example_tag],
                            "worker_type": worker_type,
                            "routes": routes,
                        }
                    )
                    logger.info(f"Loaded {example_name}/{worker_type} from {worker_file.name}")
        except Exception as e:
            logger.warning(f"Could not load {worker_file}: {e}")

    return routers


def discover_directory_routers(
    example_path: Path, example_name: str, example_tag: str = ""
) -> list[dict[str, Any]]:
    """
    Discover routers from directory-based worker patterns.

    Looks for workers/gpu/__init__.py, workers/cpu/__init__.py that export APIRouters.
    """
    routers: list[dict[str, Any]] = []
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
                    # Extract route information for deep linking
                    routes = []
                    for route in router.routes:
                        if (
                            hasattr(route, "endpoint")
                            and hasattr(route, "path")
                            and hasattr(route, "name")
                        ):
                            routes.append(
                                {
                                    "path": str(route.path),
                                    "name": str(route.name),
                                }
                            )

                    routers.append(
                        {
                            "router": router,
                            "prefix": f"/{example_name}/{worker_type}",
                            "tags": [example_tag],
                            "worker_type": worker_type,
                            "routes": routes,
                        }
                    )
                    logger.info(f"Loaded {example_name}/{worker_type} from workers/{worker_type}")
        except Exception as e:
            logger.warning(f"Could not load {worker_dir}: {e}")

    return routers


def discover_main_app_routes(
    example_path: Path, example_name: str, example_tag: str = ""
) -> list[dict[str, Any]]:
    """
    Discover context routes from main.py FastAPI app.

    Extracts only direct routes from the app's router (not included routers).
    Skips health check, info endpoints, and auto-generated OpenAPI routes.
    Returns routes as a single router grouped with the example (no separate prefix).
    """
    routers: list[dict[str, Any]] = []
    main_file = example_path / "main.py"

    if not main_file.exists():
        return routers

    module_name = f"{example_name}_main_context"

    try:
        module = load_module_from_path(module_name, main_file)
        if module is None:
            return routers

        # Look for FastAPI app instance
        if not hasattr(module, "app"):
            return routers

        main_app = module.app
        if not hasattr(main_app, "routes"):
            return routers

        from fastapi.routing import Mount

        # We want to extract routes that were directly added to the app (via @app.post, etc.)
        # not routes from included routers. We'll check the app's router directly.
        routes_list = []
        context_router = APIRouter()

        # Look at direct routes from the main app's router
        if hasattr(main_app, "router") and hasattr(main_app.router, "routes"):
            for route in main_app.router.routes:
                # Skip Mount routes (these are included routers like /gpu, /cpu)
                if isinstance(route, Mount):
                    continue

                # Skip health check and info endpoints
                if hasattr(route, "path") and route.path in SKIP_HEALTH_CHECK_PATHS:
                    continue

                # Skip auto-generated OpenAPI documentation routes
                if hasattr(route, "path") and route.path in SKIP_OPENAPI_PATHS:
                    continue

                # Skip routes from included routers (routes with /gpu/, /cpu/, etc.)
                if hasattr(route, "path"):
                    path = str(route.path)
                    # Skip routes that start with common worker types or look like they're from included routers
                    if any(f"/{wt}/" in path for wt in SKIP_WORKER_TYPES):
                        continue

                # Include everything else
                if hasattr(route, "endpoint") and hasattr(route, "path") and hasattr(route, "name"):
                    routes_list.append(
                        {
                            "path": str(route.path),
                            "name": str(route.name),
                        }
                    )
                    context_router.routes.append(route)

        if context_router.routes:
            routers.append(
                {
                    "router": context_router,
                    "prefix": f"/{example_name}",
                    "tags": [example_tag],
                    "worker_type": "api",
                    "routes": routes_list,
                }
            )
            logger.info(
                f"Loaded {example_name} context routes from main.py ({len(routes_list)} routes)"
            )

    except Exception as e:
        logger.debug(f"Could not load context routes from {main_file}: {e}")

    return routers


def discover_example_routers(
    example_path: Path, category_name: str = "", example_name: str = ""
) -> list[dict[str, Any]]:
    """
    Discover all routers from an example directory.

    Tries single-file, directory-based, and main.py app patterns.
    Groups all routes under a single example tag: "Category > Example"
    Includes context routes from main.py (like pipelines) grouped with the example.
    """
    if not example_name:
        example_name = example_path.name

    # Build example tag: "01 Getting Started > 01 Hello World"
    example_tag = (
        f"{category_name} > {example_name.replace('_', ' ').title()}"
        if category_name
        else example_name.replace("_", " ").title()
    )

    routers: list[dict[str, Any]] = []

    # Try single-file pattern
    routers.extend(discover_single_file_routers(example_path, example_name, example_tag))

    # Try directory-based pattern
    routers.extend(discover_directory_routers(example_path, example_name, example_tag))

    # Extract context routes (main.py app routes like pipelines, classifiers)
    # These are grouped with the example, not given special tagging
    routers.extend(discover_main_app_routes(example_path, example_name, example_tag))

    return routers


def register_all_examples() -> dict[str, dict[str, Any]]:
    """
    Discover and register all examples.

    Returns a dictionary of category -> examples metadata for the home endpoint.
    """
    examples_by_category: dict[str, dict[str, Any]] = {}

    for examples_dir in EXAMPLES_DIRS:
        if not examples_dir.exists() or not examples_dir.is_dir():
            continue

        category_name = examples_dir.name  # e.g., "01_getting_started"
        category_display = category_name.replace("_", " ").title()  # "01 Getting Started"

        if category_name not in examples_by_category:
            examples_by_category[category_name] = {
                "display_name": category_display,
                "examples": {},
            }

        # Iterate through example directories
        for example_path in sorted(examples_dir.iterdir()):
            if not example_path.is_dir() or example_path.name.startswith("."):
                continue

            example_name = example_path.name
            routers = discover_example_routers(example_path, category_display, example_name)

            if routers:
                # Register routers with FastAPI
                for router_info in routers:
                    app.include_router(
                        router_info["router"],
                        prefix=router_info["prefix"],
                        tags=router_info["tags"],
                    )

                # Build metadata
                examples_by_category[category_name]["examples"][example_name] = {
                    "description": f"Example: {example_name.replace('_', ' ').title()}",
                    "category_display": category_display,
                    "endpoints": {
                        router_info["worker_type"]: {
                            "prefix": router_info["prefix"],
                            "routes": router_info.get("routes", []),
                            "tag": router_info["tags"][0] if router_info["tags"] else "",
                        }
                        for router_info in routers
                    },
                }

    return examples_by_category


# Discover and register all examples
examples_metadata = register_all_examples()


def extract_operation_ids_from_app() -> dict[str, dict[str, list[str]]]:
    """
    Extract actual operation IDs from the FastAPI app's routes.

    Returns a mapping of example_name -> worker_type -> [operation_ids]
    """
    operation_ids_map: dict[str, dict[str, list[str]]] = {}

    for route in app.routes:
        if hasattr(route, "tags") and hasattr(route, "unique_id"):
            tags = route.tags or []
            operation_id = str(route.unique_id)

            # Parse tag to get example_name and worker_type
            # Tag format: "01 Hello World - GPU"
            for tag in tags:
                if " - " in tag:
                    parts = tag.split(" - ")
                    if len(parts) == 2:
                        display_name = parts[0].strip()
                        worker_type = parts[1].strip().lower()

                        # Convert display name back to example_name
                        # "01 Hello World" -> "01_hello_world"
                        example_name = display_name.lower().replace(" ", "_")

                        if example_name not in operation_ids_map:
                            operation_ids_map[example_name] = {}
                        if worker_type not in operation_ids_map[example_name]:
                            operation_ids_map[example_name][worker_type] = []

                        operation_ids_map[example_name][worker_type].append(operation_id)

    return operation_ids_map


@app.get("/", response_class=HTMLResponse)
def home():
    """Branded home page with links to all automatically discovered examples."""

    # Extract actual operation IDs from the app
    operation_ids_map = extract_operation_ids_from_app()

    # Build examples list HTML grouped by category
    categories_html = ""
    total_examples = 0
    total_endpoints = 0

    for category_data in examples_metadata.values():
        category_display = category_data["display_name"]
        examples = category_data["examples"]

        if not examples:
            continue

        total_examples += len(examples)

        # Build example cards for this category
        examples_cards = ""
        for example_name, metadata in examples.items():
            display_name = example_name.replace("_", " ").title()
            endpoints_html = ""

            total_endpoints += len(metadata["endpoints"])

            for worker_type, endpoint_info in metadata["endpoints"].items():
                # Use the actual tag from the router registration
                tag_name = endpoint_info.get("tag", "")
                if not tag_name:
                    # Fallback to old format if tag is not available
                    tag_name = f"{display_name} - {worker_type.upper()}"

                encoded_tag = quote(tag_name)

                # Get the actual operation ID from the app
                operation_ids = operation_ids_map.get(example_name, {}).get(worker_type.lower(), [])
                if operation_ids:
                    # Use the first operation ID for this worker type
                    operation_id = operation_ids[0]
                    doc_link = f"/docs#/{encoded_tag}/{operation_id}"
                else:
                    # Fallback to tag-only link
                    doc_link = f"/docs#/{encoded_tag}"

                endpoints_html += f'<a href="{doc_link}" target="_blank" rel="noopener noreferrer" class="endpoint-tag">{worker_type.upper()}</a>'

            examples_cards += f"""
            <div class="example-card">
                <h3>{display_name}</h3>
                <div class="endpoints">{endpoints_html}</div>
            </div>
            """

        # Add category section
        categories_html += f"""
        <section class="category-section">
            <h2 class="category-title">{category_display}</h2>
            <div class="examples-grid">
                {examples_cards}
            </div>
        </section>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Runpod Flash Examples</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: #0a0a0a;
                color: #ffffff;
                line-height: 1.6;
                -webkit-font-smoothing: antialiased;
                min-height: 100vh;
            }}

            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
            }}

            header {{
                padding: 3rem 0 2rem;
                text-align: center;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                margin-bottom: 3rem;
            }}

            .logo {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 0.75rem;
                margin-bottom: 1.5rem;
            }}

            .logo img {{
                height: 32px;
                width: auto;
            }}

            h1 {{
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
                background: linear-gradient(135deg, #ffffff 0%, #bbb6fd 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}

            .subtitle {{
                font-size: 1.125rem;
                color: rgba(255, 255, 255, 0.7);
                max-width: 600px;
                margin: 0 auto 2rem;
            }}

            .stats {{
                display: flex;
                gap: 2rem;
                justify-content: center;
                flex-wrap: wrap;
            }}

            .stat {{
                text-align: center;
            }}

            .stat-value {{
                font-size: 2rem;
                font-weight: 700;
                color: #bbb6fd;
            }}

            .stat-label {{
                font-size: 0.875rem;
                color: rgba(255, 255, 255, 0.6);
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }}

            .nav-buttons {{
                display: flex;
                gap: 1rem;
                justify-content: center;
                margin-top: 2rem;
            }}

            .btn {{
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.75rem 1.5rem;
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                color: #ffffff;
                text-decoration: none;
                font-weight: 500;
                transition: all 0.15s ease;
                backdrop-filter: blur(8px);
            }}

            .btn:hover {{
                background: rgba(255, 255, 255, 0.14);
                border-color: #bbb6fd;
                transform: translateY(-1px);
            }}

            .btn-primary {{
                background: rgba(187, 182, 253, 0.15);
                border-color: #bbb6fd;
            }}

            .btn-primary:hover {{
                background: rgba(187, 182, 253, 0.25);
            }}

            .category-section {{
                margin-bottom: 3rem;
            }}

            .category-title {{
                font-size: 1.5rem;
                font-weight: 600;
                color: #bbb6fd;
                margin-bottom: 1.5rem;
                padding-bottom: 0.5rem;
                border-bottom: 2px solid rgba(187, 182, 253, 0.3);
            }}

            .examples-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
                gap: 1.5rem;
            }}

            .example-card {{
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 1.5rem;
                transition: all 0.2s cubic-bezier(0.42, 0, 0.58, 1);
            }}

            .example-card:hover {{
                background: rgba(255, 255, 255, 0.05);
                border-color: rgba(187, 182, 253, 0.5);
                transform: translateY(-2px);
            }}

            .example-card h3 {{
                font-size: 1.25rem;
                margin-bottom: 0.75rem;
                color: #ffffff;
            }}

            .endpoints {{
                display: flex;
                gap: 0.5rem;
                flex-wrap: wrap;
                margin-bottom: 1rem;
            }}

            .endpoint-tag {{
                display: inline-block;
                font-family: 'Roboto Mono', monospace;
                font-size: 0.75rem;
                padding: 0.25rem 0.625rem;
                background: rgba(187, 182, 253, 0.15);
                border: 1px solid rgba(187, 182, 253, 0.3);
                border-radius: 4px;
                color: #bbb6fd;
                font-weight: 500;
                text-decoration: none;
                transition: all 0.15s ease;
            }}

            .endpoint-tag:hover {{
                background: rgba(187, 182, 253, 0.25);
                border-color: #bbb6fd;
                transform: translateY(-1px);
            }}

            footer {{
                margin-top: 4rem;
                padding: 2rem 0;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                text-align: center;
                color: rgba(255, 255, 255, 0.5);
                font-size: 0.875rem;
            }}

            @media (max-width: 768px) {{
                h1 {{
                    font-size: 2rem;
                }}

                .examples-grid {{
                    grid-template-columns: 1fr;
                }}

                .nav-buttons {{
                    flex-direction: column;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div class="logo">
                    <img src="https://cdn.prod.website-files.com/67d20fb9f56ff2ec6a7a657d/683cd0ee11462aef4a016ef6_runpod%20lowercase.webp" alt="Runpod">
                </div>
                <h1>Flash Examples</h1>
                <p class="subtitle">
                    Explore production-ready examples for Runpod Flash. All examples automatically discovered and unified in one FastAPI application.
                </p>

                <div class="stats">
                    <div class="stat">
                        <div class="stat-value">{total_examples}</div>
                        <div class="stat-label">Examples</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{total_endpoints}</div>
                        <div class="stat-label">Endpoints</div>
                    </div>
                </div>

                <div class="nav-buttons">
                    <a href="/docs" class="btn btn-primary">Interactive API Docs</a>
                    <a href="/health" class="btn">Health Check</a>
                </div>
            </header>

            <main>
                {categories_html}
            </main>

            <footer>
                Automatically discovered examples • <a href="https://github.com/runpod/flash-examples" style="color: #bbb6fd; text-decoration: none;">View on GitHub</a>
            </footer>
        </div>
    </body>
    </html>
    """


@app.get("/health", tags=["Info"])
def health():
    """Health check endpoint."""
    examples_loaded = {}
    total_examples = 0

    for category_data in examples_metadata.values():
        for example_name in category_data["examples"]:
            examples_loaded[example_name] = True
            total_examples += 1

    return {
        "status": "healthy",
        "examples_loaded": examples_loaded,
        "total_examples": total_examples,
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("FLASH_HOST", "localhost")
    port = int(os.getenv("FLASH_PORT", 8888))
    logger.info(f"Starting unified Flash examples server on {host}:{port}")
    logger.info(f"Discovered {len(examples_metadata)} examples")

    uvicorn.run(app, host=host, port=port)
