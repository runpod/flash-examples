# Code Review Agent with Kimi-K2

PR diff code reviewer powered by [Kimi-K2-Instruct](https://huggingface.co/moonshotai/Kimi-K2-Instruct) running on Runpod serverless GPUs via vLLM.

## Overview

This example demonstrates a two-worker architecture for self-hosted LLM inference:

- **GPU worker** (queue-based): Hosts Kimi-K2-Instruct via vLLM on 8xH100 GPUs with W4A16 quantization
- **CPU worker** (load-balanced): Validates diffs, constructs prompts, and formats review output as JSON or markdown

## What You'll Learn

- Self-hosting a 1T parameter MoE model with vLLM and quantization
- Cross-worker orchestration: CPU LB routes dispatching to GPU QB endpoints
- Health check patterns for large models with long cold starts
- Multiple output formats from the same pipeline (JSON + markdown)
- Multi-GPU provisioning with `gpu_count=8`

## Quick Start

### Prerequisites

- Python 3.10+
- Runpod API key ([get one here](https://docs.runpod.io/get-started/api-keys))

### GPU Requirements

| Config | Model | VRAM | Context Limit |
|--------|-------|------|---------------|
| **8xH100 80GB** (primary) | `RedHatAI/Kimi-K2-Instruct-quantized.w4a16` | ~500GB + KV cache | 8192 tokens |
| 8xH200 141GB | `moonshotai/Kimi-K2-Instruct` with FP8 | ~1TB | ~16K tokens |

Disk: ~600GB free for model weights and vLLM cache.

### Setup

```bash
cd 02_ml_inference/02_code_review_agent
uv sync
uv run flash login
```

### Run

```bash
uv run flash run
```

First run downloads the model (~500GB) and takes 30-60 minutes. Subsequent starts load from disk cache in several minutes. Server starts at http://localhost:8888

### Check Model Status

The GPU worker takes minutes to load. Poll the health endpoint before sending reviews:

```bash
curl http://localhost:8888/review/health
```

Response when loading:
```json
{"orchestrator": "ready", "gpu_worker": "loading", "status": "loading"}
```

Response when ready:
```json
{"orchestrator": "ready", "gpu_worker": "ready", "status": "ready"}
```

### Submit a Review (JSON)

```bash
curl -X POST http://localhost:8888/review/json \
  -H "Content-Type: application/json" \
  -d "{\"diff\": \"$(cat sample_diffs/security_bug.diff)\"}"
```

Response:
```json
{
  "summary": "Changes introduce SQL injection and XSS vulnerabilities.",
  "comments": [
    {
      "file": "src/auth.py",
      "line": 15,
      "severity": "critical",
      "category": "security",
      "issue": "SQL query built with string concatenation using user input",
      "suggestion": "Use parameterized queries: db.execute('SELECT * FROM users WHERE id = ?', (user_id,))"
    }
  ],
  "stats": {"critical": 2, "warning": 0, "suggestion": 0, "nitpick": 0}
}
```

### Submit a Review (Markdown)

```bash
curl -X POST http://localhost:8888/review/markdown \
  -H "Content-Type: application/json" \
  -d "{\"diff\": \"$(cat sample_diffs/style_issues.diff)\"}"
```

Returns a formatted markdown report.

## Architecture

```
User → POST /review/json
         ↓
CPU Worker (LB)          GPU Worker (QB)
  validate diff            vLLM engine
  build prompt    →await→  Kimi-K2-Instruct
  parse response  ←return← generated text
  format output
         ↓
User ← JSON or Markdown
```

## Limitations

- **Max diff size: 20KB** (~5-6K tokens). Larger diffs exceed the 8192 token context window. Split large PRs into per-file reviews.
- **Cold start: several minutes** after the worker scales to zero. Use `idle_timeout=600` (10 min) to reduce cold starts during active development.
- **First download: 30-60 minutes** for the ~500GB model weights.
- **No streaming**: vLLM generates the full response before returning.

## Cost Estimates

- Workers scale to 0 when idle (no charges)
- Pay only for GPU time during inference
- 8xH100 is a premium configuration -- consider reviewing in batches

## Swapping GPU Tiers

To use 8xH200 with FP8 quantization (more headroom, higher context), edit `gpu_worker.py`:

```python
# change GpuType and add quantization
@Endpoint(
    name="02_02_kimi_k2_gpu",
    gpu=GpuType.NVIDIA_H200,
    gpu_count=8,
    ...
)

# in _get_engine(), change model and add quantization param
_state["engine"] = LLM(
    model="moonshotai/Kimi-K2-Instruct",
    quantization="fp8",
    max_model_len=16384,
    ...
)
```

## References

- [Kimi-K2-Instruct Model Card](https://huggingface.co/moonshotai/Kimi-K2-Instruct)
- [RedHatAI W4A16 Quantization](https://huggingface.co/RedHatAI/Kimi-K2-Instruct-quantized.w4a16)
- [Running Kimi-K2 on Runpod](https://www.runpod.io/blog/guide-to-moonshotais-kimi-k2-on-runpod)
- [vLLM Kimi-K2 Recipe](https://docs.vllm.ai/projects/recipes/en/latest/moonshotai/Kimi-K2.html)
- [Flash Documentation](https://docs.runpod.io)
