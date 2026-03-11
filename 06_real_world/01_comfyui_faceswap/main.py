# FastAPI entry point for ComfyUI character generation.
# Run with: flash run
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

from gpu_worker import ComfyUICharacter, setup_hf_token

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Write HF_TOKEN to network volume before any worker init.
    # This ensures gated models (Juggernaut-XI) can be downloaded.
    hf_token = os.environ.get("HF_TOKEN", "")
    if hf_token:
        logger.info("Writing HF_TOKEN to network volume...")
        result = await setup_hf_token({"token": hf_token})
        logger.info(f"HF_TOKEN setup: {result}")
    else:
        logger.warning("HF_TOKEN not set — gated model downloads will fail")
    yield


app = FastAPI(
    title="ComfyUI Character Generation",
    description="SDXL character generation with optional face swapping via ComfyUI",
    version="0.1.0",
    lifespan=lifespan,
)

# Class-based @remote: instantiation triggers remote __init__ (model loading).
# The instance persists across requests, keeping models in GPU memory.
worker = ComfyUICharacter()


class GenerateRequest(BaseModel):
    prompt: str
    negative_prompt: str = ""
    image_url: Optional[str] = None
    face_description: str = ""
    width: int = 832
    height: int = 1216
    steps: int = 35
    cfg: float = 2.0
    seed: Optional[int] = None


@app.post("/generate")
async def generate(request: GenerateRequest):
    """Generate a character image, optionally with face swapping."""
    result = await worker.generate(request.model_dump(exclude_none=True))
    return result


@app.get("/")
def home():
    return {
        "message": "ComfyUI Character Generation",
        "docs": "/docs",
        "endpoints": {"generate": "POST /generate"},
    }


@app.get("/ping")
def ping():
    return {"status": "healthy"}
