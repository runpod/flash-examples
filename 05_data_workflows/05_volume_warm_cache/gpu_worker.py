# GPU worker that warm-caches its model on a network volume with VolumeCache.
#
# Contrast with 01_network_volumes, which points HF_HUB_CACHE straight at the
# volume so every read hits the network mount. Here the Hugging Face cache stays
# on fast local disk and VolumeCache mirrors it to the volume: inference reads
# are local, while cold starts stay warm because the model is restored from the
# volume instead of re-downloaded.
#
# STATUS: VolumeCache ships in runpod-python (SLS-367 / PR #531). This example
# runs once that change is released and the flash-worker image includes it; see
# README.md. Until then it is illustrative.
#
# run with: flash dev
import logging

from runpod_flash import Endpoint, GpuType, NetworkVolume

logger = logging.getLogger(__name__)

volume = NetworkVolume(
    name="flash-05-02-volume",
    size=50,
)


@Endpoint(
    name="02_volume_warm_cache",
    gpu=GpuType.NVIDIA_GEFORCE_RTX_5090,
    workers=(0, 3),
    idle_timeout=300,
    volume=volume,
    dependencies=["torch", "diffusers", "transformers", "accelerate"],
)
class WarmCachedSD:
    def __init__(self):
        # Imports live inside the handler: @Endpoint ships only the function
        # body to the worker, so module-level imports/constants aren't available
        # remotely. VolumeCache comes from the worker's runpod-python.
        import logging
        import os

        import torch
        from diffusers import StableDiffusionPipeline
        from runpod.serverless import VolumeCache

        self.logger = logging.getLogger(__name__)

        # HF cache stays on local disk (default ~/.cache/huggingface). We do NOT
        # point HF_HUB_CACHE at the volume. Instead VolumeCache hydrates that
        # local dir from the volume before the load and syncs new files back
        # after: the first cold worker downloads once; every later cold worker
        # restores from the volume and skips the download.
        hf_cache = os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface"))

        self.logger.info("Loading Stable Diffusion (warm cache via VolumeCache)...")
        with VolumeCache(dirs=[hf_cache]):
            self.pipe = StableDiffusionPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                torch_dtype=torch.float16,
                safety_checker=None,
                use_safetensors=True,
                requires_safety_checker=False,
                low_cpu_mem_usage=True,
            ).to("cuda")

        self.pipe.enable_attention_slicing()
        self.logger.info("Stable Diffusion ready.")

    async def generate_image(self, prompt: str) -> dict:
        """Generate a single image from a prompt."""
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
        image_path = os.path.join(output_dir, f"sd_generated_{timestamp}.png")
        image.save(image_path)
        self.logger.info(f"Image saved to: {image_path}")

        return {
            "prompt": prompt,
            "image_path": image_path,
            "timestamp": timestamp,
        }


if __name__ == "__main__":
    import asyncio

    sd = WarmCachedSD()
    asyncio.run(sd.generate_image("a cute labrador retriever surfing a wave"))
