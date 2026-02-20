# Qwen3-TTS text-to-speech GPU worker.
# Run with: flash run
# Test directly: python gpu_worker.py

from runpod_flash import GpuGroup, LiveServerless, remote

# GPU config for Qwen3-TTS - needs 24GB+ VRAM for 1.7B model
# Naming convention: {category}_{example}_{worker_type}
gpu_config = LiveServerless(
    name="02_01_text_to_speech_gpu",
    gpus=[GpuGroup.ADA_24],  # RTX 4090 or similar with 24GB
    workersMin=0,
    workersMax=3,
    idleTimeout=5,
)


@remote(
    resource_config=gpu_config,
    dependencies=[
        "qwen-tts",
        "torch",
        "soundfile",
    ],
)
async def generate_speech(input_data: dict) -> dict:
    """
    Generate speech using Qwen3-TTS-12Hz-1.7B-CustomVoice model.

    Input:
        text: str - The text to synthesize
        speaker: str - Voice to use (default: Ryan)
        language: str - Target language (default: Auto)
        instruct: str (optional) - Emotion/style instruction

    Returns:
        audio_base64: str - Base64 encoded WAV audio
        sample_rate: int - Audio sample rate
        speaker: str - Speaker used
        language: str - Language used
    """
    import base64
    import io
    from datetime import datetime

    import soundfile as sf
    import torch

    # Must be defined inside function for remote execution
    valid_speakers = [
        "Vivian",
        "Serena",
        "Uncle_Fu",
        "Dylan",
        "Eric",
        "Ryan",
        "Aiden",
        "Ono_Anna",
        "Sohee",
    ]
    valid_languages = [
        "Chinese",
        "English",
        "Japanese",
        "Korean",
        "German",
        "French",
        "Russian",
        "Portuguese",
        "Spanish",
        "Italian",
        "Auto",
    ]

    text = input_data.get("text", "Hello, this is a test.")
    speaker = input_data.get("speaker", "Ryan")
    language = input_data.get("language", "Auto")
    instruct = input_data.get("instruct", "")

    if speaker not in valid_speakers:
        return {
            "status": "error",
            "error": f"Invalid speaker '{speaker}'. Valid options: {valid_speakers}",
        }

    if language not in valid_languages:
        return {
            "status": "error",
            "error": f"Invalid language '{language}'. Valid options: {valid_languages}",
        }

    try:
        from qwen_tts import Qwen3TTSModel

        model = Qwen3TTSModel.from_pretrained(
            "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
            device_map="cuda:0",
            dtype=torch.bfloat16,
        )

        generate_kwargs = {
            "text": text,
            "language": language,
            "speaker": speaker,
        }
        if instruct:
            generate_kwargs["instruct"] = instruct

        wavs, sr = model.generate_custom_voice(**generate_kwargs)

        buffer = io.BytesIO()
        sf.write(buffer, wavs[0], sr, format="WAV")
        buffer.seek(0)
        audio_base64 = base64.b64encode(buffer.read()).decode("utf-8")

        return {
            "status": "success",
            "audio_base64": audio_base64,
            "sample_rate": sr,
            "speaker": speaker,
            "language": language,
            "instruct": instruct if instruct else None,
            "text": text,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@remote(resource_config=gpu_config, dependencies=["qwen-tts"])
async def get_voices(input_data: dict) -> dict:
    """Get available voices and languages."""
    speakers = {
        "Vivian": "Bright, slightly edgy young female voice (Chinese native)",
        "Serena": "Warm, gentle young female voice (Chinese native)",
        "Uncle_Fu": "Seasoned male voice with low, mellow timbre (Chinese native)",
        "Dylan": "Youthful Beijing male voice, clear natural timbre (Beijing dialect)",
        "Eric": "Lively Chengdu male voice, slightly husky (Sichuan dialect)",
        "Ryan": "Dynamic male voice with strong rhythmic drive (English native)",
        "Aiden": "Sunny American male voice with clear midrange (English native)",
        "Ono_Anna": "Playful Japanese female voice, light nimble timbre (Japanese native)",
        "Sohee": "Warm Korean female voice with rich emotion (Korean native)",
    }
    languages = [
        "Chinese",
        "English",
        "Japanese",
        "Korean",
        "German",
        "French",
        "Russian",
        "Portuguese",
        "Spanish",
        "Italian",
        "Auto",
    ]
    return {
        "status": "success",
        "speakers": speakers,
        "languages": languages,
    }


# Test locally with: python gpu_worker.py
if __name__ == "__main__":
    import asyncio

    # Test get_voices
    print("Available voices:")
    result = asyncio.run(get_voices({}))
    print(result)

    # Test speech generation (requires GPU)
    test_payload = {
        "text": "Hello! This is a test of the Qwen3 text to speech system.",
        "speaker": "Ryan",
        "language": "English",
        "instruct": "Speak in a friendly, warm tone.",
    }
    print(f"\nTesting TTS with payload: {test_payload}")
    result = asyncio.run(generate_speech(test_payload))
    if result["status"] == "success":
        print(f"Success! Audio generated, {len(result['audio_base64'])} bytes (base64)")
    else:
        print(f"Error: {result}")
