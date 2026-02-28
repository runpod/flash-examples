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

### 02_text_to_image
Text-to-image generation API.

**What you'll learn:**
- Building text-to-image endpoints with `@remote` GPU workers
- Running Diffusers pipelines on serverless GPUs
- Returning generated images as base64 payloads
- Tuning quality/speed tradeoffs with inference steps

**Models covered:**
- FLUX.1-schnell

### 03_image_to_image
Prompt-guided image transformation API with Stable Diffusion img2img.

**What you'll learn:**
- Building image-to-image endpoints with `@remote` GPU workers
- Sending base64-encoded images through FastAPI
- Controlling style transfer intensity with `strength` and `guidance_scale`
- Returning transformed images from serverless workers

**Models covered:**
- Stable Diffusion v1.5 img2img pipeline

### 04_text_to_video
Prompt-guided text-to-video generation API.

**What you'll learn:**
- Building text-to-video endpoints with `@remote` GPU workers
- Returning generated clips as portable GIF output
- Tuning temporal quality with frames, inference steps, and guidance
- Managing higher-memory multimodal inference workloads

**Models covered:**
- damo-vilab/text-to-video-ms-1.7b

### 05_image_to_video
Image animation API with Stable Video Diffusion.

**What you'll learn:**
- Turning still images into short animated clips on serverless GPUs
- Sending and validating base64-encoded image inputs
- Controlling animation dynamics with motion and noise settings
- Returning generated clips with preview frames

**Models covered:**
- stabilityai/stable-video-diffusion-img2vid-xt

### 06_embeddings _(coming soon)_
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

### 07_multimodal _(coming soon)_
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
