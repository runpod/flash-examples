# CPU worker with network volume for listing and serving generated images.
# Run with: flash run
# Test directly: python cpu_worker.py
from runpod_flash import CpuLiveLoadBalancer, NetworkVolume, remote

volume = NetworkVolume(
    name="flash-05-volume",
    size=50,
)

cpu_config = CpuLiveLoadBalancer(
    name="05_01_cpu_worker",
    workersMin=1,
    networkVolume=volume,
)


@remote(resource_config=cpu_config, path="/images", method="GET")
async def list_images_in_volume() -> dict:
    """List generated images from the shared volume."""
    import os

    image_dir = "/runpod-volume/generated_images"
    images = os.listdir(image_dir)

    return {
        "status": "success",
        "images": images,
    }


@remote(resource_config=cpu_config, path="/images/{file_name}", method="GET")
async def get_image_from_volume(file_name: str) -> dict:
    """Get image metadata from the shared volume."""
    import base64
    from pathlib import Path

    image_path = Path(f"/runpod-volume/generated_images/{file_name}")

    if not image_path.is_file():
        return {"status": "error", "error": "file not found"}

    image_bytes = image_path.read_bytes()
    return {
        "status": "success",
        "filename": image_path.name,
        "size_bytes": len(image_bytes),
        "image_base64": base64.b64encode(image_bytes).decode("utf-8"),
    }


if __name__ == "__main__":
    import asyncio

    print(
        "Checking cpu worker by listing image files in /runpod-volume/generated_images/"
    )
    result = asyncio.run(list_images_in_volume())
    print(f"Result: {result}")
