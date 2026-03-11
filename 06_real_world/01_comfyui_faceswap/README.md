# ComfyUI Character Generation with Face Swapping

SDXL character generation pipeline with optional face swapping, running ComfyUI as a library on RunPod Flash. Ported from a Modal deployment -- uses programmatic ComfyUI node access instead of server mode.

## What it does

1. **Text-only mode**: Prompt → SDXL generation → base64 PNG image
2. **Face swap mode**: Prompt + reference face URL → SDXL generation → IPAdapter face transfer → InstantID refinement → DetailerForEach inpainting → base64 PNG image

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  ComfyUICharacter (class-based @remote worker)          │
│                                                         │
│  __init__:                                              │
│    1. Install ComfyUI + custom nodes (cached on volume) │
│    2. Download ~19GB of models (cached on volume)       │
│    3. Initialize ComfyUI node system                    │
│    4. Load all models to GPU (~30s)                     │
│                                                         │
│  generate:                                              │
│    1. Encode prompts (CLIPTextEncode)                   │
│    2. [Optional] Apply IPAdapter FaceID + Advanced      │
│    3. Sample (KSampler, dpmpp_2m_sde, karras)           │
│    4. Decode (VAEDecode)                                │
│    5. [Optional] Face detection → InstantID → Detailer  │
│    6. Return base64 PNG                                 │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────┐
│  NetworkVolume       │
│  100GB               │
│  - ComfyUI install   │
│  - Custom nodes      │
│  - Model weights     │
└─────────────────────┘
```

## Models (~19GB total)

| Model | Purpose | Size |
|-------|---------|------|
| Juggernaut-XI (SDXL) | Base image generation | 6.5GB |
| CLIP-ViT-H-14 | Vision encoding for IPAdapter | 3.9GB |
| IPAdapter FaceID Plus v2 | Face identity transfer | 1.6GB |
| IPAdapter FaceID LoRA | LoRA for FaceID model | 370MB |
| IPAdapter Plus Face | Additional face conditioning | 1.6GB |
| InstantID ControlNet | Face structure control | 2.5GB |
| InstantID Adapter | Identity preservation | 1.7GB |
| SAM ViT-B | Segment Anything (face masking) | 375MB |
| YOLOv8m Face | Face detection | 50MB |
| InsightFace (buffalo_l + antelopev2) | Face analysis | 600MB |

## API

### `POST /generate`

**Request body:**
```json
{
  "prompt": "a young woman with red hair in a medieval castle",
  "negative_prompt": "blurry, deformed",
  "reference_image_url": "https://example.com/face.jpg",
  "width": 832,
  "height": 1216,
  "steps": 35,
  "cfg": 2.0,
  "seed": 42
}
```

Only `prompt` is required. Omit `reference_image_url` for text-only generation.

**Response:**
```json
{
  "status": "success",
  "image_base64": "<base64-encoded PNG>",
  "parameters": {
    "prompt": "...",
    "width": 832,
    "height": 1216,
    "steps": 35,
    "cfg": 2.0,
    "seed": 42,
    "face_swap": true
  },
  "duration_seconds": 25.3
}
```

## Quick Start

### Local development

```bash
cd 06_real_world/01_comfyui_character
flash run
# Visit http://localhost:8888/docs for interactive API docs
```

### Deploy to RunPod

```bash
flash deploy
```

### Test

```bash
# Text-only generation
curl -X POST http://localhost:8888/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a portrait of a knight in shining armor"}'

# Face swap generation
curl -X POST http://localhost:8888/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "a young woman as a medieval warrior",
    "reference_image_url": "https://example.com/face.jpg"
  }'
```

## Resource Configuration

- **GPU**: A100 80GB (SDXL + IPAdapter + InstantID need ~40GB peak VRAM)
- **Network Volume**: 100GB (models persist across cold starts)
- **Idle Timeout**: 5 minutes (scale to zero when inactive)
- **Max Workers**: 3

## Cold Start Behavior

1. **First ever start** (~10-15 min): Clones ComfyUI + custom nodes, downloads ~20GB of models
2. **Subsequent cold starts** (~2-3 min): Installs pip requirements, initializes nodes, loads models to GPU
3. **Warm requests** (~5-30s): Direct inference (text-only ~5s, face swap ~27s)

## Custom Nodes

| Node Package | Purpose |
|-------------|---------|
| [ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack) | Face detection, SEGS, DetailerForEach |
| [comfyui-impact-subpack](https://github.com/ltdrdata/comfyui-impact-subpack) | Impact Pack submodules |
| [ComfyUI_IPAdapter_plus](https://github.com/cubiq/ComfyUI_IPAdapter_plus) | IPAdapter FaceID, Advanced |
| [ComfyUI_InstantID](https://github.com/cubiq/ComfyUI_InstantID) | InstantID face preservation |

## Cost Estimate

| Scenario | Duration | GPU Cost (A100 80GB) |
|----------|----------|---------------------|
| Cold start (first) | ~15 min | ~$0.50 |
| Cold start (cached) | ~30s | ~$0.02 |
| Text-only generation | ~5-8s | ~$0.003 |
| Face swap generation | ~25-30s | ~$0.015 |

*Costs are approximate based on RunPod A100 80GB pricing.*
