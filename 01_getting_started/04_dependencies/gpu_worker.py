# gpu workers demonstrating Python and system dependency management.
# run with: flash run
# test directly: python gpu_worker.py
from runpod_flash import Endpoint, GpuGroup


@Endpoint(
    name="01_04_deps_ml",
    gpu=GpuGroup.ADA_32_PRO,
    workers=(0, 2),
    dependencies=[
        "requests==2.32.3",  # Pin specific version
        "Pillow>=10.0.0",  # Minimum version
        "python-dateutil<3.0.0",  # Maximum version constraint
        "httpx",  # Unpinned
    ],
)
async def process_with_ml_libs(payload: dict) -> dict:
    """
    Worker with lightweight, versioned Python dependencies.

    Best practices:
    - Pin exact versions for reproducibility (requests==2.32.3)
    - Use >= for minimum versions (Pillow>=10.0.0)
    - Use < to avoid breaking changes (python-dateutil<3.0.0)
    """
    from datetime import datetime

    import httpx
    import requests
    from importlib.metadata import version
    from PIL import Image

    versions = {
        "requests": str(requests.__version__),
        "httpx": str(httpx.__version__),
        "python_dateutil": str(version("python-dateutil")),
        "pillow": str(Image.__version__),
    }

    return {
        "status": "success",
        "message": "Python dependencies loaded successfully",
        "versions": versions,
        "payload_keys": list(payload.keys()),
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
