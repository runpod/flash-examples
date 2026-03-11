# cpu worker with network volume for listing and serving generated images.
# run with: flash run
# test directly: python cpu_worker.py
from runpod_flash import Endpoint, DataCenter, NetworkVolume

# same volume as gpu_worker.py -- must match name and datacenter
volume = NetworkVolume(
    name="flash-05-volume",
    size=50,
    datacenter=DataCenter.EU_RO_1,
)

api = Endpoint(
    name="05_01_cpu_worker",
    cpu="cpu3c-1-2",
    workers=(1, 3),
    idle_timeout=120,
    datacenter=DataCenter.EU_RO_1,
    volume=volume,
)


@api.get("/images")
async def list_images_in_volume() -> dict:
    """List generated images from the shared volume."""
    import os

    image_dir = "/runpod-volume/generated_images"
    if not os.path.isdir(image_dir):
        return {"status": "success", "images": []}

    return {
        "status": "success",
        "images": os.listdir(image_dir),
    }


@api.get("/images/{file_name}")
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
