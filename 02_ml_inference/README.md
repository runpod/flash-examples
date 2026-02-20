# 02 - ML Inference

Deploy machine learning models as production-ready APIs. Learn how to serve LLMs, diffusion models, embeddings, and multimodal models on Runpod's serverless infrastructure.

## Examples

### 01_text_to_speech
Text-to-speech API using Qwen3-TTS on serverless GPU workers.

### 02_text_generation
vLLM-based text generation API with a cached Qwen model.

**What you'll learn:**
- Loading and serving LLMs with vLLM
- Prompt templating for chat-style generation
- Worker-level model caching for lower latency
- Input validation and generation controls

**Models covered:**
- Qwen/Qwen2.5-3B-Instruct

### 03_image_generation _(coming soon)_
Stable Diffusion image generation API.

**What you'll learn:**
- Loading Stable Diffusion models
- Optimizing inference with diffusers
- Handling image uploads and downloads
- Model caching strategies

**Models covered:**
- Stable Diffusion 1.5, 2.1, XL
- SDXL Turbo
- ControlNet integration

### 04_embeddings _(coming soon)_
Text embedding API for semantic search and RAG.

**What you'll learn:**
- Serving embedding models
- Batch processing for efficiency
- Integrating with vector databases
- Dimensionality reduction

**Models covered:**
- sentence-transformers
- OpenAI-compatible embeddings
- Multilingual models

### 05_multimodal _(coming soon)_
Vision-language models (CLIP, LLaVA, etc.).

**What you'll learn:**
- Serving vision-language models
- Image+text processing
- Zero-shot classification
- Visual question answering

**Models covered:**
- CLIP
- LLaVA
- BLIP-2

## Architecture Patterns

All examples demonstrate:
- Model loading and caching
- Efficient batching
- Error handling
- Request validation
- Response streaming (where applicable)

## GPU Selection

Examples include GPU recommendations:
- **RTX 4090 (24GB)**: Most consumer models
- **L40/RTX 6000 Ada (48GB)**: Larger models
- **A100 (80GB)**: Largest models, multi-GPU

## Next Steps

After exploring ML inference:
- Learn [03_advanced_workers](../03_advanced_workers/) for optimization
- Study [04_scaling_performance](../04_scaling_performance/) for production
- Build complete apps in [06_real_world](../06_real_world/)
