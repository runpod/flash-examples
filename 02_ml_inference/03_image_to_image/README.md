# Image-to-Image with Stable Diffusion

Serverless image-to-image API built with Runpod Flash and Stable Diffusion v1.5.

## What this example does

- Accepts an input image as base64
- Applies prompt-guided transformation with `StableDiffusionImg2ImgPipeline`
- Returns a transformed image as base64 PNG

## Quick Start

```bash
cd 02_ml_inference/03_image_to_image
pip install -r requirements.txt
cp .env.example .env
# Add RUNPOD_API_KEY in .env
flash run
```

Open docs at `http://localhost:8888/docs`.

## Endpoint

### POST `/gpu/transform`

Request body:

```json
{
  "image_base64": "<base64-encoded-image-or-omit-for-default-poddy.jpg>",
  "prompt": "turn this portrait into a cinematic oil painting",
  "negative_prompt": "blurry, low quality",
  "strength": 0.65,
  "guidance_scale": 7.5,
  "num_steps": 25,
  "seed": 42
}
```

Response:

```json
{
  "status": "success",
  "image_base64": "<base64-encoded-output-image>",
  "model": "runwayml/stable-diffusion-v1-5",
  "prompt": "...",
  "negative_prompt": "...",
  "strength": 0.65,
  "guidance_scale": 7.5,
  "num_steps": 25,
  "seed": 42,
  "timestamp": "2026-02-15T12:34:56.789123"
}
```

## Local Demo Script

Run the demo client against your local endpoint:

```bash
python demo.py "turn this into a watercolor painting" output.png
```

## Notes

- First request can take longer because the worker and model need to warm up.
- Input images are resized to `512x512` before inference for stable memory usage.
- If `image_base64` is omitted, the endpoint uses `poddy.jpg` as the default input image.
- Quality is intentionally baseline for fast, reliable, and lower-cost demo runs; this is a starter configuration, not a max-quality preset.
