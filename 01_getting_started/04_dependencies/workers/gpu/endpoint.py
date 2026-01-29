from tetra_rp import GpuGroup, LiveServerless, remote

# Worker with ML dependencies (versioned)
ml_config = LiveServerless(
    name="01_04_deps_ml",
    gpus=[GpuGroup.ADA_32_PRO],
    workersMin=0,
    workersMax=2,
)

# Worker with system dependencies
system_deps_config = LiveServerless(
    name="01_04_deps_system",
    gpus=[GpuGroup.AMPERE_16],
    workersMin=0,
    workersMax=2,
)


@remote(
    resource_config=ml_config,
    dependencies=[
        "torch==2.1.0",  # Pin specific version
        "torchvision",
        "Pillow>=10.0.0",  # Minimum version
        "numpy<2.0.0",  # Maximum version constraint
    ],
)
async def process_with_ml_libs(input_data: dict) -> dict:
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

    # Show installed versions
    versions = {
        "torch": torch.__version__,
        "torchvision": torchvision.__version__,
        "pillow": Image.__version__,
        "numpy": np.__version__,
    }

    # Simple tensor operation to verify GPU
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


@remote(
    resource_config=system_deps_config,
    dependencies=["opencv-python", "requests"],
    system_dependencies=["ffmpeg", "libgl1"],  # System packages via apt
)
async def process_with_system_deps(input_data: dict) -> dict:
    """
    Worker with system-level dependencies.

    system_dependencies installs via apt-get:
    - ffmpeg: Video/audio processing
    - libgl1: OpenCV requirement
    """
    import subprocess
    from datetime import datetime

    import cv2

    # Check FFmpeg installation
    try:
        ffmpeg_version = (
            subprocess.check_output(["ffmpeg", "-version"], stderr=subprocess.STDOUT)
            .decode()
            .split("\n")[0]
        )
    except Exception as e:
        ffmpeg_version = f"Error: {e}"

    # Check OpenCV (requires libgl1)
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

    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv())  # Find and load root .env file

    async def test():
        print("\n=== Testing ML Dependencies ===")
        ml_result = await process_with_ml_libs({})
        print(f"Result: {ml_result}\n")

        print("=== Testing System Dependencies ===")
        sys_result = await process_with_system_deps({})
        print(f"Result: {sys_result}\n")

    asyncio.run(test())
