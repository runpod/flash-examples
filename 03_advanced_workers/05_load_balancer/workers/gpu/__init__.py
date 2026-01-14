"""GPU Load-Balancer Endpoints

Load-balancer endpoints use the @remote decorator with method and path parameters.
These decorators automatically create HTTP routes that are registered with the
Load Balancer runtime.

For the unified app discovery, we export a router that documents the endpoints.
The actual HTTP handling is managed by the tetra-rp-lb framework.
"""

from fastapi import APIRouter
from pydantic import BaseModel, field_validator

from .endpoint import compute_intensive, gpu_config, gpu_health, gpu_info


class ComputeRequest(BaseModel):
    """Request model for compute-intensive operations."""

    numbers: list[int]

    @field_validator("numbers")
    @classmethod
    def validate_numbers(cls, v: list[int]) -> list[int]:
        """Validate that numbers list is not empty."""
        if not v:
            raise ValueError("numbers list cannot be empty")
        return v


# Export for unified app discovery
gpu_router = APIRouter()


@gpu_router.get("/health")
async def get_gpu_health():
    """GPU service health check."""
    return await gpu_health()


@gpu_router.post("/compute")
async def post_gpu_compute(request: ComputeRequest):
    """Perform compute-intensive operation on GPU."""
    return await compute_intensive(request.model_dump())


@gpu_router.get("/info")
async def get_gpu_info():
    """Get GPU device information."""
    return await gpu_info()


__all__ = [
    "ComputeRequest",
    "compute_intensive",
    "gpu_config",
    "gpu_health",
    "gpu_info",
    "gpu_router",
]
