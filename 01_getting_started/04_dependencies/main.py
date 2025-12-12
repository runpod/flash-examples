import logging
import os

from fastapi import FastAPI
from workers.cpu import cpu_router
from workers.gpu import gpu_router

logger = logging.getLogger(__name__)


app = FastAPI(
    title="Dependency Management Examples",
    description="Learn how to manage Python and system dependencies in Flash workers",
    version="0.1.0",
)

app.include_router(gpu_router, prefix="/gpu", tags=["GPU Workers"])
app.include_router(cpu_router, prefix="/cpu", tags=["CPU Workers"])


@app.get("/", tags=["Info"])
def home():
    return {
        "message": "Flash Dependency Management Examples",
        "description": "Examples of Python and system dependency management",
        "docs": "/docs",
        "examples": {
            "ml_deps": "POST /gpu/ml-deps - ML dependencies (torch, pillow, numpy)",
            "system_deps": "POST /gpu/system-deps - System dependencies (ffmpeg, libgl1)",
            "data_deps": "POST /cpu/data - Data science dependencies (pandas, scipy)",
            "minimal": "POST /cpu/minimal - No dependencies (fastest)",
        },
        "concepts": [
            "Version pinning (torch==2.1.0)",
            "Version constraints (>=, <, ~=)",
            "System packages via apt",
            "Minimal dependencies for fast cold start",
        ],
    }


@app.get("/health", tags=["Info"])
def health():
    return {
        "status": "healthy",
        "workers": {
            "ml_deps": "GPU worker with torch, pillow, numpy",
            "system_deps": "GPU worker with ffmpeg, libgl1",
            "data_deps": "CPU worker with pandas, scipy",
            "minimal": "CPU worker with no dependencies",
        },
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("FLASH_HOST", "localhost")
    port = int(os.getenv("FLASH_PORT", 8888))
    logger.info(f"Starting Dependency Management server on {host}:{port}")

    uvicorn.run(app, host=host, port=port)
