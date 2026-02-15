import base64
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from runpod_flash import GpuGroup, LiveServerless, remote

DEFAULT_IMAGE_PATH = Path(__file__).resolve().parent / "poddy.jpg"


def load_default_image_base64() -> str:
    return base64.b64encode(DEFAULT_IMAGE_PATH.read_bytes()).decode("utf-8")


gpu_config = LiveServerless(
    name="02_05_image_to_video_gpu",
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
class ImageToVideoWorker:
    def __init__(self):
        import torch
        from diffusers import StableVideoDiffusionPipeline

        self._torch = torch
        self.model = "stabilityai/stable-video-diffusion-img2vid-xt"
        self._using_cpu_offload = False
        self.pipe = StableVideoDiffusionPipeline.from_pretrained(
            self.model,
            torch_dtype=torch.float16,
            variant="fp16",
        )
        self.pipe.enable_attention_slicing()
        if hasattr(self.pipe, "vae"):
            if hasattr(self.pipe.vae, "enable_slicing"):
                try:
                    self.pipe.vae.enable_slicing()
                except NotImplementedError:
                    pass
                except Exception:
                    pass
            if hasattr(self.pipe.vae, "enable_tiling"):
                try:
                    self.pipe.vae.enable_tiling()
                except NotImplementedError:
                    pass
                except Exception:
                    pass

        if torch.cuda.is_available():
            try:
                self.pipe.enable_model_cpu_offload()
                self._using_cpu_offload = True
            except Exception:
                self.pipe = self.pipe.to("cuda")
        else:
            self.pipe = self.pipe.to("cpu")

    async def animate(self, input_data: dict) -> dict:
        import base64
        import io
        from datetime import datetime

        from PIL import Image

        image_base64 = input_data.get("image_base64", "")
        motion_bucket_id = int(input_data.get("motion_bucket_id", 127))
        noise_aug_strength = float(input_data.get("noise_aug_strength", 0.02))
        num_frames = int(input_data.get("num_frames", 12))
        num_steps = int(input_data.get("num_steps", 18))
        fps = int(input_data.get("fps", 7))
        seed = input_data.get("seed")

        if not image_base64:
            return {"status": "error", "error": "image_base64 is required"}

        try:
            image_bytes = base64.b64decode(image_base64)
            input_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as exc:
            return {"status": "error", "error": f"Invalid input image: {exc}"}

        resized_image = input_image.resize((1024, 576))

        generator = None
        if seed is not None:
            generator_device = "cpu" if self._using_cpu_offload else "cuda"
            if not self._torch.cuda.is_available():
                generator_device = "cpu"
            generator = self._torch.Generator(device=generator_device).manual_seed(int(seed))

        try:
            with self._torch.inference_mode():
                result = self.pipe(
                    image=resized_image,
                    decode_chunk_size=4,
                    motion_bucket_id=motion_bucket_id,
                    noise_aug_strength=noise_aug_strength,
                    num_frames=num_frames,
                    num_inference_steps=num_steps,
                    generator=generator,
                    output_type="pil",
                )
            frames = result.frames[0]
        except Exception as exc:
            return {"status": "error", "error": f"Animation failed: {exc}"}
        finally:
            if self._torch.cuda.is_available():
                self._torch.cuda.empty_cache()

        if frames is None:
            return {"status": "error", "error": "Model returned no frames"}
        frames = list(frames)
        if len(frames) == 0:
            return {"status": "error", "error": "Model returned no frames"}
        if not hasattr(frames[0], "save"):
            converted_frames = []
            for frame in frames:
                arr = frame
                if hasattr(arr, "dtype") and str(arr.dtype) != "uint8":
                    arr = (arr * 255).clip(0, 255).astype("uint8")
                converted_frames.append(Image.fromarray(arr))
            frames = converted_frames

        # GIF timing is quantized in milliseconds; clamp to 25 FPS max and report actual output FPS.
        effective_fps = min(max(fps, 1), 25)
        duration_ms = int(1000 / effective_fps)

        gif_buffer = io.BytesIO()
        frames[0].save(
            gif_buffer,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=duration_ms,
            loop=0,
        )
        gif_buffer.seek(0)

        preview_buffer = io.BytesIO()
        frames[0].save(preview_buffer, format="PNG")
        preview_buffer.seek(0)

        return {
            "status": "success",
            "video_base64": base64.b64encode(gif_buffer.read()).decode("utf-8"),
            "video_mime_type": "image/gif",
            "preview_image_base64": base64.b64encode(preview_buffer.read()).decode("utf-8"),
            "preview_image_mime_type": "image/png",
            "model": self.model,
            "input_width": input_image.width,
            "input_height": input_image.height,
            "render_width": 1024,
            "render_height": 576,
            "num_frames": len(frames),
            "num_steps": num_steps,
            "motion_bucket_id": motion_bucket_id,
            "noise_aug_strength": noise_aug_strength,
            "fps": effective_fps,
            "seed": seed,
            "timestamp": datetime.now().isoformat(),
        }


gpu_router = APIRouter()
worker: ImageToVideoWorker | None = None


def get_worker() -> ImageToVideoWorker:
    global worker
    if worker is None:
        worker = ImageToVideoWorker()
    return worker


class ImageToVideoRequest(BaseModel):
    image_base64: str = Field(
        default="",
        description="Input image encoded as base64. If omitted, defaults to poddy.jpg.",
    )
    motion_bucket_id: int = Field(default=127, ge=1, le=255)
    noise_aug_strength: float = Field(default=0.02, ge=0.0, le=1.0)
    num_frames: int = Field(default=12, ge=8, le=24)
    num_steps: int = Field(default=18, ge=5, le=40)
    fps: int = Field(default=7, ge=1, le=30)
    seed: int | None = Field(default=None, ge=0)


@gpu_router.post("/animate")
async def animate(request: ImageToVideoRequest):
    payload = request.model_dump()
    if not payload.get("image_base64"):
        try:
            payload["image_base64"] = load_default_image_base64()
        except FileNotFoundError as exc:
            raise HTTPException(status_code=500, detail=f"Default image not found: {exc}") from exc
    result = await get_worker().animate(payload)
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("error", "Image animation failed"))
    return result
