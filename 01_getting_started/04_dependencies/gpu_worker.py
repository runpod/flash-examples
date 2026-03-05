# gpu workers demonstrating Python and system dependency management.
# run with: flash run
# test directly: python gpu_worker.py
from runpod_flash import Endpoint, GpuGroup


@Endpoint(
    name="01_04_deps_ml",
    gpu=GpuGroup.ADA_32_PRO,
    workers=(0, 2),
    dependencies=[
        "torch==2.1.0",
        "torchvision",
        "Pillow>=10.0.0",
        "numpy<2.0.0",
    ],
)
async def process_with_ml_libs(payload: dict) -> dict:
    """
    Worker with versioned Python dependencies.

    Best practices:
    - Pin exact versions for reproducibility (torch==2.1.0)
    - Use >= for minimum versions (Pillow>=10.0.0)
    - Use < to avoid breaking changes (numpy<2.0.0)
    """
    from datetime import datetime

    import numpy as np
    import torch
    import torchvision
    from PIL import Image

    versions = {
        "torch": torch.__version__,
        "torchvision": torchvision.__version__,
        "pillow": Image.__version__,
        "numpy": np.__version__,
    }

    if torch.cuda.is_available():
        tensor = torch.randn(100, 100, device="cuda")
        result = tensor.sum().item()
    else:
        result = "No GPU available"

    return {
        "status": "success",
        "message": "ML dependencies loaded successfully",
        "versions": versions,
        "gpu_test": result,
        "timestamp": datetime.now().isoformat(),
    }


@Endpoint(
    name="01_04_deps_system",
    gpu=GpuGroup.AMPERE_16,
    workers=(0, 2),
    dependencies=["opencv-python", "requests"],
    system_dependencies=["ffmpeg", "libgl1"],
)
async def process_with_system_deps(payload: dict) -> dict:
    """
    Worker with system-level dependencies.

    system_dependencies installs via apt-get:
    - ffmpeg: Video/audio processing
    - libgl1: OpenCV requirement
    """
    import subprocess
    from datetime import datetime

    import cv2

    try:
        ffmpeg_version = (
            subprocess.check_output(["ffmpeg", "-version"], stderr=subprocess.STDOUT)
            .decode()
            .split("\n")[0]
        )
    except Exception as e:
        ffmpeg_version = f"Error: {e}"

    opencv_version = cv2.__version__

    return {
        "status": "success",
        "message": "System dependencies available",
        "opencv_version": opencv_version,
        "ffmpeg_version": ffmpeg_version,
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import asyncio

    async def test():
        print("\n=== Testing ML Dependencies ===")
        ml_result = await process_with_ml_libs({})
        print(f"Result: {ml_result}\n")

        print("=== Testing System Dependencies ===")
        sys_result = await process_with_system_deps({})
        print(f"Result: {sys_result}\n")

    asyncio.run(test())
