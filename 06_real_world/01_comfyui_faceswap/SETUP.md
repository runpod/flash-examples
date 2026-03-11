# ComfyUI Faceswap — Verified Setup Guide

> Verified on RunPod pod with RTX 5090 on 2026-03-10. Full init + text-only generation: **success**.

## Base Image

```
runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04
```

- PyTorch 2.8.0 with CUDA 12.8 (RTX 5090 compatible)
- Python 3.11.11
- SSH support built-in (handles `PUBLIC_KEY` env var automatically)
- `runpod` SDK NOT included — must `pip install runpod`
- Clean pip environment — no conflicting insightface/onnxruntime

## Setup Steps (Verified Order)

### 1. System Dependencies

```bash
apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libxcb1 libx11-6 libxext6 libsm6
```

Required for OpenCV / image processing used by insightface and ComfyUI nodes.

### 2. ComfyUI

```bash
git clone https://github.com/comfyanonymous/ComfyUI.git /comfyui
cd /comfyui
pip install -r requirements.txt
```

### 3. Custom Nodes

```bash
cd /comfyui/custom_nodes
git clone https://github.com/ltdrdata/ComfyUI-Impact-Pack
git clone https://github.com/ltdrdata/comfyui-impact-subpack
git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus
git clone https://github.com/cubiq/ComfyUI_InstantID
```

Install their dependencies:

```bash
cd ComfyUI-Impact-Pack && pip install -r requirements.txt && python install.py
cd ../comfyui-impact-subpack && [ -f requirements.txt ] && pip install -r requirements.txt || true
cd ../ComfyUI_IPAdapter_plus && [ -f requirements.txt ] && pip install -r requirements.txt || true
cd ../ComfyUI_InstantID && [ -f requirements.txt ] && pip install -r requirements.txt || true
```

**Note:** ComfyUI_InstantID pulls in `insightface==0.7.3` and both `onnxruntime` + `onnxruntime-gpu`. The CPU onnxruntime shadows the GPU version. This is fixed in step 4.

### 4. Fix onnxruntime + Pin insightface (CRITICAL)

```bash
pip uninstall -y onnxruntime onnxruntime-gpu
pip install insightface==0.7.3 onnxruntime-gpu
```

**This must happen LAST.** The CPU `onnxruntime` package shadows `onnxruntime-gpu`'s CUDAExecutionProvider. You must uninstall BOTH, then install only `onnxruntime-gpu`.

### 5. Install RunPod SDK

```bash
pip install runpod
```

### 6. Validate

```python
python -c "
import insightface
assert insightface.__version__ == '0.7.3'
import onnxruntime
provs = onnxruntime.get_available_providers()
assert 'CUDAExecutionProvider' in provs
print(f'OK: insightface 0.7.3, providers: {provs}')
"
```

Expected output:
```
OK: insightface 0.7.3, providers: ['TensorrtExecutionProvider', 'CUDAExecutionProvider', 'CPUExecutionProvider']
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `HF_TOKEN` | Yes | HuggingFace token for gated models (Juggernaut XI) |
| `HF_HOME` | Recommended | Set to `/runpod-volume/hf_cache` to avoid filling container disk with HF download cache |
| `PUBLIC_KEY` | No | SSH public key(s) — handled by base image |

## Disk Requirements

| Location | Size | Contents |
|----------|------|----------|
| Container disk | 100 GB recommended | ComfyUI + deps (~8GB), HF cache overflow |
| Network volume | 30+ GB | Models (~22GB), HF cache, sentinel file |

**Important:** The HuggingFace download cache goes to `/root/.cache/huggingface` by default. With ~19GB of models, this fills a 30GB container disk. Set `HF_HOME=/runpod-volume/hf_cache` to redirect to the network volume.

## Models (~22GB total)

Downloaded to `/runpod-volume/comfyui/ComfyUI/models/` on first startup. Cached via sentinel file at `/runpod-volume/comfyui/.install_complete`.

| Model | Size | Path |
|-------|------|------|
| CyberRealistic XL v7 | ~6.5GB | `checkpoints/cyberrealistic_xl_v7.safetensors` |
| Juggernaut XI | ~6.5GB | `checkpoints/Juggernaut-XI-byRunDiffusion.safetensors` |
| CLIP Vision ViT-H | ~3.6GB | `clip_vision/CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors` |
| IPAdapter FaceID v2 SDXL | ~850MB | `ipadapter/ip-adapter-faceid-plusv2_sdxl.bin` |
| IPAdapter Plus Face SDXL | ~850MB | `ipadapter/ip-adapter-plus-face_sdxl_vit-h.safetensors` |
| IPAdapter FaceID LoRA | ~400MB | `loras/ip-adapter-faceid-plusv2_sdxl_lora.safetensors` |
| InstantID ControlNet | ~2.5GB | `controlnet/diffusion_pytorch_model_instantid.safetensors` |
| InstantID IP-Adapter | ~1.7GB | `instantid/ip-adapter.bin` |
| SAM ViT-B | ~375MB | `sams/sam_vit_b_01ec64.pth` |
| InsightFace buffalo_l | ~300MB | `insightface/models/buffalo_l/*.onnx` |
| InsightFace antelopev2 | ~300MB | `insightface/models/antelopev2/*.onnx` |
| YOLOv8m face | ~50MB | `ultralytics/bbox/face_yolov8m.pt` |

## Architecture

```
handler.py                    # RunPod serverless entry point
  ├── Imports ComfyUICharacter at module scope (top of file)
  ├── Initializes worker at startup (before runpod.serverless.start)
  │   └── Model loading happens during container startup phase (no execution timeout)
  └── handler(job) calls worker.generate(job["input"])

comfyui_character.py          # Main worker class
  └── ComfyUICharacter.__init__()
      ├── Phase 1: Download models to network volume (cached via sentinel)
      ├── Phase 2: Initialize ComfyUI node system + custom nodes
      └── Phase 3: Load all models to GPU
```

## Key Design Decisions

### Why not `worker-comfyui:5.7.1-base`?
- Ships insightface 0.2.1 (incompatible API, different path layout than 0.7.x)
- Ships CPU-only onnxruntime that shadows onnxruntime-gpu
- Every fix attempt broke something else

### Why init at startup, not on first request?
- Model loading takes ~7 minutes (cold)
- RunPod execution timeout is 600s per job
- Container startup has a separate, much longer timeout (10-30 min)

### Why `pip uninstall` before `pip install`?
- ComfyUI_InstantID's requirements.txt pulls in both `onnxruntime` and `onnxruntime-gpu`
- When both are installed, Python imports the CPU version first
- `onnxruntime.get_available_providers()` returns only `['AzureExecutionProvider', 'CPUExecutionProvider']`
- Uninstalling both and reinstalling only `onnxruntime-gpu` gives `CUDAExecutionProvider`

### Why `HF_HOME` on the volume?
- HuggingFace caches downloaded files in `~/.cache/huggingface/` before copying to final destination
- With ~19GB of models, this fills a 30GB container disk
- Redirecting to the network volume avoids disk space issues

## Startup Timeline (RTX 5090, cold)

| Phase | Duration | Notes |
|-------|----------|-------|
| Model download | ~5 min | Only on first run (cached by sentinel) |
| ComfyUI init | ~3 sec | Node system + custom nodes |
| Load checkpoints | ~5 min | CyberRealistic + Juggernaut to GPU |
| Load other models | ~2 min | CLIP, LoRA, ControlNet, IPAdapter, InsightFace, SAM |
| **Total cold start** | **~7 min** | With models already on volume |
| **Total first-ever** | **~12 min** | Including model download |

## Warm Generation Performance

| Mode | Duration | Notes |
|------|----------|-------|
| Text-only (no face swap) | ~5-10s expected | 20 steps, 832x1216 |
| With face swap | ~15-30s expected | Full pipeline with DetailerForEach |

*Note: The 291s observed in testing includes cold model loading during init within the same process. Warm requests after init will be much faster.*

## Known Warnings (Safe to Ignore)

1. **`WARNING: You need pytorch with cu130 or higher to use optimized CUDA operations`** — ComfyUI's comfy_kitchen wants CUDA 13.0, but everything works fine with 12.8
2. **`torchvision==0.22 is incompatible with torch==2.8`** — Minor version mismatch, doesn't affect our workflow
3. **`RuntimeWarning: coroutine 'init_extra_nodes' was never awaited`** — Latest ComfyUI made this async; our sync call still works
4. **`ModelPatcher.__del__ ... AttributeError: 'NoneType' object`** — Python cleanup order issue at process exit, not a real error

## Deploying to Serverless

1. Push code to `TimPietruskyRunPod/comfyui-faceswap`
2. RunPod builds the Docker image from `Dockerfile`
3. Deploy to endpoint `bblp777ptfep17` with template `u2fkrfnlz9`
4. Set env vars: `HF_TOKEN`, `HF_HOME=/runpod-volume/hf_cache`
5. Network volume `cx07vsgfs2` mounted at `/runpod-volume` (EUR-NO-1)
