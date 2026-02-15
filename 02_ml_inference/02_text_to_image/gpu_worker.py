"""Flux Text-to-Image — GPU Worker

One warm worker. Cached FLUX pipeline.
"""

import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from runpod_flash import GpuGroup, LiveServerless, remote

# ── GPU Configuration ────────────────────────────────────────────────
# FLUX.1-schnell is a fast distilled model (~12GB VRAM).
# ADA_24 gives us an RTX 4090-class GPU with 24GB — plenty of room.
gpu_config = LiveServerless(
    name="02_02_flux_schnell",
    gpus=[GpuGroup.ADA_24],
    workersMin=1,
    workersMax=3,
    idleTimeout=5,
)


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
class FluxWorker:
    """Warm FLUX worker that caches the pipeline between requests."""

    def __init__(self):
        import torch

        self._torch = torch
        self._model_name = "black-forest-labs/FLUX.1-schnell"
        self._pipe = None

    def _ensure_pipeline(self, hf_token: str):
        from diffusers import FluxPipeline
        from huggingface_hub import login

        if self._pipe is not None:
            return

        if hf_token:
            login(token=hf_token)

        self._pipe = FluxPipeline.from_pretrained(
            self._model_name,
            torch_dtype=self._torch.bfloat16,
        )
        self._pipe.enable_model_cpu_offload()

    async def generate(self, input_data: dict) -> dict:
        import base64
        import io

        hf_token = input_data.get("hf_token", "")
        prompt = input_data.get("prompt", "a lightning flash above a datacenter")
        width = int(input_data.get("width", 512))
        height = int(input_data.get("height", 512))
        num_steps = int(input_data.get("num_steps", 4))

        try:
            self._ensure_pipeline(hf_token=hf_token)
            image = self._pipe(
                prompt,
                num_inference_steps=num_steps,
                width=width,
                height=height,
                guidance_scale=0.0,
            ).images[0]
        except Exception as exc:
            return {"status": "error", "error": f"Image generation failed: {exc}"}

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
worker: FluxWorker | None = None


def get_worker() -> FluxWorker:
    global worker
    if worker is None:
        worker = FluxWorker()
    return worker


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
    result = await get_worker().generate(
        {
            "prompt": request.prompt,
            "width": request.width,
            "height": request.height,
            "num_steps": request.num_steps,
            "hf_token": hf_token,
        }
    )
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("error", "Image generation failed"))
    return result
