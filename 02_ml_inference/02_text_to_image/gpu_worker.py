"""Flux Text-to-Image — GPU Worker

One function. One decorator. Images from the cloud.
"""

import os

from fastapi import APIRouter
from pydantic import BaseModel, Field
from runpod_flash import GpuGroup, LiveServerless, remote

# ── GPU Configuration ────────────────────────────────────────────────
# FLUX.1-schnell is a fast distilled model (~12GB VRAM).
# ADA_24 gives us an RTX 4090-class GPU with 24GB — plenty of room.
gpu_config = LiveServerless(
    name="02_02_flux_schnell",
    gpus=[GpuGroup.AMPERE_80],
    workersMin=1,
    workersMax=3,
    idleTimeout=5,
)


# ── The entire inference pipeline in one function ────────────────────
@remote(
    resource_config=gpu_config,
    dependencies=[
        "diffusers",
        "torch",
        "transformers",
        "accelerate",
        "sentencepiece",
        "protobuf",
    ],
)
async def generate_image(input_data: dict) -> dict:
    """Generate an image with FLUX.1-schnell on a remote GPU."""
    import base64
    import io

    import torch
    from diffusers import FluxPipeline
    from huggingface_hub import login

    hf_token = input_data.get("hf_token", "")
    if hf_token:
        login(token=hf_token)

    prompt = input_data.get("prompt", "a lightning flash above a datacenter")
    width = input_data.get("width", 512)
    height = input_data.get("height", 512)
    num_steps = input_data.get("num_steps", 4)

    pipe = FluxPipeline.from_pretrained(
        "black-forest-labs/FLUX.1-schnell",
        torch_dtype=torch.bfloat16,
    )
    pipe.enable_model_cpu_offload()

    image = pipe(
        prompt,
        num_inference_steps=num_steps,
        width=width,
        height=height,
        guidance_scale=0.0,
    ).images[0]

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)

    return {
        "status": "success",
        "image_base64": base64.b64encode(buf.read()).decode(),
        "prompt": prompt,
        "width": width,
        "height": height,
    }


# ── FastAPI Router ───────────────────────────────────────────────────
gpu_router = APIRouter()


class ImageRequest(BaseModel):
    prompt: str = Field(
        default="a tiny astronaut floating in space, watercolor style",
        description="Text prompt describing the image to generate",
    )
    width: int = Field(default=512, description="Image width in pixels")
    height: int = Field(default=512, description="Image height in pixels")
    num_steps: int = Field(default=4, description="Number of diffusion steps (1-8)")
    hf_token: str = Field(
        default="",
        description="Optional Hugging Face token. Uses HF_TOKEN env var when omitted.",
    )


@gpu_router.post("/generate")
async def generate(request: ImageRequest):
    """Generate an image from a text prompt using FLUX.1-schnell."""
    hf_token = request.hf_token.strip() or os.environ.get("HF_TOKEN", "")
    return await generate_image(
        {
            "prompt": request.prompt,
            "width": request.width,
            "height": request.height,
            "num_steps": request.num_steps,
            "hf_token": hf_token,
        }
    )
