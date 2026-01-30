# 02 - ML Inference

Deploy machine learning models as production-ready APIs. Learn how to serve LLMs, diffusion models, embeddings, and multimodal models on Runpod's serverless infrastructure.

## Examples

### 01_text_generation

LLM chat inference API (serverless GPU) using Hugging Face `transformers.pipeline`.

**What you'll learn:**

- Loading a gated Llama model with `HF_TOKEN` (Hugging Face auth)
- Serving a simple chat endpoint (`POST /01_text_generation/gpu/llm`)

**Models covered:**

- `meta-llama/Llama-3.2-1B-Instruct`

### 02*image_generation *(coming soon)\_

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

### 03*embeddings *(coming soon)\_

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

### 04*multimodal *(coming soon)\_

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
