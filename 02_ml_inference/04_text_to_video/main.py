import logging
import os

from fastapi import FastAPI
from gpu_worker import gpu_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Text-to-Video API",
    description="Generate short videos from text prompts on RunPod serverless GPUs",
    version="1.0.0",
)

app.include_router(gpu_router, prefix="/gpu", tags=["Text-to-Video"])


@app.get("/")
def home():
    return {
        "message": "Text-to-Video API",
        "docs": "/docs",
        "endpoints": {"generate": "/gpu/generate"},
    }


@app.get("/ping")
def ping():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("FLASH_HOST", "localhost")
    port = int(os.getenv("FLASH_PORT", 8888))
    logger.info(f"Starting Flash server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
