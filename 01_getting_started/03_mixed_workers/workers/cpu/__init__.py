from fastapi import APIRouter
from pydantic import BaseModel, field_validator

from .endpoint import postprocess_results, preprocess_text

cpu_router = APIRouter()


class PreprocessRequest(BaseModel):
    """Request model for text preprocessing."""

    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        if len(v) < 3:
            raise ValueError(
                'Text too short (minimum 3 characters). Example: {"text": "Hello world"}'
            )
        if len(v) > 10000:
            raise ValueError(f"Text too long (maximum 10,000 characters). Got {len(v)} characters.")
        return v


@cpu_router.post("/preprocess")
async def preprocess_endpoint(request: PreprocessRequest):
    """
    Preprocess text before GPU inference.

    Fast, cheap CPU operation for validation and cleaning.
    """
    result = await preprocess_text({"text": request.text})
    return result


class Prediction(BaseModel):
    """Individual prediction with label and confidence."""

    label: str
    confidence: float

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {v}")
        return v


class PostprocessRequest(BaseModel):
    """Request model for result postprocessing."""

    predictions: list[Prediction]
    original_text: str
    metadata: dict

    @field_validator("predictions")
    @classmethod
    def validate_predictions_not_empty(cls, v):
        if not v:
            raise ValueError(
                'Predictions cannot be empty. Example: [{"label": "positive", "confidence": 0.9}]'
            )
        return v


@cpu_router.post("/postprocess")
async def postprocess_endpoint(request: PostprocessRequest):
    """
    Postprocess GPU inference results.

    Fast, cheap CPU operation for formatting and aggregation.
    """
    # Convert Pydantic models to dicts for remote serialization
    result = await postprocess_results(
        {
            "predictions": [pred.model_dump() for pred in request.predictions],
            "original_text": request.original_text,
            "metadata": request.metadata,
        }
    )
    return result
