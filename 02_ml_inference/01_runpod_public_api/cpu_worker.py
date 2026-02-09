"""Worker module for calling Runpod public text-to-image endpoint."""

import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from tetra_rp import ServerlessEndpoint

logger = logging.getLogger(__name__)

# Configure public endpoint reference
# For public endpoints, use the endpoint ID with a minimal template
public_endpoint = ServerlessEndpoint(
    name="public-t2i-worker",
    id="p-image-t2i",
)


async def generate_image_from_public_endpoint(
    prompt: str,
    aspect_ratio: str = "16:9",
    enable_safety_checker: bool = True,
    seed: int = 0,
) -> dict:
    """Call Runpod public endpoint for image generation.

    Args:
        prompt: Text description of desired image
        aspect_ratio: Image aspect ratio (16:9, 1:1, 9:16)
        enable_safety_checker: Enable content safety checking
        seed: Random seed for reproducibility

    Returns:
        Dictionary with job_id and image_url

    Raises:
        ValueError: If input is invalid or job failed
    """
    # Validate input
    if not prompt or not prompt.strip():
        raise ValueError("Prompt is required and cannot be empty")

    if len(prompt) > 1000:
        raise ValueError("Prompt must be 1000 characters or less")

    # Prepare input for public endpoint
    input_data = {
        "prompt": prompt.strip(),
        "aspect_ratio": aspect_ratio,
        "enable_safety_checker": enable_safety_checker,
        "seed": seed,
    }

    logger.info(
        "Submitting image generation job",
        extra={"prompt_length": len(prompt), "aspect_ratio": aspect_ratio},
    )

    # Call public endpoint - SDK handles job submission and polling
    job_output = await public_endpoint.run_sync(payload=input_data)

    # Check for errors
    if job_output.error:
        logger.error(
            "Image generation failed",
            extra={"job_id": job_output.id, "error": job_output.error},
        )
        raise ValueError(f"Image generation failed: {job_output.error}")

    # Extract image URL from output
    output = job_output.output or {}
    image_url = output.get("image_url")

    if not image_url:
        logger.error(
            "No image URL in response",
            extra={"job_id": job_output.id, "output": output},
        )
        raise ValueError("No image URL in response")

    logger.info(
        "Image generation succeeded",
        extra={"job_id": job_output.id, "has_image": bool(image_url)},
    )

    return {
        "status": "success",
        "job_id": job_output.id,
        "image_url": image_url,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "seed": seed,
    }


# Router for API endpoints
# Named cpu_router to match Flash discovery pattern
cpu_router = APIRouter()


class ImageRequest(BaseModel):
    """Request model for image generation."""

    prompt: str = Field(..., min_length=1, max_length=1000, description="Text description of image")
    aspect_ratio: str = Field(
        default="16:9",
        pattern="^(16:9|1:1|9:16)$",
        description="Image aspect ratio",
    )
    enable_safety_checker: bool = Field(default=True, description="Enable content safety checking")
    seed: int = Field(default=0, ge=0, le=2147483647, description="Random seed")


class ImageResponse(BaseModel):
    """Response model for image generation."""

    status: str
    job_id: str
    image_url: str
    prompt: str
    aspect_ratio: str
    seed: int


@cpu_router.post("/generate", response_model=ImageResponse, status_code=status.HTTP_200_OK)
async def generate_image_endpoint(request: ImageRequest) -> ImageResponse:
    """Generate image from text prompt using Runpod public endpoint.

    Request:
        - prompt: Text description of desired image
        - aspect_ratio: 16:9, 1:1, or 9:16
        - enable_safety_checker: Enable/disable content filtering
        - seed: Random seed for reproducibility

    Returns:
        Image generation result with job_id and image_url

    Raises:
        HTTPException 400: Invalid input or generation failed
        HTTPException 500: Unexpected error
    """
    try:
        result = await generate_image_from_public_endpoint(
            prompt=request.prompt,
            aspect_ratio=request.aspect_ratio,
            enable_safety_checker=request.enable_safety_checker,
            seed=request.seed,
        )
        return ImageResponse(**result)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Generation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image generation failed. Check server logs.",
        ) from e


# Test the endpoint locally
if __name__ == "__main__":
    import asyncio

    async def test():
        """Test the image generation function."""
        print("Testing public endpoint image generation...")
        try:
            result = await generate_image_from_public_endpoint(
                prompt="A majestic liger standing on a rocky cliff at sunset",
                aspect_ratio="16:9",
                seed=0,
            )
            print(f"Success! Job ID: {result['job_id']}")
            print(f"Image URL: {result['image_url']}")
        except Exception as e:
            print(f"Error: {e}")

    asyncio.run(test())
