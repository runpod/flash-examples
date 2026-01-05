import logging
import os

from fastapi import FastAPI
from workers.cpu import cpu_router
from workers.gpu import gpu_router

logger = logging.getLogger(__name__)


app = FastAPI(
    title="Load Balancer Example",
    description="Demonstrates load-balancer endpoints with custom HTTP routes using Flash",
    version="0.1.0",
)

# Include routers for unified app discovery
app.include_router(gpu_router, prefix="/gpu", tags=["GPU Compute Service"])
app.include_router(cpu_router, prefix="/cpu", tags=["CPU Data Service"])


@app.get("/")
def home():
    return {
        "message": "Load Balancer Example API",
        "description": "Demonstrates load-balancer endpoints with custom HTTP routes",
        "note": "Load-balancer endpoints are defined with @remote(resource, method=..., path=...)",
        "docs": "/docs",
        "gpu_endpoints": {
            "health": "GET /gpu/health",
            "compute": "POST /gpu/compute",
            "info": "GET /gpu/info",
        },
        "cpu_endpoints": {
            "health": "GET /cpu/health",
            "validate": "POST /cpu/validate",
            "transform": "POST /cpu/transform",
        },
    }


@app.get("/ping")
def ping():
    """Health check endpoint for load balancer."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("FLASH_HOST", "localhost")
    port = int(os.getenv("FLASH_PORT", 8000))
    logger.info(f"Starting Load Balancer Example on {host}:{port}")

    uvicorn.run(app, host=host, port=port)
