from fastapi import APIRouter
from pydantic import BaseModel

from .endpoint import get_image_from_volume, list_images_in_volume

cpu_router = APIRouter()


@cpu_router.get("/image")
async def list_images():
    # Simple index of files produced by the GPU worker.
    result = await list_images_in_volume()
    return result


@cpu_router.get("/image/{file_id}")
async def get_image(file_id: str):
    # Serve a single image file from the shared volume.
    result = await get_image_from_volume(file_id)
    return result
