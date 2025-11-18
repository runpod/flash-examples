from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

from .endpoint import gpu_inference

gpu_router = APIRouter()


class InferenceRequest(BaseModel):
    """Request model for GPU inference."""

    cleaned_text: str
    word_count: int = Field(ge=0)

    @field_validator("cleaned_text")
    @classmethod
    def validate_text_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Cleaned text cannot be empty")
        return v


@gpu_router.post("/inference")
async def inference_endpoint(request: InferenceRequest):
    """
    Run ML inference on GPU.

    Expensive GPU operation - only use after CPU preprocessing.
    """
    result = await gpu_inference(
        {
            "cleaned_text": request.cleaned_text,
            "word_count": request.word_count,
        }
    )
    return result
