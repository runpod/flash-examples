from runpod_flash import GpuGroup, LiveServerless, remote

# GPU config for Parakeet-TDT - needs 8GB+ VRAM for 0.6B model
# Naming convention: {category}_{example}_{worker_type}
gpu_config = LiveServerless(
    name="02_02_speech_to_text_gpu",
    gpus=[GpuGroup.ADA_24],  # RTX 4090 or similar with 24GB (can work with less)
    workersMin=0,
    workersMax=3,
    idleTimeout=5,
)


@remote(
    resource_config=gpu_config,
    dependencies=[
        "nemo_toolkit[asr]",
        "torch",
    ],
)
async def transcribe_audio(input_data: dict) -> dict:
    """
    Transcribe audio using NVIDIA Parakeet-TDT-0.6B-v2 model.

    Input:
        audio_url: str - URL of the audio file to transcribe (WAV or FLAC)
        timestamps: bool - Whether to include timestamps in the output (default: False)

    Returns:
        text: str - Transcribed text with punctuation and capitalization
        timestamps: dict (optional) - Word, segment, and character-level timestamps
        duration: float - Audio duration in seconds
    """
    import time
    from datetime import datetime
    from io import BytesIO
    from urllib.request import urlopen

    import nemo.collections.asr as nemo_asr
    import soundfile as sf

    audio_url = input_data.get("audio_url")
    include_timestamps = input_data.get("timestamps", False)

    if not audio_url:
        return {
            "status": "error",
            "error": "audio_url is required",
        }

    try:
        # Load the model (cached after first load)
        asr_model = nemo_asr.models.ASRModel.from_pretrained(
            model_name="nvidia/parakeet-tdt-0.6b-v2"
        )

        # Download audio file
        start_time = time.time()
        response = urlopen(audio_url)
        audio_bytes = response.read()

        # Load audio data
        audio_data, sample_rate = sf.read(BytesIO(audio_bytes))

        # Calculate duration
        duration = len(audio_data) / sample_rate

        # Save to temporary file (NeMo expects file paths)
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
            sf.write(temp_path, audio_data, sample_rate)

        # Transcribe with or without timestamps
        output = asr_model.transcribe([temp_path], timestamps=include_timestamps)

        # Clean up temp file
        import os

        os.unlink(temp_path)

        processing_time = time.time() - start_time

        result = {
            "status": "success",
            "text": output[0].text,
            "duration": duration,
            "processing_time": processing_time,
            "sample_rate": sample_rate,
            "timestamp": datetime.now().isoformat(),
        }

        if include_timestamps and hasattr(output[0], "timestamp"):
            result["timestamps"] = {
                "word": output[0].timestamp.get("word", []),
                "segment": output[0].timestamp.get("segment", []),
                "char": output[0].timestamp.get("char", []),
            }

        return result

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@remote(resource_config=gpu_config, dependencies=["nemo_toolkit[asr]"])
async def get_model_info(input_data: dict) -> dict:
    """Get model information and capabilities."""
    return {
        "status": "success",
        "model": "nvidia/parakeet-tdt-0.6b-v2",
        "parameters": "600M",
        "architecture": "FastConformer-TDT",
        "supported_formats": ["WAV", "FLAC"],
        "sample_rate": "16kHz",
        "max_duration": "24 minutes per pass",
        "features": [
            "Automatic punctuation",
            "Automatic capitalization",
            "Word-level timestamps",
            "Segment-level timestamps",
            "Character-level timestamps",
        ],
        "license": "CC-BY-4.0",
    }


# Test locally with: python -m workers.gpu.endpoint
if __name__ == "__main__":
    import asyncio

    # Test model info
    print("Model Information:")
    result = asyncio.run(get_model_info({}))
    print(result)

    # Test transcription (requires GPU)
    test_payload = {
        "audio_url": "https://dldata-public.s3.us-east-2.amazonaws.com/2086-149220-0033.wav",
        "timestamps": True,
    }
    print(f"\nTesting transcription with payload: {test_payload}")
    result = asyncio.run(transcribe_audio(test_payload))
    if result["status"] == "success":
        print(f"Success! Transcription: {result['text']}")
        if "timestamps" in result:
            print(f"Timestamps available: {len(result['timestamps']['word'])} words")
    else:
        print(f"Error: {result}")
