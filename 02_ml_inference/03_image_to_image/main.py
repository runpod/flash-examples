import logging
import os

from fastapi import FastAPI
from gpu_worker import gpu_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Image-to-Image API",
    description="Transform images with Stable Diffusion on RunPod serverless GPUs",
    version="1.0.0",
)

app.include_router(gpu_router, prefix="/gpu", tags=["Image-to-Image"])


@app.get("/")
def home():
    return {
        "message": "Image-to-Image API",
        "docs": "/docs",
        "endpoints": {"transform": "/gpu/transform"},
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
