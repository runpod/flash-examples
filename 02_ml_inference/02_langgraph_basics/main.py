"""LangGraph + Flash Integration Example - Local Development Server.

This FastAPI application provides a local development server for testing
the LangGraph + Flash integration example. Routes requests to GPU workers
that execute on Runpod infrastructure.

Run with: python -m main
or:       flash run
"""

import logging
import os

from fastapi import FastAPI
from gpu_worker import gpu_router

logger = logging.getLogger(__name__)


# Create FastAPI application
app = FastAPI(
    title="LangGraph + Flash Integration Example",
    description="Demonstrates agentic workflows with LangGraph orchestration and Flash distributed execution",
    version="0.1.0",
)

# Attach GPU worker router
app.include_router(
    gpu_router,
    prefix="/gpu",
    tags=["GPU Workers"],
)


@app.get("/")
def home() -> dict:
    """Home endpoint describing available services."""
    return {
        "message": "LangGraph + Flash Integration Example",
        "docs": "/docs",
        "endpoints": {
            "analyze_dataset": "/gpu/analyze-dataset",
            "health": "/gpu/health",
        },
        "examples": {
            "analyze": {
                "method": "POST",
                "url": "/gpu/analyze-dataset",
                "payload": {
                    "values": [1.2, 3.4, 2.1, 5.6, 4.3, 2.8, 1.9, 3.2, 4.1, 2.5],
                    "dataset_type": "numerical",
                },
            }
        },
    }


@app.get("/ping")
def ping() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("FLASH_HOST", "localhost")
    port = int(os.getenv("FLASH_PORT", 8888))

    logger.info(f"Starting LangGraph + Flash server on {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
    )
