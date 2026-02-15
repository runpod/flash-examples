import base64
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from runpod_flash import GpuGroup, LiveServerless, remote

DEFAULT_IMAGE_PATH = Path(__file__).resolve().parent / "poddy.jpg"


def load_default_image_base64() -> str:
    return base64.b64encode(DEFAULT_IMAGE_PATH.read_bytes()).decode("utf-8")


gpu_config = LiveServerless(
    name="02_03_image_to_image_gpu",
    gpus=[GpuGroup.ADA_24],
    workersMin=0,
    workersMax=2,
    idleTimeout=5,
)


@remote(
    resource_config=gpu_config,
    dependencies=[
        "diffusers",
        "torch",
        "transformers",
        "accelerate",
        "safetensors",
        "pillow",
    ],
)
class ImageToImageWorker:
    def __init__(self):
        import torch
        from diffusers import StableDiffusionImg2ImgPipeline

        self._torch = torch
        self.pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            torch_dtype=torch.float16,
            safety_checker=None,
            requires_safety_checker=False,
        )
        self.pipe = self.pipe.to("cuda")
        self.pipe.enable_attention_slicing()

    async def transform(self, input_data: dict) -> dict:
        import base64
        import io
        from datetime import datetime

        from PIL import Image

        image_base64 = input_data.get("image_base64", "")
        prompt = input_data.get("prompt", "").strip()
        negative_prompt = input_data.get("negative_prompt", "").strip()
        strength = float(input_data.get("strength", 0.65))
        guidance_scale = float(input_data.get("guidance_scale", 7.5))
        num_steps = int(input_data.get("num_steps", 25))
        seed = input_data.get("seed")

        if not image_base64:
            return {"status": "error", "error": "image_base64 is required"}
        if not prompt:
            return {"status": "error", "error": "prompt is required"}

        try:
            image_bytes = base64.b64decode(image_base64)
            input_image = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize((512, 512))
        except Exception as exc:
            return {"status": "error", "error": f"Invalid input image: {exc}"}

        generator = None
        if seed is not None:
            generator = self._torch.Generator(device="cuda").manual_seed(int(seed))

        output_image = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt if negative_prompt else None,
            image=input_image,
            strength=strength,
            guidance_scale=guidance_scale,
            num_inference_steps=num_steps,
            generator=generator,
        ).images[0]

        output_buffer = io.BytesIO()
        output_image.save(output_buffer, format="PNG")
        output_buffer.seek(0)

        return {
            "status": "success",
            "image_base64": base64.b64encode(output_buffer.read()).decode("utf-8"),
            "model": "runwayml/stable-diffusion-v1-5",
            "prompt": prompt,
            "negative_prompt": negative_prompt or None,
            "strength": strength,
            "guidance_scale": guidance_scale,
            "num_steps": num_steps,
            "seed": seed,
            "timestamp": datetime.now().isoformat(),
        }


gpu_router = APIRouter()
worker: ImageToImageWorker | None = None


def get_worker() -> ImageToImageWorker:
    global worker
    if worker is None:
        worker = ImageToImageWorker()
    return worker


class ImageToImageRequest(BaseModel):
    image_base64: str = Field(
        default="",
        description="Input image encoded as base64. If omitted, defaults to poddy.jpg.",
    )
    prompt: str = Field(description="Prompt that describes how to transform the image")
    negative_prompt: str = Field(default="", description="What to avoid in the output image")
    strength: float = Field(default=0.65, ge=0.1, le=1.0)
    guidance_scale: float = Field(default=7.5, ge=0.0, le=20.0)
    num_steps: int = Field(default=25, ge=1, le=50)
    seed: int | None = Field(default=None, ge=0)


@gpu_router.post("/transform")
async def transform(request: ImageToImageRequest):
    payload = request.model_dump()
    if not payload.get("image_base64"):
        try:
            payload["image_base64"] = load_default_image_base64()
        except FileNotFoundError as exc:
            raise HTTPException(status_code=500, detail=f"Default image not found: {exc}") from exc
    result = await get_worker().transform(payload)
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("error", "Image transformation failed"))
    return result
