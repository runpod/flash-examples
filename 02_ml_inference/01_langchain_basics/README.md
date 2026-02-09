# Langchain Basics - Flash GPU Local LLM Inference

Learn how to integrate Langchain with Flash workers for cost-effective local LLM inference. This example demonstrates building GPU-based LLM services using vLLM for self-hosted inference with open-source models like Mistral-7B.

## Overview

This example shows you how to:
- Integrate Langchain with Flash's `@remote` decorator
- Use GPU workers for local LLM inference with vLLM (no external API needed)
- Build production-ready LLM-powered endpoints with self-hosted models
- Handle model loading and GPU memory management
- Parse structured output from LLM responses
- Implement proper error handling and logging

The architecture uses Flash's GPU workers to run vLLM-optimized inference on open-source models, providing a cost-effective pattern for LLM-powered services that scale to zero when idle and avoid external API fees.

## What You'll Learn

- **Langchain Integration**: How to use Langchain with Flash's remote workers
- **GPU Workers**: Cost-effective local LLM inference without external APIs
- **vLLM Optimization**: High-throughput inference engine for open-source models
- **Model Loading**: Efficient GPU memory management and model caching
- **Prompt Engineering**: Creating templates for summarization, analysis, and transformation
- **Structured Output**: Parsing JSON responses from local LLM inference
- **Environment Management**: Configuring GPU workers and model parameters
- **Error Handling**: Production patterns for robust local inference
- **Cost Optimization**: Scaling to zero and eliminating API fees

## Quick Start

### Prerequisites

- Python 3.10+
- Flash SDK installed
- GPU with at least 24GB VRAM (for Mistral-7B, local testing)
- Runpod account and API key (for cloud deployment)
- HuggingFace token (optional, only for gated models like Llama)

### Installation

```bash
# Navigate to this example
cd 02_ml_inference/01_langchain_basics

# Set up environment (optional)
cp .env.example .env

# No API keys needed for local inference! Models download automatically
# RUNPOD_API_KEY=... (optional, only for cloud deployment)
```

### Local Development

```bash
# Run the example locally
flash run

# First request will download Mistral-7B model (~5GB) - takes 3-5 minutes
# Server starts at http://localhost:8888
# API documentation available at http://localhost:8888/docs
```

Visit the Swagger UI to test endpoints interactively. The first request will load the model (5-10 minutes), subsequent requests will be fast (1-2 seconds).

## API Endpoints

### POST /gpu/summarize

Summarize long text into key points using local LLM inference with Mistral-7B.

**Request**:
```bash
curl -X POST http://localhost:8888/gpu/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Artificial intelligence is transforming industries worldwide. Machine learning enables computers to learn from data without explicit programming. Deep learning networks process images and text with remarkable accuracy. Applications range from healthcare diagnostics to autonomous vehicles.",
    "max_length": 50
  }'
```

**Response** (200 OK):
```json
{
  "status": "success",
  "summary": "AI transforms industries through machine learning and deep learning. Applications include healthcare diagnostics and autonomous vehicles.",
  "word_count": 18,
  "model": "mistralai/Mistral-7B-Instruct-v0.3",
  "processing_time_ms": 1850
}
```

**Parameters**:
- `text` (required): Text to summarize (10-10000 characters)
- `max_length` (optional): Maximum summary length in words (50-500, default: 150)

**Error Responses**:
- `400 Bad Request`: Invalid input (empty text, invalid length)
- `500 Internal Server Error`: API failure (check logs)

---

### POST /gpu/analyze-sentiment

Analyze text sentiment with structured output including topics and action items using local LLM inference.

**Request**:
```bash
curl -X POST http://localhost:8888/gpu/analyze-sentiment \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This product exceeded my expectations! The customer service team was incredibly helpful and responsive. Highly recommend!"
  }'
```

**Response** (200 OK):
```json
{
  "status": "success",
  "sentiment": {
    "label": "positive",
    "confidence": 0.92,
    "reasoning": "Strong positive language with superlatives and recommendation",
    "topics": ["product_quality", "customer_service"],
    "action_required": false
  },
  "model": "mistralai/Mistral-7B-Instruct-v0.3",
  "processing_time_ms": 1620
}
```

**Parameters**:
- `text` (required): Text to analyze (5-5000 characters)

**Sentiment Labels**:
- `positive`: Favorable sentiment with confidence 0-1
- `negative`: Unfavorable sentiment
- `neutral`: No strong sentiment

**Topics** (examples):
- `product_quality`: Comments about product features or quality
- `customer_service`: Comments about service or support
- `pricing`: Comments about cost or value
- `delivery`: Comments about shipping or availability

---

### POST /gpu/transform

Transform text using custom instructions with local LLM inference. Demonstrates dynamic prompting for flexible text operations.

**Request Examples**:

*Translate to Spanish*:
```bash
curl -X POST http://localhost:8888/gpu/transform \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you today?",
    "instruction": "Translate this to Spanish and keep it formal",
    "temperature": 0.3
  }'
```

*Rephrase for clarity*:
```bash
curl -X POST http://localhost:8888/gpu/transform \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The quick brown fox jumps over the lazy dog because it wanted to escape",
    "instruction": "Rephrase this more clearly and concisely",
    "temperature": 0.5
  }'
```

*Convert to bullet points*:
```bash
curl -X POST http://localhost:8888/gpu/transform \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Machine learning is a subset of AI that focuses on learning from data. Deep learning uses neural networks with multiple layers. These techniques enable computers to recognize patterns without explicit programming.",
    "instruction": "Convert this into a bulleted list of key points",
    "temperature": 0.7
  }'
```

**Response** (200 OK):
```json
{
  "status": "success",
  "original_text": "Hello, how are you today?",
  "transformed_text": "Hola, ¿cómo está usted hoy?",
  "instruction_used": "Translate this to Spanish and keep it formal",
  "temperature": 0.3,
  "model": "mistralai/Mistral-7B-Instruct-v0.3",
  "processing_time_ms": 1650
}
```

**Parameters**:
- `text` (required): Text to transform (5-5000 characters)
- `instruction` (required): Transformation instruction (10-500 characters)
- `temperature` (optional): Creativity level 0-2 (default: 0.7)
  - `0-0.3`: Deterministic, focused output
  - `0.4-0.9`: Balanced creativity and consistency
  - `1.0-2.0`: Creative, varied output

**Error Responses**:
- `400 Bad Request`: Missing or invalid parameters
- `500 Internal Server Error`: Processing failed

## Architecture

```
User Request
    ↓
FastAPI Endpoint (validation)
    ↓
GPU Worker Function (@remote)
    ↓
vLLM Inference Engine
    ↓
Mistral-7B-Instruct Model (local)
    ↓
Response (with metadata)
```

### Component Details

**FastAPI Endpoints**: Handle HTTP requests, validate input with Pydantic models, manage error handling

**GPU Workers**: vLLM inference runs on Runpod GPU instances (RTX 4090), scales to zero when idle

**vLLM**: High-performance inference engine optimized for throughput, supports advanced features like paged attention

**Langchain**: Manages prompt templates, structured output parsing, and integration patterns

**Mistral-7B-Instruct**: Open-source 7B parameter model with excellent instruction-following capabilities

## Configuration

### Environment Variables

Create a `.env` file from `.env.example` and configure:

```bash
# Optional - HuggingFace (only for gated models like Llama-2)
HF_TOKEN=hf_...        # Get from https://huggingface.co/settings/tokens

# Optional - Runpod (for deployment)
RUNPOD_API_KEY=...     # Get from https://www.runpod.io/console/user/settings

# Optional - Local development
FLASH_HOST=localhost
FLASH_PORT=8888
LOG_LEVEL=INFO
```

**Note**: No API keys required for Mistral-7B! Model weights are open-source.

### Cost Optimization Configuration

In `gpu_worker.py`, the GPU config is optimized for cost:

```python
gpu_config = LiveServerless(
    name="02_01_langchain_gpu",
    gpus=[GpuGroup.ADA_24],  # RTX 4090 with 24GB VRAM
    workersMin=0,            # Scale to ZERO when idle
    workersMax=3,            # Allow parallel requests
    idleTimeout=3,           # Minutes before scaling down
)
```

**Why these settings?**
- `workersMin=0`: Scales to zero, you only pay when processing
- `workersMax=3`: Supports concurrent requests without overprovisioning
- `idleTimeout=3`: Quickly scales down after each request
- `GpuGroup.ADA_24`: RTX 4090 provides 24GB VRAM for efficient inference

## Cost Estimates

### Development/Testing

- **GPU Workers**: Free (scale to zero between requests)
- **Model Download**: One-time (~5GB, included with first request)
- **Total**: Minimal cost for development

### Production (10,000 requests/month)

#### GPU Worker Costs
- **Instance Type**: RTX 4090 (24GB VRAM, ~$0.38/hour when active)
- **Average Request Time**: 2-3 seconds (after model loaded)
- **Monthly Estimate**: 10,000 requests × 2.5 sec ÷ 3600 = ~7 hours active = ~$2.65/month
- **Scaling Benefit**: Scale to zero between requests, no idle charges

#### No External API Costs
- **Mistral-7B**: Open-source, no API fees
- **Monthly API Cost**: $0 (zero)

**Total Monthly Cost: ~$2-3/month** (10,000 requests)

**Cost Reduction**: 85-90% cheaper than OpenAI-based solution ($13 → $2-3)

### Cost Comparison

| Architecture | Monthly (10K req) | Per Request | Breakeven |
|--------------|------------------|------------|----------|
| CPU + OpenAI API | ~$13 | $0.0013 | Baseline |
| GPU + vLLM Local | ~$2.65 | $0.00027 | Day 1 (always cheaper) |
| **Savings** | **~$10/month** | **80% less** | **Immediate** |

### Cost Optimization Tips

1. **Set `workersMin=0`**: Only pay when processing
2. **Use efficient models**: Mistral-7B vs Mistral-Large saves 3-5x
3. **Batch requests**: Process multiple items per worker activation
4. **Monitor GPU usage**: Check Runpod dashboard for optimization
5. **Scale horizontally**: Add workers only during peak demand
6. **Cache model in worker**: Model loads once per worker lifetime

## Testing

### Interactive Testing (Recommended)

1. Start the server:
   ```bash
   flash run
   ```

2. Open Swagger UI:
   ```
   http://localhost:8888/docs
   ```

3. Try each endpoint with the built-in interface

### Command-Line Testing

Test summarization:
```bash
curl -X POST http://localhost:8888/gpu/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Machine learning enables computers to learn from data. Neural networks process information through interconnected layers. Deep learning achieves remarkable performance on complex tasks like image recognition and language processing.",
    "max_length": 50
  }' | jq .
```

Test sentiment analysis:
```bash
curl -X POST http://localhost:8888/gpu/analyze-sentiment \
  -H "Content-Type: application/json" \
  -d '{"text": "Great product! Highly satisfied with the purchase and would recommend it."}' | jq .
```

Test text transformation:
```bash
curl -X POST http://localhost:8888/gpu/transform \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The quick brown fox jumped over the fence",
    "instruction": "Make this more dramatic and add action verbs",
    "temperature": 0.8
  }' | jq .
```

Test validation errors:
```bash
# Empty text should return 400
curl -X POST http://localhost:8888/gpu/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": ""}' | jq .

# Expected: 400 with "Text cannot be empty" message
```

### Python Testing

```python
import httpx
import asyncio

async def test_api():
    async with httpx.AsyncClient() as client:
        # Test summarize
        response = await client.post(
            "http://localhost:8888/gpu/summarize",
            json={
                "text": "Your long text here...",
                "max_length": 100
            }
        )
        print("Summarize:", response.json())

        # Test sentiment
        response = await client.post(
            "http://localhost:8888/gpu/analyze-sentiment",
            json={"text": "This is great!"}
        )
        print("Sentiment:", response.json())

asyncio.run(test_api())
```

## Deployment to Runpod

### Prerequisites

- Runpod account with API key configured
- Flash SDK installed
- Repository committed to git

### Deploy from Root

```bash
# From repository root
flash deploy 02_ml_inference/01_langchain_basics

# Follow prompts to configure deployment
```

### Post-Deployment

1. Verify endpoints via Runpod dashboard
2. Monitor logs for errors
3. Check OpenAI usage on https://platform.openai.com/account/billing/overview

## Troubleshooting

### Issue: "CUDA out of memory"

**Problem**: GPU doesn't have enough VRAM for the model

**Solution**:
- Mistral-7B requires ~14-16GB VRAM (uses GpuGroup.ADA_24 with 24GB)
- Try smaller models: Mistral-7B is recommended minimum
- Reduce batch size or max_tokens in vLLM config
- Check GPU memory with: `nvidia-smi`

### Issue: "Model download timeout"

**Problem**: First request takes 5-10 minutes to download and load model

**Solution**:
- This is normal! Mistral-7B is ~5GB
- First request will be slow (model download + load)
- Subsequent requests fast (1-2 seconds)
- Monitor progress in logs: `LOG_LEVEL=DEBUG flash run`
- Ensure stable internet connection

### Issue: "Router not discovered by unified app"

**Problem**: Router naming issue

**Solution**: Ensure `gpu_router` is exported in `gpu_worker.py`:
```python
gpu_router = APIRouter()

@gpu_router.post("/summarize")
async def summarize_endpoint(request):
    # ...
```

### Issue: "Import errors: No module named 'vllm'"

**Problem**: Dependencies not installed

**Solution**:
```bash
# Install dependencies
cd 02_ml_inference/01_langchain_basics
uv sync

# Or globally
make consolidate-deps
```

### Issue: "ImportError: cannot import name 'LLM' from vllm"

**Problem**: vLLM version incompatibility

**Solution**:
- Ensure vLLM >=0.2.0 installed
- Update: `pip install --upgrade vllm`
- Check version: `python -c "import vllm; print(vllm.__version__)"`

### Issue: "OutOfMemory during model initialization"

**Problem**: vLLM trying to use more VRAM than available

**Solution**:
- Reduce gpu_memory_utilization (default 0.9)
- Reduce max_model_len in gpu_worker.py
- Use smaller model (Mistral-3.7B if available)

### Issue: "Validation error: Text too long"

**Problem**: Input exceeds character limit

**Solution**:
- Summarize endpoint: Max 10,000 characters
- Sentiment endpoint: Max 5,000 characters
- Transform endpoint: Max 5,000 characters

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
flash run
```

Check logs for:
- vLLM initialization
- Model loading progress
- GPU memory allocation
- Inference timing
- Error details

## Code Structure

```
gpu_worker.py
├── Remote Worker Functions
│   ├── summarize_text()
│   ├── analyze_sentiment()
│   └── transform_text()
├── Pydantic Models
│   ├── SummarizeRequest/Response
│   ├── SentimentRequest/Response
│   └── TransformRequest/Response
└── FastAPI Endpoints
    ├── /gpu/summarize
    ├── /gpu/analyze-sentiment
    └── /gpu/transform

main.py
├── FastAPI Application Setup
├── Health Check Endpoints
└── Router Integration
```

### Key Implementation Details

**@remote Decorator**: Marks functions to run on GPU workers with vLLM
**vLLM Integration**: LLM() initialization with optimized inference parameters
**Langchain Templates**: PromptTemplate for structured prompt engineering
**Pydantic Models**: Validate all inputs and structure outputs
**Error Handling**: Catch and log all exceptions with context
**Async/Await**: All LLM operations use async for performance
**Model Caching**: vLLM model instance cached across requests for efficiency

## Next Steps

After completing this example:

1. **Explore Langchain Chains**: Combine multiple LLM calls for complex workflows
2. **Add Memory**: Implement conversation history with LangChain memory
3. **Build RAG**: Create Retrieval-Augmented Generation with vector databases
4. **Add Caching**: Implement Redis caching for common requests
5. **Stream Responses**: Return real-time LLM token generation
6. **Multi-LLM**: Support different models (GPT-4, Claude, local LLMs)

## Related Examples

- `01_getting_started/02_cpu_worker` - Basic CPU worker pattern
- `02_ml_inference/02_langchain_rag` - Advanced: Retrieval-Augmented Generation

## References

### vLLM Documentation
- [vLLM Docs](https://docs.vllm.ai) - High-throughput LLM inference engine
- [vLLM GitHub](https://github.com/vllm-project/vllm) - Source code and issues
- [vLLM Performance](https://docs.vllm.ai/en/latest/performance.html) - Optimization guide

### Mistral AI
- [Mistral-7B Model](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3) - Model weights on HuggingFace
- [Mistral Docs](https://docs.mistral.ai) - Official documentation
- [Prompt Formatting](https://docs.mistral.ai/capabilities/function_calling/) - Best practices

### Langchain Documentation
- [Langchain Introduction](https://python.langchain.com/docs/get_started/introduction)
- [Langchain Prompts](https://python.langchain.com/docs/modules/model_io/prompts)
- [Langchain Community](https://python.langchain.com/docs/integrations/llms/) - Community integrations

### Flash Documentation
- [Flash Introduction](https://docs.runpod.io)
- [GPU Workers](https://docs.runpod.io) - GPU resource configuration
- [Deployment Guide](https://docs.runpod.io) - Cloud deployment

### FastAPI
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Pydantic Validation](https://docs.pydantic.dev)
- [Async Patterns](https://fastapi.tiangolo.com/async-sql-databases/) - Async best practices

## Support & Issues

If you encounter issues:

1. Check the **Troubleshooting** section above
2. Review server logs: `LOG_LEVEL=DEBUG flash run`
3. Verify API keys are set correctly
4. Check OpenAI API status
5. Review code comments for implementation details

## License

This example is part of the flash-examples repository.
