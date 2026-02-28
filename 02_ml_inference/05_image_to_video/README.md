# Image-to-Video with Stable Video Diffusion

Serverless image-to-video API built with Runpod Flash and Stable Video Diffusion.

## What this example does

- Accepts an input image as base64
- Animates the image into a short clip with `StableVideoDiffusionPipeline`
- Returns the generated video as base64-encoded GIF

## Quick Start

```bash
cd 02_ml_inference/05_image_to_video
pip install -r requirements.txt
cp .env.example .env
# Add RUNPOD_API_KEY in .env
flash run
```

Open docs at `http://localhost:8888/docs`.

## Endpoint

### POST `/gpu/animate`

Request body:

```json
{
  "image_base64": "<base64-encoded-image-or-omit-for-default-poddy.jpg>",
  "motion_bucket_id": 127,
  "noise_aug_strength": 0.02,
  "num_frames": 12,
  "num_steps": 18,
  "fps": 7,
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
  "model": "stabilityai/stable-video-diffusion-img2vid-xt",
  "input_width": 1920,
  "input_height": 1080,
  "render_width": 1024,
  "render_height": 576,
  "num_frames": 16,
  "timestamp": "2026-02-15T12:34:56.789123"
}
```

## Local Demo Script

```bash
python demo.py
# or explicitly:
python demo.py input.png output.gif
```

## Notes

- First request can take longer because the worker and model need to warm up.
- Input images are resized to `1024x576` before animation for predictable memory usage.
- This example returns GIF output for portability and simple local testing.
- GIF encoding is capped at 25 FPS; higher requested values are clamped and response `fps` reflects the encoded output.
- If `image_base64` is omitted, the endpoint uses `poddy.jpg` as the default input image.
- Quality is intentionally baseline for fast, reliable, and lower-cost demo runs; this is a starter configuration, not a max-quality preset.
- The default parameters are tuned for reliability on 24GB GPUs; increase frames/steps gradually if you want higher quality.
