from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from runpod_flash import GpuGroup, LiveServerless, remote

gpu_config = LiveServerless(
    name="02_04_text_to_video_gpu",
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
class TextToVideoWorker:
    def __init__(self):
        import torch
        from diffusers import DiffusionPipeline

        self._torch = torch
        self.model = "damo-vilab/text-to-video-ms-1.7b"
        self._using_cpu_offload = False
        self.pipe = DiffusionPipeline.from_pretrained(
            self.model,
            torch_dtype=torch.float16,
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
                # Prefer CPU offload for better reliability on 24GB GPUs.
                self.pipe.enable_model_cpu_offload()
                self._using_cpu_offload = True
            except Exception:
                # Fallback to full-GPU placement if offload is unavailable.
                self.pipe = self.pipe.to("cuda")
        else:
            self.pipe = self.pipe.to("cpu")

    async def generate(self, input_data: dict) -> dict:
        import base64
        import io
        from datetime import datetime

        prompt = input_data.get("prompt", "").strip()
        negative_prompt = input_data.get("negative_prompt", "").strip()
        num_frames = int(input_data.get("num_frames", 12))
        num_steps = int(input_data.get("num_steps", 18))
        guidance_scale = float(input_data.get("guidance_scale", 7.0))
        fps = int(input_data.get("fps", 8))
        width = int(input_data.get("width", 512))
        height = int(input_data.get("height", 288))
        seed = input_data.get("seed")

        if not prompt:
            return {"status": "error", "error": "prompt is required"}
        if width % 8 != 0 or height % 8 != 0:
            return {"status": "error", "error": "width and height must be divisible by 8"}

        generator = None
        if seed is not None:
            generator_device = "cpu" if self._using_cpu_offload else "cuda"
            if not self._torch.cuda.is_available():
                generator_device = "cpu"
            generator = self._torch.Generator(device=generator_device).manual_seed(int(seed))

        try:
            with self._torch.inference_mode():
                result = self.pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt if negative_prompt else None,
                    num_frames=num_frames,
                    num_inference_steps=num_steps,
                    guidance_scale=guidance_scale,
                    width=width,
                    height=height,
                    generator=generator,
                    output_type="pil",
                )
            frames = result.frames[0]
        except Exception as exc:
            return {"status": "error", "error": f"Video generation failed: {exc}"}
        finally:
            if self._torch.cuda.is_available():
                self._torch.cuda.empty_cache()

        if frames is None:
            return {"status": "error", "error": "Model returned no frames"}
        frames = list(frames)
        if len(frames) == 0:
            return {"status": "error", "error": "Model returned no frames"}
        if not hasattr(frames[0], "save"):
            from PIL import Image

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
            "prompt": prompt,
            "negative_prompt": negative_prompt or None,
            "num_frames": len(frames),
            "fps": effective_fps,
            "num_steps": num_steps,
            "guidance_scale": guidance_scale,
            "width": width,
            "height": height,
            "seed": seed,
            "timestamp": datetime.now().isoformat(),
        }


gpu_router = APIRouter()
worker: TextToVideoWorker | None = None


def get_worker() -> TextToVideoWorker:
    global worker
    if worker is None:
        worker = TextToVideoWorker()
    return worker


class TextToVideoRequest(BaseModel):
    prompt: str = Field(description="Prompt that describes the video to generate")
    negative_prompt: str = Field(default="", description="What to avoid in the generated video")
    num_frames: int = Field(default=12, ge=8, le=24)
    num_steps: int = Field(default=18, ge=5, le=40)
    guidance_scale: float = Field(default=7.0, ge=1.0, le=20.0)
    fps: int = Field(default=8, ge=1, le=30)
    width: int = Field(default=512, ge=256, le=768)
    height: int = Field(default=288, ge=256, le=512)
    seed: int | None = Field(default=None, ge=0)


@gpu_router.post("/generate")
async def generate(request: TextToVideoRequest):
    result = await get_worker().generate(request.model_dump())
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("error", "Video generation failed"))
    return result
