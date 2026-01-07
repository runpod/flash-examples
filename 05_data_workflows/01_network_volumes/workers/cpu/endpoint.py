from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse

from tetra_rp import CpuInstanceType, CpuLiveServerless, remote

from .. import volume

cpu_config = CpuLiveServerless(
    name="cpu_worker",
    instanceIds=[CpuInstanceType.ANY],
    workersMin=0,
    workersMax=2,
    idleTimeout=5,
    env={"LOG_LEVEL": "DEBUG"},
    networkVolume=volume,
)

@remote(resource_config=cpu_config)
async def list_images_in_volume() -> dict:
    import os
    """Simple CPU worker example."""
    image_dir = "/runpod-volume/generated_images"
    images = os.listdir(image_dir)


    return {
        "status": "success",
        "images": images,
    }

@remote(resource_config=cpu_config, dependencies=["fastapi"])
async def get_image_from_volume(file_id: str) -> "FileResponse":
    from pathlib import Path

    image_path = Path(f"/runpod-volume/generated_images/{file_id}")

    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="file not found")

    from fastapi.responses import FileResponse
    return FileResponse(image_path, media_type="image/png", filename=image_path.name)

# Test locally with: python -m workers.cpu.endpoint
if __name__ == "__main__":
    import asyncio

    print("checking cpu worker by listing image files in /runpod-volume/generated_images/")
    result = asyncio.run(list_images_in_volume())
    print(f"Result: {result}")
