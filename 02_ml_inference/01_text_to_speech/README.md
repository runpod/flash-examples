# Text-to-Speech with Qwen3-TTS

Text-to-Speech API using [Qwen3-TTS-12Hz-1.7B-CustomVoice](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice) running on RunPod serverless GPUs.

## Overview

This example demonstrates running a 1.7B parameter TTS model on serverless GPU infrastructure. It supports 9 voices across 11 languages with optional emotion/style control via natural language instructions.

## What You'll Learn

- Running a HuggingFace model with `@remote` on GPU workers
- Returning binary audio data (WAV) from API endpoints
- Using `bfloat16` precision for memory-efficient inference
- Input validation inside self-contained `@remote` functions

## Quick Start

### Prerequisites

- Python 3.10+
- RunPod API key ([get one here](https://docs.runpod.io/get-started/api-keys))

### Setup

```bash
cd 02_ml_inference/01_text_to_speech
pip install -r requirements.txt
cp .env.example .env
# Add your RUNPOD_API_KEY to .env
```

### Run

```bash
flash run
```

First run provisions the endpoint (~1 min). Server starts at http://localhost:8888

### Test the Endpoint

**Get WAV file directly:**
```bash
curl -X POST http://localhost:8888/gpu/tts/audio \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world!", "speaker": "Ryan", "language": "English"}' \
  --output speech.wav
```

**Get JSON with base64 audio:**
```bash
curl -X POST http://localhost:8888/gpu/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world!", "speaker": "Ryan", "language": "English"}'
```

**With emotion/style control:**
```bash
curl -X POST http://localhost:8888/gpu/tts/audio \
  -H "Content-Type: application/json" \
  -d '{"text": "I have great news!", "speaker": "Ryan", "language": "English", "instruct": "Speak with excitement and joy"}' \
  --output excited.wav
```

**List available voices:**
```bash
curl http://localhost:8888/gpu/voices
```

Visit http://localhost:8888/docs for interactive API documentation.

## API Endpoints

### POST /gpu/tts

Generate speech and return JSON with base64-encoded WAV audio.

**Request:**
```json
{
  "text": "Hello world!",
  "speaker": "Ryan",
  "language": "English",
  "instruct": "Speak warmly"
}
```

**Response:**
```json
{
  "status": "success",
  "audio_base64": "UklGRs4XAgBXQVZF...",
  "sample_rate": 24000,
  "speaker": "Ryan",
  "language": "English"
}
```

### POST /gpu/tts/audio

Generate speech and return raw WAV file directly.

Same request body as `/gpu/tts`. Returns `audio/wav` content type.

### GET /gpu/voices

List available voices and supported languages.

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| text | Yes | - | Text to synthesize |
| speaker | No | Ryan | Voice to use |
| language | No | Auto | Target language |
| instruct | No | - | Emotion/style instruction |

## Voices

| Voice | Style | Native Language |
|-------|-------|-----------------|
| **Ryan** | Dynamic male | English |
| **Aiden** | Sunny American male | English |
| **Vivian** | Bright young female | Chinese |
| **Serena** | Warm gentle female | Chinese |
| **Ono_Anna** | Playful female | Japanese |
| **Sohee** | Warm female | Korean |
| Dylan | Clear male | Chinese (Beijing) |
| Eric | Lively male | Chinese (Sichuan) |
| Uncle_Fu | Deep mellow male | Chinese |

## Supported Languages

Chinese, English, Japanese, Korean, German, French, Russian, Portuguese, Spanish, Italian, Auto

## Deployment

```bash
flash build
flash deploy new production
flash deploy send production
```

## Cost Estimates

- Workers scale to 0 when idle (no charges)
- Pay only for GPU time during generation
- First request after idle: ~20-30s (cold start)
- Subsequent requests: ~5-10s
- GPU: RTX 4090 (24GB VRAM)

## Common Issues

- **Cold start delay**: First request after idle takes 20-30s to load the model. Use `flash run --auto-provision` during development.
- **Out of memory**: The model requires 24GB+ VRAM. Ensure `GpuGroup.ADA_24` or higher is configured.
- **Invalid speaker/language**: Check `/gpu/voices` for valid options.

## References

- [Qwen3-TTS Model Card](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice)
- [Flash Documentation](https://docs.runpod.io)
