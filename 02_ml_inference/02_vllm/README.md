# vLLM Inference with RunPod

Deploy large language models using [vLLM](https://github.com/vllm-project/vllm) on RunPod's serverless infrastructure via Flash. Uses RunPod's official `worker-vllm` Docker image for production-ready LLM serving.

## Overview

vLLM is a high-throughput LLM inference engine with:
- **Continuous batching** for concurrent request handling
- **PagedAttention** for efficient KV cache management
- **OpenAI-compatible API** (`/v1/chat/completions`, `/v1/completions`)
- **Tensor parallelism** for multi-GPU models

This example deploys vLLM using RunPod's pre-built Docker image (`runpod/worker-v1-vllm`), configured entirely through environment variables. No custom Docker image build required.

## What You'll Learn

- Deploying vLLM with `ServerlessEndpoint` and `dockerImage`
- Configuring models via environment variables (MODEL_NAME, MAX_MODEL_LEN, etc.)
- Chat completions (Llama 3.1, Mistral)
- Raw text completions for code generation
- Running multiple models with different configurations

## Quick Start

### Prerequisites

- Python 3.10+
- RunPod API key ([get one here](https://docs.runpod.io/get-started/api-keys))
- HuggingFace token (for gated models like Llama)

### Setup

```bash
cd 02_ml_inference/02_vllm
cp .env.example .env
# Add your RUNPOD_API_KEY and HF_TOKEN to .env
```

### Run

```bash
flash run
```

Server starts at http://localhost:8888. Visit http://localhost:8888/docs for interactive API documentation.

### Test Endpoints

**Chat with Llama 3.1 8B:**
```bash
curl -X POST http://localhost:8888/gpu_worker/run_sync \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is vLLM?"}
    ],
    "max_tokens": 256
  }'
```

**Chat with Mistral 7B:**
```bash
curl -X POST http://localhost:8888/gpu_worker/run_sync \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Explain serverless in 2 sentences."}
    ],
    "max_tokens": 128
  }'
```

**Text completion (code generation):**
```bash
curl -X POST http://localhost:8888/gpu_worker/run_sync \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "def fibonacci(n):",
    "max_tokens": 128,
    "stop": ["\n\n"]
  }'
```

## How It Works

### Architecture

```
Flash CLI (flash run / flash deploy)
    │
    ├─ ServerlessEndpoint config
    │   ├─ dockerImage: runpod/worker-v1-vllm:stable-cuda12.1.0
    │   ├─ env: MODEL_NAME, MAX_MODEL_LEN, DTYPE, ...
    │   └─ gpuIds, workers, idleTimeout
    │
    └─ RunPod Serverless
        └─ vLLM Container
            ├─ Loads model from HuggingFace
            ├─ Starts vLLM engine
            └─ Serves OpenAI-compatible API
```

### Request Flow

1. Client sends request to Flash endpoint
2. Flash routes request to RunPod serverless
3. RunPod starts vLLM container (or reuses warm worker)
4. vLLM processes request with continuous batching
5. Response returned through the chain

## Configuration

### vLLM Environment Variables

Configure the vLLM server via `env` in `ServerlessEndpoint`:

| Variable | Description | Default |
|----------|-------------|---------|
| `MODEL_NAME` | HuggingFace model ID | Required |
| `MAX_MODEL_LEN` | Maximum sequence length | Model default |
| `DTYPE` | Data type (`half`, `bfloat16`, `auto`) | `auto` |
| `GPU_MEMORY_UTILIZATION` | GPU memory fraction (0.0-1.0) | `0.90` |
| `TENSOR_PARALLEL_SIZE` | Number of GPUs for parallelism | `1` |
| `DEFAULT_BATCH_SIZE` | Token streaming batch size | `50` |
| `HF_TOKEN` | HuggingFace token for gated models | - |
| `QUANTIZATION` | Quantization method (`awq`, `gptq`, `squeezellm`) | - |
| `TRUST_REMOTE_CODE` | Allow custom model code | `false` |

### GPU Selection by Model Size

| Model Size | Recommended GPU | `gpuIds` |
|------------|-----------------|----------|
| 7-8B (fp16) | RTX 4090 24GB | `["NVIDIA GeForce RTX 4090"]` |
| 7-8B (quantized) | RTX 4090 24GB | `["NVIDIA GeForce RTX 4090"]` |
| 13B (fp16) | A6000 48GB | `["NVIDIA RTX A6000"]` |
| 34-70B (fp16) | A100 80GB x2 | `["NVIDIA A100 80GB PCIe"]` |
| 70B+ (fp16) | H100 x2-4 | `["NVIDIA H100 80GB HBM3"]` |

### Multi-GPU Configuration

For models that don't fit on a single GPU:

```python
large_model_config = ServerlessEndpoint(
    name="vllm_70b",
    dockerImage="runpod/worker-v1-vllm:stable-cuda12.1.0",
    gpuIds=["NVIDIA A100 80GB PCIe"],
    workersMin=0,
    workersMax=1,
    env={
        "MODEL_NAME": "meta-llama/Llama-3.1-70B-Instruct",
        "TENSOR_PARALLEL_SIZE": "2",
        "MAX_MODEL_LEN": "4096",
        "DTYPE": "half",
        "GPU_MEMORY_UTILIZATION": "0.95",
    },
)
```

## Supported Models

Any HuggingFace model compatible with vLLM works. Popular choices:

| Model | ID | Size | Notes |
|-------|----|------|-------|
| Llama 3.1 8B | `meta-llama/Llama-3.1-8B-Instruct` | 16GB | Requires HF token |
| Llama 3.1 70B | `meta-llama/Llama-3.1-70B-Instruct` | 140GB | Multi-GPU |
| Mistral 7B | `mistralai/Mistral-7B-Instruct-v0.3` | 14GB | Open access |
| Mixtral 8x7B | `mistralai/Mixtral-8x7B-Instruct-v0.1` | 93GB | Multi-GPU |
| Qwen 2.5 7B | `Qwen/Qwen2.5-7B-Instruct` | 14GB | Open access |
| Phi-3 Mini | `microsoft/Phi-3-mini-4k-instruct` | 7.6GB | Small & fast |
| CodeLlama 34B | `codellama/CodeLlama-34b-Instruct-hf` | 68GB | Code generation |

## Deployment

```bash
# Build the application
flash build

# Deploy to RunPod
flash deploy
```

After deployment, Flash creates serverless endpoints for each `ServerlessEndpoint` config. The vLLM container starts automatically when requests arrive.

## Cost Estimates

- Workers scale to 0 when idle (no charges)
- Cold start: 30-90s (model loading depends on size)
- RTX 4090: ~$0.44/hr for 7-8B models
- A100 80GB: ~$1.64/hr for 70B models
- Optimize costs with `idleTimeout` and `workersMin=0`

## Common Issues

- **Cold start latency**: First request takes 30-90s to load the model. Set `workersMin=1` for always-warm endpoints (costs more).
- **Out of memory**: Reduce `MAX_MODEL_LEN` or `GPU_MEMORY_UTILIZATION`. Use quantization (`QUANTIZATION=awq`) for larger models on smaller GPUs.
- **Gated model access denied**: Set `HF_TOKEN` in the `env` config with a valid HuggingFace token that has access to the model.
- **Model not found**: Verify the `MODEL_NAME` matches the exact HuggingFace model ID. Check for typos and case sensitivity.
- **Slow throughput**: Increase `DEFAULT_BATCH_SIZE` and `GPU_MEMORY_UTILIZATION`. Enable tensor parallelism for multi-GPU setups.

## Project Structure

```
02_vllm/
├── gpu_worker.py        # vLLM workers: Llama chat, Mistral chat, text completion
├── pyproject.toml       # Project metadata
└── README.md            # This file
```

## Next Steps

- See [03_advanced_workers/02_docker_images](../../03_advanced_workers/02_docker_images/) for general custom Docker image usage
- See [03_advanced_workers/03_public_endpoints](../../03_advanced_workers/03_public_endpoints/) for calling existing RunPod endpoints
- See [03_advanced_workers/05_load_balancer](../../03_advanced_workers/05_load_balancer/) for low-latency HTTP routing

## References

- [vLLM Documentation](https://docs.vllm.ai/)
- [RunPod vLLM Worker](https://github.com/runpod-workers/worker-vllm)
- [RunPod Serverless](https://docs.runpod.io/serverless/overview)
- [HuggingFace Models](https://huggingface.co/models)
- [Flash Documentation](https://docs.runpod.io)
