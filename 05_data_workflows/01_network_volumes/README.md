# 01_network_volumes

Network volume example that shares model cache and generated images between GPU and CPU workers.

## Overview

The GPU worker generates images with Stable Diffusion and writes them to a Runpod network volume. The CPU worker lists or serves those images from the same volume.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env`:

```bash
RUNPOD_API_KEY=your_api_key_here
```

Get your API key from [Runpod Settings](https://www.runpod.io/console/user/settings).

### 3. Run Locally

```bash
flash run
```

Server starts at `http://localhost:8888`

### 4. Test the API

```bash
# Health check
curl http://localhost:8888/ping

# Generate an image on the GPU worker
curl -X POST http://localhost:8888/gpu/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a lighthouse on a cliff at sunrise"}'

# List generated images from the CPU worker
curl http://localhost:8888/cpu/image

# Fetch a single image by filename
curl http://localhost:8888/cpu/image/<file_id> --output image.png
```

Visit `http://localhost:8888/docs` for interactive API documentation.

## What You'll Learn

- How to attach a shared `NetworkVolume` to GPU and CPU workers
- How to use the GPU worker to write to the volume
- How to read and serve files from the CPU worker

## Architecture

- GPU worker: loads Stable Diffusion, caches weights in `/runpod-volume/models`, writes images to `/runpod-volume/generated_images`
- CPU worker: lists images and serves files from `/runpod-volume/generated_images`

## Quick Project Structure

```
01_network_volumes/
├── main.py
├── workers/
│   ├── __init__.py           # Network volume definition
│   ├── gpu/
│   │   ├── __init__.py       # GPU router
│   │   └── endpoint.py       # Stable Diffusion worker
│   └── cpu/
│       ├── __init__.py       # CPU router
│       └── endpoint.py       # List and serve images
├── requirements.txt
└── README.md
```

## API Endpoints

### POST /gpu/generate

**Request**:
```json
{ "prompt": "string" }
```

**Response**:
```json
{
  "prompt": "string",
  "image_path": "string",
  "timestamp": "string",
  "generation_params": {
    "num_inference_steps": 20,
    "guidance_scale": 7.5,
    "width": 512,
    "height": 512
  },
  "message": "Image generated and saved locally!"
}
```

### GET /cpu/image

**Response**:
```json
{ "status": "success", "images": ["file.png"] }
```

### GET /cpu/image/{file_id}

Returns the PNG file as `image/png`.

## Notes

- The network volume is defined in `workers/__init__.py` and attached to both workers.
- Stable Diffusion weights are cached in the volume so cold starts are faster after the first run.

## Deployment

```bash
flash build
flash deploy new production
flash deploy send production
```
