# Text-to-Video with Diffusers

Serverless text-to-video API built with Runpod Flash and Diffusers.

## What this example does

- Accepts a text prompt
- Generates a short video clip with a GPU `@remote` worker
- Returns the generated video as base64-encoded GIF

## Quick Start

```bash
cd 02_ml_inference/04_text_to_video
pip install -r requirements.txt
cp .env.example .env
# Add RUNPOD_API_KEY in .env
flash run
```

Open docs at `http://localhost:8888/docs`.

## Endpoint

### POST `/gpu/generate`

Request body:

```json
{
  "prompt": "a cinematic drone shot of snowy mountains at sunrise",
  "negative_prompt": "blurry, noisy, low quality",
  "num_frames": 12,
  "num_steps": 18,
  "guidance_scale": 7.0,
  "fps": 8,
  "width": 512,
  "height": 288,
  "seed": 42
}
```

Response:

```json
{
  "status": "success",
  "video_base64": "<base64-encoded-gif>",
  "video_mime_type": "image/gif",
  "preview_image_base64": "<base64-encoded-png>",
  "preview_image_mime_type": "image/png",
  "model": "damo-vilab/text-to-video-ms-1.7b",
  "prompt": "...",
  "num_frames": 16,
  "fps": 8,
  "timestamp": "2026-02-15T12:34:56.789123"
}
```

## Local Demo Script

```bash
python demo.py "a cinematic drone shot of snowy mountains" output.gif
```

## Notes

- First request can take longer because the worker and model need to warm up.
- This example returns GIF output for portability and simple local testing.
- GIF encoding is capped at 25 FPS; higher requested values are clamped and response `fps` reflects the encoded output.
- Quality is intentionally baseline for fast, reliable, and lower-cost demo runs; this is a starter configuration, not a max-quality preset.
- The default parameters are tuned for reliability on 24GB GPUs; increase frames/steps/resolution gradually if you want higher quality.
