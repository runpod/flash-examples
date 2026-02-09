# Runpod Public API: Text-to-Image Generation

Generate images from text descriptions using Runpod's public text-to-image endpoint. This example demonstrates how to integrate with public serverless endpoints without needing to create custom workers.

## What You'll Learn

- Calling Runpod public endpoints using Flash SDK
- Working with `JobOutput` for async job handling
- Building interactive web UIs for AI generation tasks
- Error handling for API calls
- Job polling and status tracking

## Architecture

```
Browser Form
    ↓
FastAPI Server
    ↓
Flash SDK (Authentication + Polling)
    ↓
Runpod Public API (p-image-t2i)
    ↓
Image Generation
    ↓
Image URL → Browser Display
```

**Key Pattern**: Use `ServerlessEndpoint` to reference public endpoints. Flash SDK handles:
- API authentication
- Job submission
- Automatic polling for completion
- Error handling

## Quick Start

### Prerequisites

- Python 3.10+
- Flash CLI
- Runpod account (public endpoints are available to all users)

### Installation

```bash
cd 02_ml_inference/01_runpod_public_api
flash run
```

Visit `http://localhost:8888` to see the interactive form.

### Test the Unified App

From the repository root:

```bash
make consolidate-deps
flash run
```

Then visit `http://localhost:8888/docs` and navigate to the `02_ml_inference/01_runpod_public_api` section.

## How It Works

### API Calls to Public Endpoint

The example makes direct HTTP calls to Runpod's public endpoint API:

```python
import httpx

# Submit job to public endpoint
submit_response = await client.post(
    "https://api.runpod.io/v2/p-image-t2i/run",
    json={"input": {"prompt": "...", "aspect_ratio": "16:9"}}
)

job_id = submit_response.json()["id"]
```

### Job Polling

After submission, poll for status:

```python
# Check job status
status_response = await client.get(
    f"https://api.runpod.io/v2/p-image-t2i/status/{job_id}"
)

status = status_response.json()

if status["status"] == "COMPLETED":
    image_url = status["output"]["image_url"]
```

### Status Values

- **IN_QUEUE**: Waiting to start processing
- **IN_PROGRESS**: Currently generating image
- **COMPLETED**: Image ready, check `output.image_url`
- **FAILED**: Generation failed, check `output.error`

## API Endpoints

### POST /api/generate

Generate an image from a text description.

**Request**:
```json
{
  "prompt": "A majestic liger standing on a rocky cliff at sunset",
  "aspect_ratio": "16:9",
  "enable_safety_checker": true,
  "seed": 0
}
```

**Response**:
```json
{
  "status": "success",
  "job_id": "abc-123-def",
  "image_url": "https://cdn.runpod.io/...",
  "prompt": "A majestic liger standing on a rocky cliff at sunset",
  "aspect_ratio": "16:9",
  "seed": 0
}
```

**Error Response** (400):
```json
{
  "detail": "Prompt is required and cannot be empty"
}
```

## Deployment

### Deploy to Runpod

```bash
cd 02_ml_inference/01_runpod_public_api
flash build
flash deploy
```

Flash automatically handles:
- Container building
- Endpoint creation
- Public URL generation
- Monitoring and logging

## Configuration

### Environment Variables

Optional settings via `.env`:

```bash
# API Server
FLASH_HOST=localhost
FLASH_PORT=8888
```

No API key needed - Flash SDK handles authentication automatically.

### Input Parameters

- **prompt** (required): Text description, 1-1000 characters
- **aspect_ratio**: Image dimensions (default: "16:9")
  - "16:9" - Wide format
  - "1:1" - Square
  - "9:16" - Tall format
- **enable_safety_checker**: Content filtering (default: true)
- **seed**: Random seed for reproducibility (default: 0)

## Error Handling

### Client Errors (400)

Returned when input validation fails:
- Empty or missing prompt
- Prompt exceeds 1000 characters
- Invalid aspect ratio
- Generation job failed

```python
try:
    result = await generate_image_from_public_endpoint(prompt="")
except ValueError as e:
    # Caught and converted to HTTP 400
    print(f"Validation error: {e}")
```

### Server Errors (500)

Returned for unexpected failures:
- Network issues during job submission
- Timeout waiting for job completion
- Malformed response from public endpoint

```python
try:
    result = await generate_image_from_public_endpoint(...)
except Exception as e:
    # Caught and converted to HTTP 500
    logger.error(f"Unexpected error: {e}")
```

## Troubleshooting

### "Image generation failed" Error

The public endpoint may have encountered an issue:

1. **Invalid prompt**: Check for profanity or unsafe content
2. **Safety checker**: Try disabling if content is flagged
3. **Timeout**: Generation took too long (>2 min), try simpler prompt
4. **Service issue**: Public endpoint may be temporarily unavailable

**Solution**: Retry with a simpler prompt or different seed.

### Image URL Expires

Generated images are stored for 7 days. Links expire after:

```
Expiration = generation_time + 7 days
```

**Solution**: Download image immediately or regenerate if needed.

### No Image URL in Response

Indicates malformed response from public endpoint:

1. Check server logs for error details
2. Verify endpoint is accessible
3. Try again with different parameters

### Application Won't Start

Missing dependencies:

```bash
# Install from pyproject.toml
pip install -e .

# Or use Flash
flash run
```

## Cost Considerations

Using public endpoints incurs charges:
- Per-request pricing based on inference time
- Typical cost: $0.01-0.05 per image
- No setup or base fees

Monitor costs via Runpod dashboard. Budget implications:
- 100 images/day: ~$1-5/day
- 1000 images/day: ~$10-50/day

## Common Use Cases

### Batch Generation

For generating multiple images, iterate:

```python
prompts = [
    "A serene mountain landscape",
    "A bustling city at night",
    "A peaceful forest stream",
]

results = []
for prompt in prompts:
    result = await generate_image_from_public_endpoint(prompt=prompt)
    results.append(result)
```

### Different Aspect Ratios

Generate variations:

```python
for aspect_ratio in ["16:9", "1:1", "9:16"]:
    result = await generate_image_from_public_endpoint(
        prompt="A beautiful sunset",
        aspect_ratio=aspect_ratio,
    )
    print(f"{aspect_ratio}: {result['image_url']}")
```

### Reproducible Results

Use fixed seed:

```python
# First generation
result1 = await generate_image_from_public_endpoint(
    prompt="A liger",
    seed=42,
)

# Same seed produces identical image
result2 = await generate_image_from_public_endpoint(
    prompt="A liger",
    seed=42,
)

# result1['image_url'] == result2['image_url']
```

## Understanding the Code

### Key Files

- **`main.py`**: FastAPI app with HTML form and API endpoints
- **`cpu_worker.py`**: Public endpoint integration with job submission and polling
- **`pyproject.toml`**: Dependencies (httpx for HTTP calls)

### Direct HTTP Calls

This example uses direct HTTP calls via `httpx` to interact with Runpod's public API:

1. **Job Submission**: POST to `/run` endpoint
   - Sends prompt and parameters
   - Returns job ID

2. **Status Polling**: GET to `/status/{job_id}` endpoint
   - Checks job status every 1 second
   - Returns image URL when complete

3. **Error Handling**: Check status field for failures
   - Status "FAILED" indicates error
   - Returns error message in output

### Why Direct HTTP?

- No dependency on SDK features still in development
- Simple, transparent API calls
- Works with public endpoints without authentication
- Easy to debug and understand
- Standard async/await patterns

## Advanced Features

### Custom Error Messages

Extend error handling:

```python
try:
    job_output = await public_endpoint.run(input=input_data)
    if job_output.error:
        if "safety" in job_output.error.lower():
            raise ValueError("Content flagged by safety checker")
        else:
            raise ValueError(f"Generation error: {job_output.error}")
except Exception as e:
    # Return user-friendly error
    return {"status": "error", "message": str(e)}
```

### Job ID Tracking

Store job IDs for monitoring:

```python
results = []
for prompt in prompts:
    result = await generate_image_from_public_endpoint(prompt=prompt)
    results.append({
        "prompt": prompt,
        "job_id": result["job_id"],
        "image_url": result["image_url"],
        "timestamp": datetime.now(),
    })

# Later, retrieve by job_id for logging/auditing
```

### Status Dashboard

Track generation metrics:

```python
# Count successful/failed generations
success_count = sum(1 for r in results if r.get("image_url"))
failure_count = len(results) - success_count
avg_generation_time = sum(r["generation_time"]) / len(results)
```

## Next Steps

- Add image gallery/storage (S3, database)
- Build batch generation API
- Add webhook notifications for completion
- Integrate other public endpoints (see Runpod docs)
- Add user authentication
- Track generation costs per user

## References

- [Runpod Public Endpoints Documentation](https://docs.runpod.io/)
- [Flash SDK Reference](https://docs.runpod.io/sdks/flash-sdk)
- [Text-to-Image Endpoint Docs](https://docs.runpod.io/endpoints/text-to-image)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Validation](https://docs.pydantic.dev/)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review server logs: `FLASH_LOG_LEVEL=DEBUG flash run`
3. See Runpod documentation for endpoint-specific issues
4. Open issue on GitHub repository
