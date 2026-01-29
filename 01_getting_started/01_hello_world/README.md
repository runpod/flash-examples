# Hello World: GPU Serverless Worker

Simple example demonstrating GPU-based serverless workers with automatic scaling on Runpod's infrastructure.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```bash
RUNPOD_API_KEY=your_api_key_here
```

Get your API key from [Runpod Settings](https://www.runpod.io/console/user/settings).

### 3. Run Locally

```bash
flash run
```

Server starts at **http://localhost:8000**

### 4. Test the API

```bash
# Health check
curl http://localhost:8000/ping

# GPU worker
curl -X POST http://localhost:8000/gpu/hello \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello GPU!"}'
```

Visit **http://localhost:8000/docs** for interactive API documentation.

## What This Demonstrates

### GPU Worker (`gpu_worker.py`)

Simple GPU-based serverless function that:
- Detects GPU availability and specifications
- Returns GPU information (name, memory, count)
- Scales from 0-3 workers automatically
- Runs on any available GPU

The worker demonstrates:
- Remote execution with `@remote` decorator
- GPU resource configuration with `LiveServerless`
- Automatic scaling based on demand
- Local development and testing

## API Endpoints

### POST /gpu/hello

Executes a simple GPU worker and returns system/GPU information.

**Request:**
```json
{
  "message": "Hello GPU!"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Hello GPU!",
  "worker_type": "GPU",
  "gpu_info": {
    "available": true,
    "name": "NVIDIA RTX 4090",
    "count": 1,
    "memory_gb": 24.0
  },
  "timestamp": "2024-01-24T10:30:45.123456",
  "platform": "Linux",
  "python_version": "3.11.0"
}
```

## Project Structure

```
01_hello_world/
├── main.py              # FastAPI application
├── gpu_worker.py        # GPU worker with @remote decorator
├── mothership.py        # Mothership endpoint configuration
├── pyproject.toml       # Project metadata
├── requirements.txt     # Dependencies
├── .env.example         # Environment variables template
└── README.md            # This file
```

## Key Concepts

### Remote Execution
The `@remote` decorator transparently executes functions on serverless infrastructure:
- Code runs locally during development
- Automatically deploys to Runpod when configured
- Handles serialization and resource management

### Resource Scaling
The GPU worker scales to zero when idle:
- **workersMin=0**: Scales down completely when idle
- **workersMax=3**: Up to 3 concurrent workers
- **idleTimeout=5**: 5 minutes before scaling down

### GPU Detection
The worker uses PyTorch to detect and report GPU information:
- GPU availability
- GPU model name
- Number of GPUs
- Total memory in GB

## Development

### Test Worker Locally
```bash
python gpu_worker.py
```

### Run the Application
```bash
flash run
```

## Next Steps

- Customize GPU type: Change `GpuGroup.ANY` to specific GPU (ADA_24, AMPERE_80, etc.)
- Add your own GPU-accelerated code
- Implement error handling and validation
- Deploy to production with `flash deploy`

## Resources

- [Flash Documentation](https://docs.runpod.io/flash)
- [Runpod API Documentation](https://docs.runpod.io/api)
- [PyTorch GPU Documentation](https://pytorch.org/docs/stable/cuda.html)
