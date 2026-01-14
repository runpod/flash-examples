# Load Balancer Endpoints Example

Demonstrates Flash's load-balancer endpoints with custom HTTP routes using the `@remote` decorator with `method` and `path` parameters. This example shows how to create low-latency APIs with direct HTTP routing on a single serverless endpoint.

## What Are Load-Balancer Endpoints?

Load-balancer endpoints use direct HTTP routing to serverless workers, providing lower latency compared to queue-based endpoints. They support custom HTTP methods (GET, POST, PUT, DELETE, PATCH) and multiple routes on a single endpoint.

| Feature | Queue-Based (QB) | Load-Balanced (LB) |
|---------|------------------|-------------------|
| Request model | Sequential queue | Direct HTTP routing |
| Latency | Higher (queuing) | Lower (direct) |
| Custom routes | Limited | Full HTTP support (GET, POST, PUT, DELETE, PATCH) |
| Automatic retries | Yes | No (client handles) |
| Configuration | Default `ServerlessType.QB` | Use `LiveLoadBalancer` or `LoadBalancerSlsResource` |
| Use case | Batch processing, long-running tasks | Real-time APIs, request/response patterns |

**Load-balancer endpoints are ideal for:**
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

### 5. Run Standalone (for this example only)

```bash
cd 03_advanced_workers/05_load_balancer
python main.py
```

This runs the example on **http://localhost:8000** (default standalone port) without the example name prefix. The unified app uses port 8888, but standalone mode defaults to 8000 unless FLASH_PORT is set.

## How Load-Balancer Endpoints Work

### Defining Routes with @remote Decorator

Load-balancer endpoints use the `@remote` decorator with `method` and `path` parameters to define HTTP routes. The decorator automatically registers the function as an HTTP endpoint on the load-balancer runtime.

```python
from tetra_rp import remote, LiveLoadBalancer

# Create load-balanced endpoint (for local development)
lb = LiveLoadBalancer(name="my_service")

# Define HTTP routes with method and path parameters
@remote(lb, method="GET", path="/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}

@remote(lb, method="POST", path="/compute")
async def compute_data(numbers: list[int]) -> dict:
    """Compute the sum of squared numbers."""
    result = sum(x ** 2 for x in numbers)
    return {"result": result}

@remote(lb, method="GET", path="/info")
async def get_info() -> dict:
    """Get service information."""
    return {"info": "service running"}
```

**Key parameters for @remote:**
- `method`: HTTP verb (GET, POST, PUT, DELETE, PATCH)
- `path`: Route path (must start with `/`)
- Resource: Use `LiveLoadBalancer` for local development, `LoadBalancerSlsResource` for production deployment

**How routing works:**
1. Each `@remote` decorated function becomes an HTTP endpoint
2. The `method` parameter specifies the HTTP verb
3. The `path` parameter specifies the URL route
4. When an HTTP request matches the method and path, the function is called with the request data

### Multiple Routes on One Endpoint

One load-balanced endpoint can have multiple routes:

```python
api = LiveLoadBalancer(name="user_api")

@remote(api, method="GET", path="/users")
async def list_users(): ...

@remote(api, method="POST", path="/users")
async def create_user(name: str): ...

@remote(api, method="DELETE", path="/users/{user_id}")
async def delete_user(user_id: int): ...
```

All routes are automatically registered on the same load-balanced endpoint.

### Reserved Paths

The following paths are reserved and cannot be used:
- `/ping` - Health check endpoint (reserved)
- `/execute` - Framework endpoint (local development only)

## Project Structure

```
05_load_balancer/
├── main.py                    # FastAPI application
├── workers/
│   ├── gpu/                  # GPU load-balancer endpoints
│   │   ├── __init__.py       # Router with endpoints
│   │   └── endpoint.py       # @remote functions
│   └── cpu/                  # CPU load-balancer endpoints
│       ├── __init__.py       # Router with endpoints
│       └── endpoint.py       # @remote functions
├── .env.example              # Environment template
├── requirements.txt          # Dependencies
└── README.md                 # This file
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

## Resource Types

### LiveLoadBalancer (Local Development)

`LiveLoadBalancer` is used for local development and testing. It provides all load-balancer features in a development environment without requiring a full deployment.

```python
from tetra_rp import LiveLoadBalancer, remote

# Create load-balanced endpoint for local development
lb = LiveLoadBalancer(name="my_api")

@remote(lb, method="POST", path="/process")
async def process(data: dict) -> dict:
    """Process data on the load-balanced endpoint."""
    return {"result": "success", "processed": data}
```

**When to use:**
- Local development and testing
- Testing @remote decorated functions before deployment
- Running examples with `flash run` from the repository root

**Features:**
- Automatically uses the `tetra-rp-lb` container image
- Local execution with `/execute` endpoint for development
- Perfect for testing and debugging
- No GPU/CPU configuration needed (inherits from resource type)

### LoadBalancerSlsResource (Production Deployment)

`LoadBalancerSlsResource` is the production resource for deploying load-balancer endpoints to RunPod.

```python
from tetra_rp import LoadBalancerSlsResource, remote

# Create load-balanced endpoint for production deployment
lb = LoadBalancerSlsResource(
    name="my_api",
    imageName="runpod/tetra-rp-lb:latest",
    workersMin=1,
    workersMax=5,
)

@remote(lb, method="POST", path="/process")
async def process(data: dict) -> dict:
    """Process data on the deployed load-balanced endpoint."""
    return {"result": "success", "processed": data}
```

**When to use:**
- Production deployment to RunPod
- Scaling requirements (auto-scaling based on request count)
- Multi-region deployment

**Features:**
- Direct HTTP routing to healthy workers
- Auto-scaling based on request count (default scaler)
- No `/execute` endpoint (security - direct routes only)
- Client handles retries (no automatic retries)
- Lower latency for request/response patterns
- Custom HTTP routes on a single endpoint

## Testing Workers Locally

```bash
# Test GPU worker
python -m workers.gpu.endpoint

# Test CPU worker
python -m workers.cpu.endpoint
```

## Deployment

### Build for Production

```bash
flash build
```

This generates handlers for your load-balancer endpoints.

### Deploy to RunPod

```bash
flash deploy new production
flash deploy send production
```

## Local vs Deployed

The `@remote` decorator with method and path works the same way in both local and production environments. The only difference is the resource configuration.

**Local Development (LiveLoadBalancer):**
- Use `LiveLoadBalancer` for testing load-balancer endpoints locally
- Automatically uses `tetra-rp-lb` container image
- Includes `/execute` endpoint for development/testing
- Testing via `flash run` or direct Python execution
- Perfect for development, testing, and debugging

**Production Deployment (LoadBalancerSlsResource):**
- Use `LoadBalancerSlsResource` when deploying to RunPod
- Specifies the container image and scaling parameters
- No `/execute` endpoint (security - direct routes only)
- All execution flows through custom HTTP routes
- Automatic scaling based on request count
- Direct HTTP routing to healthy workers

**Migration path:** Code remains identical - just change the resource from `LiveLoadBalancer` to `LoadBalancerSlsResource` when deploying to production!

## Key Concepts

### Async Functions
All `@remote` functions should be async:
```python
@remote(config, method="POST", path="/process")
async def process_data(input: str) -> dict:
    # Your code here
    return {"result": "success"}
```

### Error Handling
For load-balancer endpoints, raise `ValueError` for validation errors. The framework automatically handles these as HTTP 400 Bad Request responses:
```python
@remote(lb, method="POST", path="/process")
async def process(text: str) -> dict:
    if not text:
        raise ValueError("text cannot be empty")
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    return {"result": text.upper()}
```

**HTTP Error Mapping:**
- `ValueError` → 400 Bad Request
- Other exceptions → 500 Internal Server Error

### Dependencies
Specify Python dependencies in the decorator:
```python
@remote(
    config,
    method="POST",
    path="/analyze",
    dependencies=["torch", "transformers"]
)
async def analyze(data: str) -> dict:
    import torch
    # Your code here
```

## Environment Variables

```bash
# Required
RUNPOD_API_KEY=your_api_key_here

# Optional
FLASH_HOST=localhost     # Server host (default: localhost)
FLASH_PORT=8000         # Server port (default: 8000)
LOG_LEVEL=INFO          # Logging level (default: INFO)
```

## Cost Estimates

Load-balancer endpoints are cost-efficient for request/response patterns:

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

### Load-balancer endpoints not responding

**Problem**: Endpoints return 502 or timeout
- Ensure workers are properly deployed with `flash deploy`
- Check worker logs via RunPod console
- Verify `method` and `path` parameters match your HTTP requests
- Confirm the resource configuration (GPU/CPU types) is available

### ValueError not mapping to 400 responses

**Problem**: Validation errors return 500 instead of 400
- Ensure you're raising `ValueError` for validation errors
- For custom error types, the framework may return 500
- Raise `ValueError` for all user input validation errors

### Workers not starting

**Problem**: Workers fail to initialize
- Check that all dependencies in `dependencies` parameter are available
- Verify the container image has required system packages
- Check worker function imports and module availability
- Review worker logs in the RunPod console

### Mixed latency in responses

**Problem**: Some requests are fast, others are slow
- Load-balancer uses direct HTTP routing (no queue)
- First request to a cold worker will be slower (initialization)
- Adjust `workersMin` to keep workers warm if consistent low latency is critical
- Consider using `idleTimeout` to reduce cold starts

### Endpoint discovery not working

**Problem**: Example doesn't load in unified app with `flash run`
- Ensure routers are named `gpu_router` and `cpu_router`
- Verify routers are properly exported in `__init__.py` files
- Check that `main.py` includes routers with `app.include_router()`
- Run `flash run` from the repository root, not the example directory

## Next Steps

1. Explore the endpoints via Swagger UI (`/docs`)
2. Modify the `@remote` functions to add your logic
3. Add new routes with different `method` and `path` values
4. Deploy to RunPod when ready
5. Monitor performance and scaling behavior
