# RunPod Public Endpoints

Call RunPod serverless endpoints from Flash workers using the RunPod Python SDK and raw HTTP. Demonstrates building pipelines that orchestrate multiple serverless endpoints.

## Overview

RunPod serverless endpoints are deployed AI services accessible via API. This example shows how to:

1. **Call endpoints** from Flash workers using the `runpod` SDK
2. **Poll async jobs** for long-running inference tasks
3. **Use webhooks** for completion notifications
4. **Chain endpoints** into GPU-accelerated pipelines
5. **Batch requests** for concurrent processing

This works with any RunPod endpoint: your own (deployed via `flash deploy`), community endpoints, or RunPod's official public endpoints.

## What You'll Learn

- Using the `runpod` Python SDK to call serverless endpoints
- Synchronous vs asynchronous endpoint invocation
- Job status polling and webhook patterns
- Building pipelines that combine local GPU processing with remote endpoints
- Concurrent batch processing across endpoints
- Raw HTTP API calls without the SDK

## Quick Start

### Prerequisites

- Python 3.10+
- RunPod API key ([get one here](https://docs.runpod.io/get-started/api-keys))
- A deployed RunPod endpoint ID (from `flash deploy` or the RunPod console)

### Setup

```bash
cd 03_advanced_workers/03_public_endpoints
cp .env.example .env
# Add your RUNPOD_API_KEY to .env
```

### Deploy an Endpoint to Call

If you don't have an endpoint yet, deploy one from another example:

```bash
# Deploy the vLLM example as a target endpoint
cd ../../02_ml_inference/02_vllm
flash deploy

# Note the endpoint ID from the deploy output
# Use it as endpoint_id in the requests below
```

### Run

```bash
flash run
```

Server starts at http://localhost:8888. Visit http://localhost:8888/docs for interactive API documentation.

### Test Endpoints

**Synchronous call:**
```bash
curl -X POST http://localhost:8888/cpu_worker/run_sync \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint_id": "YOUR_ENDPOINT_ID",
    "prompt": "What is serverless computing?",
    "max_tokens": 128,
    "mode": "sync"
  }'
```

**Asynchronous call (fire-and-forget):**
```bash
curl -X POST http://localhost:8888/cpu_worker/run_sync \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint_id": "YOUR_ENDPOINT_ID",
    "prompt": "Write a poem about GPUs.",
    "mode": "async"
  }'
```

**Check async job status:**
```bash
curl -X POST http://localhost:8888/cpu_worker/run_sync \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint_id": "YOUR_ENDPOINT_ID",
    "job_id": "JOB_ID_FROM_ASYNC_CALL"
  }'
```

**GPU pipeline (preprocess + endpoint):**
```bash
curl -X POST http://localhost:8888/gpu_worker/run_sync \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint_id": "YOUR_ENDPOINT_ID",
    "text": "RunPod provides serverless GPU computing."
  }'
```

**Batch concurrent calls:**
```bash
curl -X POST http://localhost:8888/gpu_worker/run_sync \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint_id": "YOUR_ENDPOINT_ID",
    "prompts": ["What is RunPod?", "Explain vLLM.", "What is Flash?"],
    "max_tokens": 64
  }'
```

**Raw HTTP (no SDK):**
```bash
curl -X POST http://localhost:8888/cpu_worker/run_sync \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint_id": "YOUR_ENDPOINT_ID",
    "prompt": "Hello from raw HTTP!",
    "max_tokens": 64
  }'
```

## How It Works

### RunPod Endpoint API

Every RunPod serverless endpoint exposes these REST endpoints:

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/v2/{endpoint_id}/run` | Submit async job, returns job_id |
| POST | `/v2/{endpoint_id}/runsync` | Submit sync job, blocks until done |
| GET | `/v2/{endpoint_id}/status/{job_id}` | Check job status |
| POST | `/v2/{endpoint_id}/cancel/{job_id}` | Cancel a running job |

### SDK vs Raw HTTP

**RunPod SDK** (recommended):
```python
import runpod
runpod.api_key = "your_key"
endpoint = runpod.Endpoint("endpoint_id")

# Sync
result = endpoint.run_sync({"input": {...}}, timeout=120)

# Async
job = endpoint.run({"input": {...}})
status = endpoint.status(job.job_id)
```

**Raw HTTP**:
```python
import httpx
response = await client.post(
    f"https://api.runpod.ai/v2/{endpoint_id}/runsync",
    json={"input": {...}},
    headers={"Authorization": f"Bearer {api_key}"},
)
```

### Pipeline Architecture

```
Client Request
    │
    ├─ Flash Worker (CPU or GPU)
    │   ├─ Local preprocessing (GPU-accelerated)
    │   ├─ Call RunPod Endpoint A (e.g., LLM)
    │   ├─ Call RunPod Endpoint B (e.g., image gen)
    │   └─ Combine results
    │
    └─ Response
```

## CPU Worker Functions

| Function | Description |
|----------|-------------|
| `call_llm_endpoint` | Sync/async calls to any RunPod endpoint |
| `check_job_status` | Poll async job status |
| `call_endpoint_with_webhook` | Submit with webhook callback |
| `call_endpoint_raw` | Raw HTTP without SDK |

## GPU Worker Functions

| Function | Description |
|----------|-------------|
| `gpu_pipeline_with_endpoint` | GPU preprocess + endpoint call |
| `batch_endpoint_calls` | Concurrent multi-prompt batch |

## Deployment

```bash
flash build
flash deploy
```

After deployment, your Flash workers run on RunPod and can call other RunPod endpoints with minimal latency (intra-datacenter communication).

## Cost Estimates

- CPU workers: ~$0.02/hr (lightweight orchestration)
- GPU workers: ~$0.44/hr (RTX 4090 for preprocessing)
- Target endpoint costs depend on the endpoint's GPU and usage
- Workers scale to 0 when idle

## Common Issues

- **RUNPOD_API_KEY not set**: Ensure the key is in your `.env` file or environment.
- **Endpoint not found (404)**: Verify the endpoint_id. Get it from `flash deploy` output or the [RunPod Console](https://www.runpod.io/console/serverless).
- **Timeout on sync calls**: Long-running models may exceed the default timeout. Use async mode with polling instead.
- **Rate limiting**: RunPod may throttle requests. Implement exponential backoff for production batch processing.

## Project Structure

```
03_public_endpoints/
├── cpu_worker.py        # SDK calls, async jobs, webhooks, raw HTTP
├── gpu_worker.py        # GPU pipeline + batch endpoint calls
├── pyproject.toml       # Project metadata
└── README.md            # This file
```

## Next Steps

- Deploy a vLLM endpoint with [02_ml_inference/02_vllm](../../02_ml_inference/02_vllm/) to use as a target
- See [03_advanced_workers/02_docker_images](../02_docker_images/) for custom Docker image deployment
- See [05_data_workflows/01_network_volumes](../../05_data_workflows/01_network_volumes/) for shared storage between workers

## References

- [RunPod Python SDK](https://github.com/runpod/runpod-python)
- [RunPod Serverless API](https://docs.runpod.io/serverless/endpoints/job-operations)
- [RunPod Public Endpoints](https://www.runpod.io/console/explore)
- [Flash Documentation](https://docs.runpod.io)
