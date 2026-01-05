"""CPU Load-Balancer Endpoints

Load-balancer endpoints use the @remote decorator with method and path parameters.
These decorators automatically create HTTP routes that are registered with the
Load Balancer runtime.

For the unified app discovery, we export a router that documents the endpoints.
The actual HTTP handling is managed by the tetra-rp-lb framework.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from .endpoint import cpu_config, cpu_health, transform_data, validate_data


# Pydantic models for request validation
class ValidateRequest(BaseModel):
    """Request model for text validation."""

    text: str


class TransformRequest(BaseModel):
    """Request model for text transformation."""

    text: str
    operation: str = "uppercase"


# Export for unified app discovery
cpu_router = APIRouter()


@cpu_router.get("/health")
async def get_cpu_health():
    """CPU service health check."""
    return await cpu_health()


@cpu_router.post("/validate")
async def post_validate(request: ValidateRequest):
    """Validate and analyze text data."""
    return await validate_data(request.text)


@cpu_router.post("/transform")
async def post_transform(request: TransformRequest):
    """Transform text data with specified operation."""
    return await transform_data(request.text, request.operation)


__all__ = ["cpu_config", "cpu_health", "cpu_router", "transform_data", "validate_data"]
