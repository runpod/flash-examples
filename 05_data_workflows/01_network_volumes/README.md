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

**Generate an image (GPU worker):**
```bash
curl -X POST http://localhost:8888/gpu_worker/run_sync \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a sunset over mountains"}'
```

**List generated images (CPU worker):**
```bash
curl http://localhost:8888/images
```

**Get a specific image (CPU worker):**
```bash
curl http://localhost:8888/images/sd_generated_20240101_120000.png
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
├── gpu_worker.py        # Stable Diffusion worker with @remote
├── cpu_worker.py        # List and serve images with @remote
├── requirements.txt
└── README.md
```

## API Endpoints

### POST /gpu_worker/run_sync

GPU worker (QB, class-based `@remote`). Generates an image and saves it to the shared volume.

**Request**:
```json
{ "prompt": "a sunset over mountains" }
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

### GET /images

CPU worker (LB, explicit path). Lists all generated images on the shared volume.

**Response**:
```json
{ "status": "success", "images": ["sd_generated_20240101_120000.png"] }
```

### GET /images/{file_name}

CPU worker (LB, explicit path). Returns metadata and base64-encoded content for a single image.

## Notes

- The network volume is defined inline in each worker file and attached to both workers.
- Stable Diffusion weights are cached in the volume so cold starts are faster after the first run.

## Deployment

```bash
flash build
flash deploy new production
flash deploy send production
```
