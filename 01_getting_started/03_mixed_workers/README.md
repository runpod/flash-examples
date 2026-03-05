# 03 - Mixed GPU/CPU Workers

Learn the production pattern of combining CPU and GPU workers for cost-effective ML pipelines.

## What This Demonstrates

- **Mixed worker architecture** - Combining CPU and GPU workers intelligently
- **Cost optimization** - Using GPU only when necessary
- **Pipeline orchestration** - Coordinating multiple worker types via a load-balanced endpoint
- **Production patterns** - Real-world ML service architecture

## Architecture

```
User Request
    |
CPU Worker (Preprocessing)
- Text normalization
- Text cleaning
- Tokenization
    |
GPU Worker (Inference)
- ML model inference
- Classification
    |
CPU Worker (Postprocessing)
- Result formatting
- Aggregation
    |
Response
```

**Cost Breakdown:**
- Preprocessing: $0.0002/sec (CPU)
- Inference: $0.0015/sec (GPU)
- Postprocessing: $0.0002/sec (CPU)
- **More cost-effective than GPU-only pipeline**

## Quick Start

**Prerequisites**: Complete the [repository setup](../../README.md#quick-start) first (clone, `make dev`, set API key).

### Run This Example

```bash
cd 01_getting_started/03_mixed_workers
flash run
```

### Alternative: Standalone Setup

If you haven't run the repository-wide setup:

```bash
# Install dependencies
uv sync

# Authenticate
uv run flash login
# Or create .env file with RUNPOD_API_KEY=your_api_key_here

# Run
uv run flash run
```

Server starts at http://localhost:8888

## Test the Pipeline

```bash
# Complete pipeline (recommended)
curl -X POST http://localhost:8888/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "This product is amazing! I love it!"}'

# Individual stages
curl -X POST http://localhost:8888/cpu_worker/runsync \
  -H "Content-Type: application/json" \
  -d '{"text": "Test message"}'

curl -X POST http://localhost:8888/gpu_worker/runsync \
  -H "Content-Type: application/json" \
  -d '{"cleaned_text": "Test message", "word_count": 2}'
```

Visit http://localhost:8888/docs for interactive API documentation.

### Full CLI Documentation

For complete CLI usage including deployment, environment management, and troubleshooting:
- **[CLI Reference](../../CLI-REFERENCE.md)** - All commands and options
- **[Getting Started Guide](../../docs/cli/getting-started.md)** - Step-by-step tutorial
- **[Workflows](../../docs/cli/workflows.md)** - Common development patterns

## Why This Pattern?

### GPU-Only Pipeline (Expensive)
```
Every operation on GPU = $0.0015/sec
- Preprocessing: $0.0015/sec
- Inference: $0.0015/sec
- Postprocessing: $0.0015/sec
Total: $0.0045/sec
```

### Mixed Pipeline (Cost-Effective)
```
Use right tool for each job
- Preprocessing: $0.0002/sec (CPU)
- Inference: $0.0015/sec (GPU)
- Postprocessing: $0.0002/sec (CPU)
Total: $0.0019/sec
```

## When to Use This Pattern

**Use mixed workers when:**
- ML inference is only part of your workflow
- You have preprocessing/postprocessing logic
- You want to minimize GPU costs
- You need input validation before expensive operations
- You process data after inference

**Don't use when:**
- Your entire workflow needs GPU (image processing, video, etc.)
- Overhead of orchestration > cost savings
- Very simple operations (single worker is fine)

## Worker Configurations

### CPU Preprocessing Worker
```python
@Endpoint(
    name="preprocess_worker",
    cpu=CpuInstanceType.CPU3G_2_8,  # 2 vCPU, 8GB
    workers=(0, 10),
    idle_timeout=3,
)
async def preprocess_text(input_data: dict) -> dict: ...
```

**Cost:** ~$0.0002/sec
**Best for:** Validation, cleaning, tokenization

### GPU Inference Worker
```python
@Endpoint(
    name="inference_worker",
    gpu=GpuGroup.ADA_24,  # RTX 4090
    workers=(0, 3),
    idle_timeout=5,
    dependencies=["torch"],
)
async def gpu_inference(input_data: dict) -> dict: ...
```

**Cost:** ~$0.0015/sec
**Best for:** ML model inference only

### CPU Postprocessing Worker
```python
@Endpoint(
    name="postprocess_worker",
    cpu=CpuInstanceType.CPU3G_2_8,  # 2 vCPU, 8GB
    workers=(0, 10),
    idle_timeout=3,
)
async def postprocess_results(input_data: dict) -> dict: ...
```

**Cost:** ~$0.0002/sec
**Best for:** Formatting, aggregation, logging

## Pipeline Orchestration

The `/classify` load-balanced endpoint orchestrates all workers:

```python
from cpu_worker import postprocess_results, preprocess_text
from gpu_worker import gpu_inference
from runpod_flash import Endpoint

pipeline = Endpoint(name="classify_pipeline", cpu="cpu3c-1-2", workers=(1, 3))

@pipeline.post("/classify")
async def classify(text: str) -> dict:
    """Complete ML pipeline: CPU preprocess -> GPU inference -> CPU postprocess."""
    preprocess_result = await preprocess_text({"text": text})

    gpu_result = await gpu_inference(
        {
            "cleaned_text": preprocess_result["cleaned_text"],
            "word_count": preprocess_result["word_count"],
        }
    )

    return await postprocess_results(
        {
            "predictions": gpu_result["predictions"],
            "original_text": text,
            "metadata": {
                "word_count": preprocess_result["word_count"],
                "sentence_count": preprocess_result["sentence_count"],
                "model": gpu_result["model_info"],
            },
        }
    )
```

## Cost Analysis

**Example: 10,000 requests/day**

Assumptions:
- Preprocessing: 0.05 sec
- GPU inference: 0.2 sec
- Postprocessing: 0.03 sec

**Mixed Pipeline:**
```
Preprocessing: 0.05 x $0.0002 x 10,000 = $0.10/day
Inference: 0.2 x $0.0015 x 10,000 = $3.00/day
Postprocessing: 0.03 x $0.0002 x 10,000 = $0.06/day
Total: $3.16/day = $94.80/month
```

**GPU-Only Pipeline:**
```
All stages: 0.28 x $0.0015 x 10,000 = $4.20/day
Total: $126/month
```

**Savings: $31.20/month**

For higher volumes, savings multiply significantly.

## Production Best Practices

### 1. Error Handling

```python
try:
    preprocess_result = await preprocess_text(data)
    gpu_result = await gpu_inference(preprocess_result)
    final_result = await postprocess_results(gpu_result)
    return final_result
except Exception as e:
    logger.error(f"Pipeline failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

### 2. Timeouts

Set appropriate timeouts for each stage via `execution_timeout_ms`:
```python
# CPU stages: short timeouts
@Endpoint(name="preprocess", cpu="cpu3c-1-2", execution_timeout_ms=30000)

# GPU stage: longer timeout
@Endpoint(name="inference", gpu=GpuGroup.ADA_24, execution_timeout_ms=120000)
```

### 3. Monitoring

Track costs per stage:
```python
logger.info(f"Stage costs - Prep: ${prep_cost}, GPU: ${gpu_cost}, Post: ${post_cost}")
```

## Deployment

```bash
# Build application
flash build

# Create environment
flash deploy new production

# Deploy
flash deploy send production
```

## Troubleshooting

### Pipeline Failing at GPU Stage

Check GPU worker logs:
```bash
flash logs production --worker inference_worker
```

### High Costs

Review worker usage:
- Are CPU workers scaling down?
- Is GPU worker idle timeout appropriate?
- Can you cache preprocessing results?

### Slow Performance

- Increase CPU worker max count for preprocessing
- Check if GPU cold start is the issue (set `workers=(1, 3)` for always-warm)
- Consider caching preprocessed data

## Next Steps

- **04_dependencies** - Manage Python/system dependencies
- **02_ml_inference** - Deploy real ML models
- **04_scaling_performance** - Production optimization

## Resources

- [Runpod Cost Calculator](https://www.runpod.io/console/serverless/pricing)
- [Flash CLI Documentation](https://github.com/runpod/runpod-flash)
- [Serverless Architecture Patterns](https://docs.runpod.io/serverless/patterns)
