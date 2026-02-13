# Speech-to-Text with Parakeet-TDT

Automatic Speech Recognition (ASR) API using [NVIDIA Parakeet-TDT-0.6B-v2](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2) running on RunPod serverless GPUs.

## Overview

This example demonstrates running a 600M parameter automatic speech recognition model on serverless GPU infrastructure. Parakeet-TDT is a high-performance English transcription model that provides accurate text output with automatic punctuation, capitalization, and detailed timestamp predictions.

## What You'll Learn

- Running a NeMo ASR model with `@remote` on GPU workers
- Processing audio files from URLs with automatic format handling
- Returning transcription results with word-level timestamps
- Using efficient FastConformer-TDT architecture for real-time inference
- Input validation for audio processing endpoints

## Architecture

Parakeet-TDT-0.6B-v2 is based on the FastConformer-TDT architecture and achieves:
- **Average WER**: 6.05% across major benchmarks
- **RTFx Performance**: 3380 at batch size 128
- **Max Duration**: Up to 24 minutes of audio per pass
- **Parameters**: 600 million

## Quick Start

### Prerequisites

- Python 3.10+
- RunPod API key ([get one here](https://docs.runpod.io/get-started/api-keys))

### Setup

```bash
cd 02_ml_inference/02_speech_to_text
pip install -r requirements.txt
cp .env.example .env
# Add your RUNPOD_API_KEY to .env
```

### Run

```bash
flash run
```

First run provisions the endpoint (~1-2 min). Server starts at http://localhost:8888

### Test the Endpoint

**Basic transcription:**
```bash
curl -X POST http://localhost:8888/gpu/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "https://dldata-public.s3.us-east-2.amazonaws.com/2086-149220-0033.wav"
  }'
```

**With timestamps:**
```bash
curl -X POST http://localhost:8888/gpu/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "https://dldata-public.s3.us-east-2.amazonaws.com/2086-149220-0033.wav",
    "timestamps": true
  }'
```

**Get model information:**
```bash
curl http://localhost:8888/gpu/model-info
```

Visit http://localhost:8888/docs for interactive API documentation.

## API Endpoints

### POST /gpu/transcribe

Transcribe audio from a URL and return text with optional timestamps.

**Request:**
```json
{
  "audio_url": "https://example.com/audio.wav",
  "timestamps": false
}
```

**Response (without timestamps):**
```json
{
  "status": "success",
  "text": "This is the transcribed text with proper punctuation and capitalization.",
  "duration": 5.2,
  "processing_time": 0.8,
  "sample_rate": 16000,
  "timestamp": "2026-02-13T10:30:00.000000"
}
```

**Response (with timestamps):**
```json
{
  "status": "success",
  "text": "This is the transcribed text.",
  "duration": 5.2,
  "processing_time": 0.9,
  "sample_rate": 16000,
  "timestamps": {
    "word": [
      {"start": 0.0, "end": 0.2, "word": "This"},
      {"start": 0.2, "end": 0.4, "word": "is"},
      {"start": 0.4, "end": 0.6, "word": "the"}
    ],
    "segment": [
      {"start": 0.0, "end": 5.2, "segment": "This is the transcribed text."}
    ],
    "char": []
  },
  "timestamp": "2026-02-13T10:30:00.000000"
}
```

### GET /gpu/model-info

Get information about the Parakeet-TDT model and its capabilities.

**Response:**
```json
{
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
    "Character-level timestamps"
  ],
  "license": "CC-BY-4.0"
}
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| audio_url | string (URL) | Yes | - | URL of the audio file to transcribe (WAV or FLAC) |
| timestamps | boolean | No | false | Include word, segment, and character-level timestamps |

## Supported Audio Formats

- **Formats**: WAV, FLAC
- **Sample Rate**: 16kHz (recommended)
- **Channels**: Mono (single channel recommended)
- **Duration**: Up to 24 minutes per request

## Performance Metrics

**Word Error Rate (WER) on Benchmarks:**

| Dataset | WER |
|---------|-----|
| LibriSpeech test-clean | 1.69% |
| LibriSpeech test-other | 3.19% |
| GigaSpeech | 9.74% |
| Earnings-22 | 11.15% |
| AMI | 11.16% |

**Average WER**: 6.05%

## Deployment

```bash
flash build
flash deploy new production
flash deploy send production
```

## Cost Estimates

- Workers scale to 0 when idle (no charges)
- Pay only for GPU time during transcription
- First request after idle: ~30-60s (cold start for model loading)
- Subsequent requests: ~1-3s for short audio clips
- GPU: RTX 4090 (24GB VRAM) or similar

## Use Cases

- **Podcast Transcription**: Convert podcast episodes to searchable text
- **Meeting Notes**: Transcribe recorded meetings with timestamps
- **Caption Generation**: Create accurate captions for video content
- **Voice Commands**: Process voice commands with low latency
- **Call Analytics**: Transcribe customer support calls for analysis

## Common Issues

- **Cold start delay**: First request after idle takes 30-60s to load the NeMo model. Use `flash run --auto-provision` during development.
- **Out of memory**: The model requires 8GB+ VRAM. Ensure `GpuGroup.ADA_24` or similar is configured.
- **Invalid audio format**: Only WAV and FLAC formats are supported. Convert other formats (MP3, M4A) to WAV before uploading.
- **Audio too long**: Maximum 24 minutes per request. Split longer audio files into chunks.
- **Low quality transcription**: Ensure audio is 16kHz mono for best results. Background noise and multiple speakers may reduce accuracy.

## Advanced Features

### Timestamp Analysis

The model provides three levels of timestamps:

1. **Word-level**: Start/end times for each word
2. **Segment-level**: Start/end times for sentence segments
3. **Character-level**: Start/end times for individual characters

Use these for:
- Creating precise subtitles
- Analyzing speech patterns
- Synchronizing transcripts with video
- Building interactive transcripts

### Example: Processing Timestamps

```python
import requests

response = requests.post(
    "http://localhost:8888/gpu/transcribe",
    json={
        "audio_url": "https://example.com/audio.wav",
        "timestamps": True
    }
)

result = response.json()

# Print word-level timestamps
for word_info in result["timestamps"]["word"]:
    print(f"{word_info['start']:.2f}s - {word_info['end']:.2f}s: {word_info['word']}")

# Print segment-level timestamps
for segment_info in result["timestamps"]["segment"]:
    print(f"{segment_info['start']:.2f}s - {segment_info['end']:.2f}s: {segment_info['segment']}")
```

## Model Details

**Architecture**: FastConformer with Token-and-Duration Transducer (TDT) decoder

**Key Features**:
- Trained with full attention for long-form audio
- Efficient inference with RTFx of 3380
- Supports commercial and non-commercial use (CC-BY-4.0 license)
- Optimized for English transcription
- Accurate on various domains (audiobooks, podcasts, meetings, earnings calls)

## Error Handling

The API returns detailed error messages:

**Invalid audio URL:**
```json
{
  "status": "error",
  "error": "audio_url is required",
  "timestamp": "2026-02-13T10:30:00.000000"
}
```

**Processing failure:**
```json
{
  "status": "error",
  "error": "Failed to download audio: 404 Not Found",
  "timestamp": "2026-02-13T10:30:00.000000"
}
```

## References

- [Parakeet-TDT-0.6B-v2 Model Card](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2)
- [NVIDIA NeMo Toolkit](https://github.com/NVIDIA/NeMo)
- [Flash Documentation](https://docs.runpod.io)
- [Model Demo Space](https://huggingface.co/spaces/nvidia/parakeet-tdt-0.6b-v2)
