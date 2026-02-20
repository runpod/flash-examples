# 03 - Mixed GPU/CPU Workers

Learn the production pattern of combining CPU and GPU workers for cost-effective ML pipelines.

## What This Demonstrates

- **Mixed worker architecture** - Combining CPU and GPU workers intelligently
- **Cost optimization** - Using GPU only when necessary
- **Pipeline orchestration** - Coordinating multiple worker types
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
pip install -r requirements.txt

# Set API key (choose one):
export RUNPOD_API_KEY=your_api_key_here
# OR create .env file:
echo "RUNPOD_API_KEY=your_api_key_here" > .env

# Run
flash run
```

Server starts at http://localhost:8888

## Test the Pipeline

```bash
# Complete pipeline (recommended)
curl -X POST http://localhost:8888/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "This product is amazing! I love it!"}'

# Individual stages
curl -X POST http://localhost:8888/cpu_worker/run_sync \
  -H "Content-Type: application/json" \
  -d '{"text": "Test message"}'

curl -X POST http://localhost:8888/gpu_worker/run_sync \
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
preprocess_config = CpuLiveServerless(
    name="preprocess_worker",
    instanceIds=[CpuInstanceType.CPU3G_2_8],  # 2 vCPU, 8GB
    workersMin=0,
    workersMax=10,  # High traffic capacity
    idleTimeout=3,   # Quick scale-down
)
```

**Cost:** ~$0.0002/sec
**Best for:** Validation, cleaning, tokenization

### GPU Inference Worker
```python
gpu_config = LiveServerless(
    name="inference_worker",
    gpus=[GpuGroup.ADA_24],  # RTX 4090
    workersMin=0,
    workersMax=3,
    idleTimeout=5,
)
```

**Cost:** ~$0.0015/sec
**Best for:** ML model inference only

### CPU Postprocessing Worker
```python
postprocess_config = CpuLiveServerless(
    name="postprocess_worker",
    instanceIds=[CpuInstanceType.CPU3G_2_8],  # 2 vCPU, 8GB
    workersMin=0,
    workersMax=10,
    idleTimeout=3,
)
```

**Cost:** ~$0.0002/sec
**Best for:** Formatting, aggregation, logging

## Pipeline Orchestration

The `/classify` load-balanced endpoint orchestrates all workers:

```python
@remote(resource_config=pipeline_config, method="POST", path="/classify")
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
    # Stage 1: Preprocess (validation already done)
    preprocess_result = await preprocess_text(data)

    # Stage 2: GPU inference
    gpu_result = await gpu_inference(preprocess_result)

    # Stage 3: Postprocess
    final_result = await postprocess_results(gpu_result)

    return final_result
except Exception as e:
    logger.error(f"Pipeline failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

### 2. Timeouts

Set appropriate timeouts for each stage:
```python
# CPU stages: short timeouts
preprocess_config.executionTimeout = 30  # seconds

# GPU stage: longer timeout
gpu_config.executionTimeout = 120  # seconds
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
- Check if GPU cold start is the issue (set workersMin=1)
- Consider caching preprocessed data

## Next Steps

- **04_dependencies** - Manage Python/system dependencies
- **02_ml_inference** - Deploy real ML models
- **04_scaling_performance** - Production optimization

## Resources

- [Runpod Cost Calculator](https://www.runpod.io/console/serverless/pricing)
- [Flash CLI Documentation](https://github.com/runpod/runpod-flash)
- [Serverless Architecture Patterns](https://docs.runpod.io/serverless/patterns)
