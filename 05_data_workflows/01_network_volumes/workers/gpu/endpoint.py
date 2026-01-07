## GPU worker with network volumes
# In this example, we'll use a GPU worker with a stable diffusion pipieline to generate images.
from tetra_rp import GpuGroup, LiveServerless, remote
import logging

from .. import volume

logger = logging.getLogger(__name__)

MODEL_PATH = "/runpod-volume/models"

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
        import os

        import torch
        from diffusers import StableDiffusionPipeline

        model_path = os.getenv("MODEL_PATH")

        logger.info("Initializing compact Stable Diffusion model...")

        self.pipe = StableDiffusionPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            torch_dtype=torch.float16,
            safety_checker=None,  # Disable to save memory
            use_safetensors=True,
            requires_safety_checker=False,
            low_cpu_mem_usage=True,  # Additional memory optimization
        )

        # Move to GPU and optimize
        self.pipe = self.pipe.to("cuda")
        self.pipe.enable_attention_slicing()  # Additional memory saving

        # Clean up any leftover memory
        gc.collect()
        torch.cuda.empty_cache()

        logger.info("Compact Stable Diffusion initialized successfully!")
        logger.info(f"Model weights stored in {model_path}: {os.listdir(model_path)}")

    def generate_image(self, prompt: str):
        """Generate a single image from prompt"""
        logger.info(f"Generating image for: '{prompt}'")

        image = self.pipe(
            prompt=prompt,
            num_inference_steps=20,
            guidance_scale=7.5,
            width=512,
            height=512,
        ).images[0]

        # Create output directory if it doesn't exist
        import datetime
        import os

        output_dir = "/runpod-volume/generated_images"
        os.makedirs(output_dir, exist_ok=True)

        # Save image locally with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        image_filename = f"sd_generated_{timestamp}.png"
        image_path = os.path.join(output_dir, image_filename)
        image.save(image_path)
        logger.info(f"Image saved to: {image_path}")

        # Create response data
        response_data = {
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
        return response_data


# Test locally with: python -m workers.gpu.endpoint
if __name__ == "__main__":
    import asyncio

    test_payload = {"message": "Testing GPU worker"}
    logger.info(f"Testing GPU worker with payload: {test_payload}")
    sd = SimpleSD()
    asyncio.run(sd.generate_image("make an image of a cute labrador retriever surfing a wave"))
