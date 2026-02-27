# Load Balancer Endpoints Example

Demonstrates Flash's load-balanced endpoints with custom HTTP routes using the `Endpoint` class with route decorators. This example shows how to create low-latency APIs with direct HTTP routing on a single serverless endpoint.

## What Are Load-Balanced Endpoints?

Load-balanced endpoints use direct HTTP routing to serverless workers, providing lower latency compared to queue-based endpoints. They support custom HTTP methods (GET, POST, PUT, DELETE, PATCH) and multiple routes on a single endpoint.

| Feature | Queue-Based (QB) | Load-Balanced (LB) |
|---------|------------------|-------------------|
| Request model | Sequential queue | Direct HTTP routing |
| Latency | Higher (queuing) | Lower (direct) |
| Custom routes | Limited | Full HTTP support (GET, POST, PUT, DELETE, PATCH) |
| Automatic retries | Yes | No (client handles) |
| Use case | Batch processing, long-running tasks | Real-time APIs, request/response patterns |

**Load-balanced endpoints are ideal for:**
- Low-latency REST APIs
- Custom HTTP routes with different methods (GET, POST, etc.)
- Request/response patterns that require direct HTTP communication
- Multiple endpoints on a single serverless instance
- Services requiring fast turnaround times

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Add your RUNPOD_API_KEY to .env
```

Get your API key from [Runpod Settings](https://www.runpod.io/console/user/settings).

### 3. Run Locally (from repository root)

```bash
flash run
```

Visit **http://localhost:8888/docs** for interactive API documentation (unified app with all examples).

### 4. Test Endpoints (via unified app)

When using `flash run` from the repository root, routes are prefixed with the example name:

**GPU Service (Compute)**:
```bash
# Health check
curl http://localhost:8888/05_load_balancer/gpu/health

# List GPU info
curl http://localhost:8888/05_load_balancer/gpu/info

# Compute with GPU
curl -X POST http://localhost:8888/05_load_balancer/gpu/compute \
  -H "Content-Type: application/json" \
  -d '{"numbers": [1, 2, 3, 4, 5]}'
```

**CPU Service (Data Processing)**:
```bash
# Health check
curl http://localhost:8888/05_load_balancer/cpu/health

# Validate text
curl -X POST http://localhost:8888/05_load_balancer/cpu/validate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}'

# Transform text
curl -X POST http://localhost:8888/05_load_balancer/cpu/transform \
  -H "Content-Type: application/json" \
  -d '{"text": "hello", "operation": "uppercase"}'
```

## How Load-Balanced Endpoints Work

### Defining Routes with Endpoint

Load-balanced endpoints use the `Endpoint` class with route decorators (`.get()`, `.post()`, etc.) to define HTTP routes. The decorator automatically registers the function as an HTTP endpoint on the load-balancer runtime.

```python
from runpod_flash import Endpoint, GpuGroup

# create load-balanced endpoint
api = Endpoint(name="my-service", gpu=GpuGroup.ANY, workers=(1, 3))

# define HTTP routes with method decorators
@api.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}

@api.post("/compute")
async def compute_data(numbers: list[int]) -> dict:
    """Compute the sum of squared numbers."""
    result = sum(x ** 2 for x in numbers)
    return {"result": result}

@api.get("/info")
async def get_info() -> dict:
    """Get service information."""
    return {"info": "service running"}
```

**Key parameters for Endpoint:**
- `name`: Endpoint name for identification
- `gpu=` or `cpu=`: Resource type
- `workers=(min, max)`: Worker scaling bounds

**How routing works:**
1. Each route-decorated function becomes an HTTP endpoint
2. The decorator method (`.get()`, `.post()`, etc.) specifies the HTTP verb
3. The path argument specifies the URL route
4. When an HTTP request matches the method and path, the function is called with the request data

### Multiple Routes on One Endpoint

One load-balanced endpoint can have multiple routes:

```python
api = Endpoint(name="user-api", cpu="cpu3c-1-2", workers=(1, 5))

@api.get("/users")
async def list_users(): ...

@api.post("/users")
async def create_user(name: str): ...

@api.delete("/users/{user_id}")
async def delete_user(user_id: int): ...
```

All routes are automatically registered on the same load-balanced endpoint.

### Queue-Based vs Load-Balanced

The `Endpoint` class infers QB vs LB from usage pattern:
- **Direct decorator** (`@Endpoint(...)`) = queue-based (one function per endpoint)
- **Route decorators** (`.get()`, `.post()`, etc.) = load-balanced (multiple routes, shared workers)

### Reserved Paths

The following paths are reserved and cannot be used:
- `/ping` - Health check endpoint (reserved)
- `/execute` - Framework endpoint (local development only)

## Project Structure

```
05_load_balancer/
├── gpu_lb.py            # GPU load-balanced endpoints
├── cpu_lb.py            # CPU load-balanced endpoints
├── .env.example         # Environment template
├── requirements.txt     # Dependencies
└── README.md            # This file
```

## GPU Service Endpoints

**Compute-intensive operations on GPU**

### GET /gpu/health
Health check for GPU service.
```bash
curl http://localhost:8888/05_load_balancer/gpu/health
```

### GET /gpu/info
Get GPU availability and device information.
```bash
curl http://localhost:8888/05_load_balancer/gpu/info
```

### POST /gpu/compute
Perform compute-intensive operations on GPU.

Request:
```json
{
  "numbers": [1, 2, 3, 4, 5]
}
```

Response:
```json
{
  "status": "success",
  "input_count": 5,
  "sum_of_squares": 55,
  "mean": 3.0,
  "max": 5,
  "min": 1,
  "compute_time_ms": 0.42
}
```

## CPU Service Endpoints

**Data processing operations**

### GET /cpu/health
Health check for CPU service.

### POST /cpu/validate
Validate and analyze text data.

Request:
```json
{
  "text": "Hello world from load balancer"
}
```

Response:
```json
{
  "status": "success",
  "is_valid": true,
  "character_count": 30,
  "word_count": 5,
  "average_word_length": 6.0
}
```

### POST /cpu/transform
Transform text with various operations.

Request:
```json
{
  "text": "hello world",
  "operation": "uppercase"
}
```

Operations:
- `uppercase` - Convert to uppercase
- `lowercase` - Convert to lowercase
- `reverse` - Reverse the text
- `title` - Convert to title case

Response:
```json
{
  "status": "success",
  "original": "hello world",
  "transformed": "HELLO WORLD",
  "operation": "uppercase"
}
```

## Testing Workers Locally

```bash
# Test GPU worker
python gpu_lb.py

# Test CPU worker
python cpu_lb.py
```

## Deployment

### Build for Production

```bash
flash build
```

This generates handlers for your load-balanced endpoints.

### Deploy to RunPod

```bash
flash deploy new production
flash deploy send production
```

## Key Concepts

### Async Functions
All route-decorated functions should be async:
```python
@api.post("/process")
async def process_data(input: str) -> dict:
    return {"result": "success"}
```

### Error Handling
For load-balanced endpoints, raise `ValueError` for validation errors. The framework automatically handles these as HTTP 400 Bad Request responses:
```python
@api.post("/process")
async def process(text: str) -> dict:
    if not text:
        raise ValueError("text cannot be empty")
    return {"result": text.upper()}
```

**HTTP Error Mapping:**
- `ValueError` -> 400 Bad Request
- Other exceptions -> 500 Internal Server Error

### Dependencies
Specify Python dependencies on the Endpoint:
```python
api = Endpoint(
    name="my-service",
    gpu=GpuGroup.ADA_24,
    dependencies=["torch", "transformers"],
)

@api.post("/analyze")
async def analyze(data: str) -> dict:
    import torch
    # your code here
```

## Environment Variables

```bash
# Required
RUNPOD_API_KEY=your_api_key_here

# Optional
FLASH_HOST=localhost     # Server host (default: localhost)
FLASH_PORT=8888         # Server port (default: 8888)
LOG_LEVEL=INFO          # Logging level (default: INFO)
```

## Cost Estimates

Load-balanced endpoints are cost-efficient for request/response patterns:

**GPU Service (Compute)**
- Instance type: GPU (depends on your configuration)
- Minimum workers: 1
- Idle timeout: Varies by configuration
- Cost: Pay-per-second while running

**CPU Service (Data Processing)**
- Instance type: 3 vCPU, 1 GB RAM (CPU3C_1_2)
- Minimum workers: 1
- Cost: ~$0.0002 per hour per worker (idle)

**Comparison with queue-based endpoints:**
- Load-balancers: Lower latency, pay for active processing time only
- Queue-based: Higher throughput, automatic retries, better for batch jobs

For current pricing, see [RunPod Pricing](https://www.runpod.io/pricing).

## Troubleshooting

### Load-balanced endpoints not responding

**Problem**: Endpoints return 502 or timeout
- Ensure workers are properly deployed with `flash deploy`
- Check worker logs via RunPod console
- Verify route paths match your HTTP requests
- Confirm the resource configuration (GPU/CPU types) is available

### ValueError not mapping to 400 responses

**Problem**: Validation errors return 500 instead of 400
- Ensure you're raising `ValueError` for validation errors
- For custom error types, the framework may return 500
- Raise `ValueError` for all user input validation errors

### Workers not starting

**Problem**: Workers fail to initialize
- Check that all `dependencies` are available
- Verify the container image has required system packages
- Check worker function imports and module availability
- Review worker logs in the RunPod console

### Mixed latency in responses

**Problem**: Some requests are fast, others are slow
- Load-balanced uses direct HTTP routing (no queue)
- First request to a cold worker will be slower (initialization)
- Set `workers=(1, N)` to keep workers warm if consistent low latency is critical
- Adjust `idle_timeout` to reduce cold starts

## Next Steps

1. Explore the endpoints via Swagger UI (`/docs`)
2. Modify the route functions to add your logic
3. Add new routes with different HTTP methods
4. Deploy to RunPod when ready
5. Monitor performance and scaling behavior
