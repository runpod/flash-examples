# GPU worker with network volume for Stable Diffusion image generation.
# Run with: flash run
# Test directly: python gpu_worker.py
import logging

from runpod_flash import GpuGroup, LiveServerless, NetworkVolume, remote

logger = logging.getLogger(__name__)

MODEL_PATH = "/runpod-volume/models"

volume = NetworkVolume(
    name="flash-05-volume",
    size=50,
)

gpu_config = LiveServerless(
    name="gpu_worker",
    gpus=[GpuGroup.ANY],
    workersMin=0,
    workersMax=3,
    idleTimeout=5,
    networkVolume=volume,
    env={"HF_HUB_CACHE": MODEL_PATH, "MODEL_PATH": MODEL_PATH},
)


@remote(resource_config=gpu_config, dependencies=["diffusers", "torch", "transformers"])
class SimpleSD:
    def __init__(self):
        import gc
        import logging
        import os

        import torch
        from diffusers import StableDiffusionPipeline

        self.logger = logging.getLogger(__name__)
        model_path = os.getenv("MODEL_PATH")

        self.logger.info("Initializing compact Stable Diffusion model...")

        self.pipe = StableDiffusionPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            torch_dtype=torch.float16,
            safety_checker=None,
            use_safetensors=True,
            requires_safety_checker=False,
            low_cpu_mem_usage=True,
        )

        self.pipe = self.pipe.to("cuda")
        self.pipe.enable_attention_slicing()

        gc.collect()
        torch.cuda.empty_cache()

        self.logger.info("Compact Stable Diffusion initialized successfully!")
        self.logger.info(f"Model weights stored in {model_path}: {os.listdir(model_path)}")

    async def generate_image(self, prompt: str) -> dict:
        """Generate a single image from prompt."""
        self.logger.info(f"Generating image for: '{prompt}'")

        image = self.pipe(
            prompt=prompt,
            num_inference_steps=20,
            guidance_scale=7.5,
            width=512,
            height=512,
        ).images[0]

        import datetime
        import os

        output_dir = "/runpod-volume/generated_images"
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        image_filename = f"sd_generated_{timestamp}.png"
        image_path = os.path.join(output_dir, image_filename)
        image.save(image_path)
        self.logger.info(f"Image saved to: {image_path}")

        return {
            "prompt": prompt,
            "image_path": image_path,
            "timestamp": timestamp,
            "generation_params": {
                "num_inference_steps": 20,
                "guidance_scale": 7.5,
                "width": 512,
                "height": 512,
            },
            "message": "Image generated and saved locally!",
        }


if __name__ == "__main__":
    import asyncio

    test_payload = {"message": "Testing GPU worker"}
    logger.info(f"Testing GPU worker with payload: {test_payload}")
    sd = SimpleSD()
    asyncio.run(sd.generate_image("make an image of a cute labrador retriever surfing a wave"))
