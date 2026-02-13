from fastapi import APIRouter
from pydantic import BaseModel, Field, HttpUrl

from .endpoint import get_model_info, transcribe_audio

gpu_router = APIRouter()


class TranscribeRequest(BaseModel):
    """Request model for audio transcription."""

    audio_url: HttpUrl = Field(
        ..., description="URL of the audio file to transcribe (WAV or FLAC format)"
    )
    timestamps: bool = Field(
        default=False,
        description="Include word, segment, and character-level timestamps in the output",
    )


class TimestampInfo(BaseModel):
    """Timestamp information for words, segments, or characters."""

    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    word: str | None = Field(None, description="Word text (for word timestamps)")
    segment: str | None = Field(None, description="Segment text (for segment timestamps)")
    char: str | None = Field(None, description="Character (for char timestamps)")


class TranscribeResponse(BaseModel):
    """Response model for audio transcription."""

    status: str = Field(..., description="Status of the request")
    text: str | None = Field(None, description="Transcribed text with punctuation and capitalization")
    duration: float | None = Field(None, description="Audio duration in seconds")
    processing_time: float | None = Field(None, description="Processing time in seconds")
    sample_rate: int | None = Field(None, description="Audio sample rate")
    timestamps: dict | None = Field(None, description="Timestamp information (if requested)")
    error: str | None = Field(None, description="Error message if status is error")


@gpu_router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio_endpoint(request: TranscribeRequest) -> dict:
    """
    Transcribe audio from a URL using NVIDIA Parakeet-TDT-0.6B-v2.

    Returns JSON with transcribed text and optional timestamps.
    """
    payload = {
        "audio_url": str(request.audio_url),
        "timestamps": request.timestamps,
    }

    result = await transcribe_audio(payload)
    return result


@gpu_router.get("/model-info")
async def model_info() -> dict:
    """Get information about the Parakeet-TDT model and its capabilities."""
    result = await get_model_info({})
    return result
