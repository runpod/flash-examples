import logging
import os

from fastapi import FastAPI

from workers.gpu import gpu_router


logger = logging.getLogger(__name__)


app = FastAPI(
    title="Qwen3-TTS API",
    description="Text-to-Speech API using Qwen3-TTS on RunPod serverless GPUs",
    version="1.0.0",
)

app.include_router(gpu_router, prefix="/gpu", tags=["TTS"])


@app.get("/")
def home():
    return {
        "message": "Qwen3-TTS API",
        "docs": "/docs",
        "endpoints": {
            "tts": "/gpu/tts",
            "tts_audio": "/gpu/tts/audio",
            "voices": "/gpu/voices",
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
