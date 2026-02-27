# Text-to-Image with FLUX.1-schnell

Serverless text-to-image API built with Runpod Flash and FLUX.1-schnell.

## What this example does

- Accepts a text prompt
- Generates an image with a GPU `@remote` worker using FLUX.1-schnell
- Returns the generated image as base64-encoded PNG

## Quick Start

```bash
cd 02_ml_inference/02_text_to_image
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
  "prompt": "a tiny astronaut floating in space, watercolor style",
  "width": 512,
  "height": 512,
  "num_steps": 4,
  "hf_token": ""
}
```

Response:

```json
{
  "status": "success",
  "image_base64": "<base64-encoded-png>",
  "prompt": "...",
  "width": 512,
  "height": 512
}
```

## Local Demo Script

```bash
python demo.py "a cat astronaut on mars"
```

The demo renders the generated image directly in your terminal.

## Notes

- First request can take longer because the worker and model need to warm up.
- FLUX.1-schnell is a fast distilled model (~12GB VRAM) — 4 inference steps produce good results.
- `hf_token` can be passed per-request or set via `HF_TOKEN` env var for gated model access.
- Quality is intentionally baseline for fast, reliable, and lower-cost demo runs; this is a starter configuration, not a max-quality preset.
