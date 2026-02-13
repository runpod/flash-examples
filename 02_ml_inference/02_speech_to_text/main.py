import logging
import os

from fastapi import FastAPI

from workers.gpu import gpu_router

logger = logging.getLogger(__name__)


app = FastAPI(
    title="Parakeet-TDT Speech-to-Text API",
    description="Speech-to-Text API using NVIDIA Parakeet-TDT-0.6B-v2 on RunPod serverless GPUs",
    version="1.0.0",
)

app.include_router(gpu_router, prefix="/gpu", tags=["Speech-to-Text"])


@app.get("/")
def home():
    return {
        "message": "Parakeet-TDT Speech-to-Text API",
        "docs": "/docs",
        "endpoints": {
            "transcribe": "/gpu/transcribe",
            "model_info": "/gpu/model-info",
        },
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
