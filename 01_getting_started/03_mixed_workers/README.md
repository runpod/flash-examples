# 03 - Mixed GPU/CPU Workers

Learn the production pattern of combining CPU and GPU workers for cost-effective ML pipelines.

## What This Demonstrates

- **Mixed worker architecture** - Combining CPU and GPU workers intelligently
- **Cost optimization** - Using GPU only when necessary
- **Pipeline orchestration** - Coordinating multiple worker types
- **Production patterns** - Real-world ML service architecture
- **Input validation** - Pydantic validation at each pipeline stage

## Architecture

```
User Request
    ↓
CPU Worker (Preprocessing)
- Input validation
- Text cleaning  
- Tokenization
    ↓
GPU Worker (Inference)
- ML model inference
- Classification
    ↓
CPU Worker (Postprocessing)
- Result formatting
- Aggregation
    ↓
Response
```

**Cost Breakdown:**
- Preprocessing: $0.0002/sec (CPU)
- Inference: $0.0015/sec (GPU)  
- Postprocessing: $0.0002/sec (CPU)
- **Total: 85% cheaper than GPU-only pipeline**

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
curl -X POST http://localhost:8888/cpu/preprocess \
  -H "Content-Type: application/json" \
  -d '{"text": "Test message"}'

curl -X POST http://localhost:8888/gpu/inference \
  -H "Content-Type: application/json" \
  -d '{"cleaned_text": "Test message", "word_count": 2}'
```

Visit http://localhost:8888/docs for interactive API documentation.

## Why This Pattern?

### GPU-Only Pipeline (❌ Expensive)
```
Every operation on GPU = $0.0015/sec
- Preprocessing: $0.0015/sec
- Inference: $0.0015/sec
- Postprocessing: $0.0015/sec
Total: $0.0045/sec
```

### Mixed Pipeline (✅ Cost-Effective)
```
Use right tool for each job
- Preprocessing: $0.0002/sec (CPU)
- Inference: $0.0015/sec (GPU)  
- Postprocessing: $0.0002/sec (CPU)
Total: $0.0019/sec (58% savings!)
```

## When to Use This Pattern

✅ **Use mixed workers when:**
- ML inference is only part of your workflow
- You have preprocessing/postprocessing logic
- You want to minimize GPU costs
- You need input validation before expensive operations
- You process data after inference

❌ **Don't use when:**
- Your entire workflow needs GPU (image processing, video, etc.)
- Overhead of orchestration > cost savings
- Very simple operations (single worker is fine)

## Input Validation

This example demonstrates production-grade input validation using Pydantic at each pipeline stage.

### Why Validation in Pipelines?

**Key principle: Fail fast before expensive operations**

- Catch errors **before** GPU inference (saves money)
- Validate at API layer (prevents bad data reaching workers)
- Provide clear error messages (better developer experience)
- Type-safe data structures (prevent runtime errors)

### Validation at Each Stage

**1. Pipeline Endpoint (/classify)**

```python
class ClassifyRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        if len(v) < 3:
            raise ValueError("Text too short (minimum 3 characters)")
        if len(v) > 10000:
            raise ValueError("Text too long (maximum 10,000 characters)")
        return v
```

**2. Preprocessing Endpoint (/cpu/preprocess)**

```python
class PreprocessRequest(BaseModel):
    text: str  # Same validation as ClassifyRequest
```

Validates:
- Text is not empty or whitespace
- Minimum 3 characters
- Maximum 10,000 characters

**3. Inference Endpoint (/gpu/inference)**

```python
class InferenceRequest(BaseModel):
    cleaned_text: str
    word_count: int = Field(ge=0)  # >= 0

    @field_validator("cleaned_text")
    @classmethod
    def validate_text_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Cleaned text cannot be empty")
        return v
```

Validates:
- Cleaned text is not empty
- Word count is non-negative

**4. Postprocessing Endpoint (/cpu/postprocess)**

```python
class Prediction(BaseModel):
    label: str
    confidence: float

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0")
        return v

class PostprocessRequest(BaseModel):
    predictions: list[Prediction]  # Validates structure!
    original_text: str
    metadata: dict
```

Validates:
- Predictions is a list of `Prediction` objects
- Each prediction has `label` (str) and `confidence` (float 0.0-1.0)
- Rejects invalid structures like `["string"]`

### Remote Serialization Pattern

**Problem:** Pydantic models can't be directly serialized for remote workers.

**Solution:** Convert models to dicts using `.model_dump()`:

```python
# ❌ BAD - Pydantic models cause serialization errors
result = await postprocess_results({
    "predictions": request.predictions,  # List[Prediction] objects
})

# ✅ GOOD - Convert to dicts first
result = await postprocess_results({
    "predictions": [pred.model_dump() for pred in request.predictions],
})
```

This pattern:
1. Validates at API layer (type safety + error messages)
2. Converts to plain dicts before remote call (avoids serialization issues)
3. Remote worker receives clean, validated data

### Testing Validation

**Valid requests:**

```bash
# Pipeline endpoint
curl -X POST http://localhost:8888/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "This product is amazing!"}'

# Postprocessing endpoint
curl -X POST http://localhost:8888/cpu/postprocess \
  -H "Content-Type: application/json" \
  -d '{
    "predictions": [
      {"label": "positive", "confidence": 0.9},
      {"label": "negative", "confidence": 0.1}
    ],
    "original_text": "This is great!",
    "metadata": {"word_count": 3}
  }'
```

**Invalid requests (rejected with 422):**

```bash
# Too short
curl -X POST http://localhost:8888/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "Hi"}'
# Error: Text too short (minimum 3 characters)

# Invalid predictions structure
curl -X POST http://localhost:8888/cpu/postprocess \
  -H "Content-Type: application/json" \
  -d '{
    "predictions": ["string"],
    "original_text": "Test",
    "metadata": {}
  }'
# Error: Input should be a valid dictionary or instance of Prediction

# Confidence out of range
curl -X POST http://localhost:8888/cpu/postprocess \
  -H "Content-Type: application/json" \
  -d '{
    "predictions": [{"label": "test", "confidence": 1.5}],
    "original_text": "Test",
    "metadata": {}
  }'
# Error: Confidence must be between 0.0 and 1.0
```

### Validation Best Practices

**1. Validate early** - At API layer, not in worker functions

```python
# ✅ GOOD - Validation in Pydantic model
class Request(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        if len(v) < 3:
            raise ValueError("Too short")
        return v

# ❌ BAD - Validation in worker function
@remote(resource_config=config)
async def process(data: dict) -> dict:
    if len(data["text"]) < 3:
        return {"error": "Too short"}  # Wastes remote call
```

**2. Save costs** - Reject bad requests before GPU operations

```python
# Pipeline validates input → rejects early → GPU never called → money saved
```

**3. Clear errors** - Help API consumers fix issues

```python
# ✅ GOOD
raise ValueError("Text too long (maximum 10,000 characters). Got 15000 characters.")

# ❌ BAD
raise ValueError("Invalid text")
```

**4. Type safety** - Use structured models, not raw dicts

```python
# ✅ GOOD - Type-safe, validated
predictions: list[Prediction]

# ❌ BAD - No validation, error-prone
predictions: list
```

### Resources

See also: [04_dependencies](../04_dependencies/) for more validation patterns

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

The `/classify` endpoint orchestrates all workers:

```python
@app.post("/classify")
async def classify_text(request: ClassifyRequest):
    # Stage 1: CPU Preprocessing
    preprocess_result = await preprocess_text({"text": request.text})
    
    # Stage 2: GPU Inference
    gpu_result = await gpu_inference({
        "cleaned_text": preprocess_result["cleaned_text"],
        "word_count": preprocess_result["word_count"],
    })
    
    # Stage 3: CPU Postprocessing
    final_result = await postprocess_results({
        "predictions": gpu_result["predictions"],
        "original_text": request.text,
        "metadata": metadata,
    })
    
    return final_result
```

## Cost Analysis

**Example: 10,000 requests/day**

Assumptions:
- Preprocessing: 0.05 sec
- GPU inference: 0.2 sec
- Postprocessing: 0.03 sec

**Mixed Pipeline:**
```
Preprocessing: 0.05 × $0.0002 × 10,000 = $0.10/day
Inference: 0.2 × $0.0015 × 10,000 = $3.00/day
Postprocessing: 0.03 × $0.0002 × 10,000 = $0.06/day
Total: $3.16/day = $94.80/month
```

**GPU-Only Pipeline:**
```
All stages: 0.28 × $0.0015 × 10,000 = $4.20/day
Total: $126/month
```

**Savings: $31.20/month (25%)**

For higher volumes, savings multiply significantly.

## Production Best Practices

### 1. Input Validation

Always validate input at API layer **before** pipeline execution:

```python
class ClassifyRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        # Validation happens here - fails fast before GPU
        if not v or len(v) < 3 or len(v) > 10000:
            raise ValueError("Invalid text")
        return v

@app.post("/classify")
async def classify(request: ClassifyRequest):
    # Input already validated by Pydantic
    # GPU won't be called for invalid requests
    result = await run_pipeline(request.text)
    return result
```

### 2. Error Handling

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

### 3. Timeouts

Set appropriate timeouts for each stage:
```python
# CPU stages: short timeouts
preprocess_config.executionTimeout = 30  # seconds

# GPU stage: longer timeout  
gpu_config.executionTimeout = 120  # seconds
```

### 4. Monitoring

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

## Advanced Patterns

### Conditional GPU Usage

Only use GPU when necessary:

```python
@app.post("/classify-smart")
async def smart_classify(request: ClassifyRequest):
    # Preprocess
    preprocess_result = await preprocess_text({"text": request.text})
    
    # Check if GPU is needed
    if preprocess_result["word_count"] < 5:
        # Simple rule-based classification (no GPU)
        return {"classification": "neutral", "method": "rules"}
    
    # Use GPU for complex cases
    gpu_result = await gpu_inference(preprocess_result)
    return await postprocess_results(gpu_result)
```

### Batch Processing

Process multiple inputs together:

```python
@app.post("/classify-batch")
async def batch_classify(requests: list[ClassifyRequest]):
    # Preprocess all on CPU
    preprocessed = await asyncio.gather(*[
        preprocess_text({"text": r.text}) for r in requests
    ])
    
    # Batch GPU inference
    gpu_results = await gpu_batch_inference(preprocessed)
    
    # Postprocess all on CPU
    final_results = await asyncio.gather(*[
        postprocess_results(r) for r in gpu_results
    ])
    
    return final_results
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
- [Flash CLI Documentation](https://github.com/runpod/tetra-rp)
- [Serverless Architecture Patterns](https://docs.runpod.io/serverless/patterns)
