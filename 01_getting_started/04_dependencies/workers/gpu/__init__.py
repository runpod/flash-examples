from fastapi import APIRouter

from .endpoint import process_with_ml_libs, process_with_system_deps

gpu_router = APIRouter()


@gpu_router.post("/ml-deps")
async def ml_deps_endpoint():
    """Test worker with ML dependencies (torch, pillow, numpy)."""
    result = await process_with_ml_libs({})
    return result


@gpu_router.post("/system-deps")
async def system_deps_endpoint():
    """Test worker with system dependencies (ffmpeg, libgl1)."""
    result = await process_with_system_deps({})
    return result
