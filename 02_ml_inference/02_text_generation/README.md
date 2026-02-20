# Text Generation with vLLM (Qwen)

Serve a chat-style text generation worker with vLLM on Runpod Flash GPUs.

## What You'll Learn

- Configuring a GPU worker with `LiveServerless`
- Serving a vLLM-backed model with `@remote`
- Caching model initialization to avoid repeated cold loads
- Calling a `@remote` class method from a worker function

## Quick Start

### Prerequisites

- Python 3.10+
- Runpod API key

### Setup

```bash
cd 02_ml_inference/02_text_generation
pip install -r requirements.txt
cp .env.example .env
# Add RUNPOD_API_KEY to .env
```

### Run

```bash
flash run
```

Server starts at http://localhost:8888
Visit http://localhost:8888/docs for interactive docs.

## Common Issues

- Cold start latency on first request is expected when worker is scaled to zero.
- If you hit GPU memory errors, reduce `max_model_len` or use a larger GPU group.

## References

- https://docs.runpod.io/flash
- https://docs.vllm.ai
