# Benchmark worker A: DIRECT caching.
#
# HF_HOME / HF_HUB_CACHE point at a directory ON the network volume, so the model
# is read directly from the (network) mount on every cold start. This is the
# 01_network_volumes approach. Paired with bench_volumecache.py; driven by
# benchmark.py.
#
# Runnable on Flash today (no VolumeCache dependency).
import logging

from runpod_flash import Endpoint, GpuType, NetworkVolume

logger = logging.getLogger(__name__)

# Shared volume so both strategies compete on the same storage medium.
volume = NetworkVolume(name="flash-05-bench-volume", size=50)

HF_ON_VOLUME = "/runpod-volume/hf"


@Endpoint(
    name="bench_direct",
    gpu=GpuType.NVIDIA_GEFORCE_RTX_5090,
    workers=(0, 1),  # single worker so each call is one clean measurement
    idle_timeout=30,  # scale to 0 between trials -> next call is a cold start
    volume=volume,
    env={"HF_HOME": HF_ON_VOLUME, "HF_HUB_CACHE": HF_ON_VOLUME},
    dependencies=["torch", "diffusers", "transformers", "accelerate"],
)
class BenchDirect:
    def __init__(self):
        # Imports/paths live inside the body: @Endpoint ships only the function
        # body to the worker.
        import logging
        import os
        import time

        import torch
        from diffusers import StableDiffusionPipeline

        self.logger = logging.getLogger(__name__)

        hf = os.environ.get("HF_HOME", "/runpod-volume/hf")
        # First run = the on-volume cache was empty before this cold start.
        self._first_run = not (os.path.isdir(hf) and any(os.scandir(hf)))

        t0 = time.perf_counter()
        self.pipe = StableDiffusionPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            torch_dtype=torch.float16,
            safety_checker=None,
            requires_safety_checker=False,
            use_safetensors=True,
            low_cpu_mem_usage=True,
        ).to("cuda")
        self._load_seconds = time.perf_counter() - t0
        self.logger.info(
            f"[direct] load={self._load_seconds:.2f}s first_run={self._first_run}"
        )

    async def benchmark(self) -> dict:
        """Report the cold-start metrics captured during __init__."""
        import os

        def dir_bytes(path):
            total = 0
            for root, _dirs, files in os.walk(path):
                for name in files:
                    try:
                        total += os.path.getsize(os.path.join(root, name))
                    except OSError:
                        pass
            return total

        return {
            "mode": "direct",
            "first_run": self._first_run,
            "load_seconds": round(self._load_seconds, 2),
            "hydrate_seconds": 0.0,
            "volume_bytes": dir_bytes("/runpod-volume/hf"),
            "local_bytes": 0,
        }
