# Benchmark worker B: VOLUMECACHE strategy.
#
# HF cache stays on local disk; runpod.serverless.VolumeCache hydrates it from
# the network volume before the load and syncs new files back after. Reads are
# local; the volume is a warm mirror. Paired with bench_direct.py; driven by
# benchmark.py.
#
# PREREQUISITE: the deployed flash-worker image must include VolumeCache
# (SLS-367 / runpod-python PR #531). It cannot be added at runtime via the
# dependencies list because the worker's runpod is already imported before the
# handler runs. Until flash-worker ships it, this arm will fail to import
# VolumeCache — see benchmark/README.md.
import logging

from runpod_flash import Endpoint, GpuType, NetworkVolume

logger = logging.getLogger(__name__)

# Same volume as bench_direct so both strategies compete on the same medium.
volume = NetworkVolume(name="flash-05-bench-volume", size=50)


@Endpoint(
    name="bench_volumecache",
    gpu=GpuType.NVIDIA_GEFORCE_RTX_5090,
    workers=(0, 1),
    idle_timeout=30,
    volume=volume,
    dependencies=["torch", "diffusers", "transformers", "accelerate"],
)
class BenchVolumeCache:
    def __init__(self):
        import logging
        import os
        import time

        import torch
        from diffusers import StableDiffusionPipeline
        from runpod.serverless import VolumeCache

        self.logger = logging.getLogger(__name__)

        # HF cache on local disk (default). VolumeCache mirrors it to the volume.
        hf = os.path.expanduser("~/.cache/huggingface")
        self._hf = hf
        self._vc = VolumeCache(dirs=[hf])

        # Mirror location is {volume}/.cache/{RUNPOD_ENDPOINT_ID}; empty = first run.
        self._mirror = os.path.join(
            "/runpod-volume", ".cache", os.environ.get("RUNPOD_ENDPOINT_ID", "")
        )
        self._first_run = not (
            os.path.isdir(self._mirror) and any(os.scandir(self._mirror))
        )

        t0 = time.perf_counter()
        self._files_hydrated = self._vc.hydrate()  # volume -> local
        self._hydrate_seconds = time.perf_counter() - t0

        self.pipe = StableDiffusionPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            torch_dtype=torch.float16,
            safety_checker=None,
            requires_safety_checker=False,
            use_safetensors=True,
            low_cpu_mem_usage=True,
        ).to("cuda")
        # Total cold-start-to-ready time, including the hydrate copy.
        self._load_seconds = time.perf_counter() - t0

        self._vc.sync()  # local -> volume, in the background
        self.logger.info(
            f"[volumecache] load={self._load_seconds:.2f}s "
            f"hydrate={self._hydrate_seconds:.2f}s first_run={self._first_run}"
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
            "mode": "volumecache",
            "first_run": self._first_run,
            "files_hydrated": self._files_hydrated,
            "load_seconds": round(self._load_seconds, 2),
            "hydrate_seconds": round(self._hydrate_seconds, 2),
            "local_bytes": dir_bytes(self._hf),
            "volume_bytes": dir_bytes(self._mirror),
        }
