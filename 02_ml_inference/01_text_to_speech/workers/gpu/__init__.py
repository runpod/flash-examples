import base64

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .endpoint import generate_speech, get_voices

gpu_router = APIRouter()


class TTSRequest(BaseModel):
    """Request model for text-to-speech generation."""

    text: str = Field(..., description="The text to synthesize into speech")
    speaker: str = Field(
        default="Ryan",
        description="Voice to use. Options: Vivian, Serena, Uncle_Fu, Dylan, Eric, Ryan, Aiden, Ono_Anna, Sohee",
    )
    language: str = Field(
        default="Auto",
        description="Language. Options: Chinese, English, Japanese, Korean, German, French, Russian, Portuguese, Spanish, Italian, Auto",
    )
    instruct: str | None = Field(
        default=None,
        description="Optional emotion/style instruction (e.g., 'Speak happily', 'Say it slowly and calmly')",
    )


@gpu_router.post("/tts")
async def text_to_speech(request: TTSRequest) -> dict:
    """
    Generate speech from text using Qwen3-TTS.

    Returns JSON with base64-encoded WAV audio.
    """
    payload = {
        "text": request.text,
        "speaker": request.speaker,
        "language": request.language,
    }
    if request.instruct:
        payload["instruct"] = request.instruct

    result = await generate_speech(payload)
    return result


@gpu_router.post("/tts/audio")
async def text_to_speech_audio(request: TTSRequest) -> Response:
    """
    Generate speech from text using Qwen3-TTS.

    Returns raw WAV audio file directly.
    """
    payload = {
        "text": request.text,
        "speaker": request.speaker,
        "language": request.language,
    }
    if request.instruct:
        payload["instruct"] = request.instruct

    result = await generate_speech(payload)

    if result["status"] == "error":
        return result

    audio_bytes = base64.b64decode(result["audio_base64"])
    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={"Content-Disposition": "attachment; filename=speech.wav"},
    )


@gpu_router.get("/voices")
async def list_voices() -> dict:
    """Get available voices and languages."""
    result = await get_voices({})
    return result
