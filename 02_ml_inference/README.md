# 02 - ML Inference

Deploy machine learning models as production-ready APIs. Learn how to serve LLMs, diffusion models, embeddings, and multimodal models on Runpod's serverless infrastructure.

## Examples

### 01_text_generation _(coming soon)_
LLM inference API with streaming support.

**What you'll learn:**
- Loading and serving LLMs (Llama, Mistral, etc.)
- Streaming text generation
- Model quantization for efficiency
- Memory management for large models

**Models covered:**
- Llama 3, Llama 3.1, Llama 3.2
- Mistral, Mixtral
- Qwen, Phi, Gemma

### 02_image_generation _(coming soon)_
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

### 03_embeddings _(coming soon)_
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

### 04_multimodal _(coming soon)_
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
