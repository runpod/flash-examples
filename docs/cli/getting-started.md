# Getting Started with Flash CLI

Complete your first Flash project in under 10 minutes. This guide walks you through creating, testing, and deploying a distributed inference API.

## Prerequisites

Before starting, ensure you have:

- **Python 3.10 or higher** - Check with `python --version`
- **Runpod API Key** - Get from https://runpod.io/console/user/settings
- **Flash installed** - Install with `pip install runpod-flash`

### Verify Installation

```bash
flash --version
# Should output: flash, version X.Y.Z
```

### Configure API Key

Set your Runpod API key as an environment variable:

```bash
export RUNPOD_API_KEY=your-key-here
```

Or add to `.env` file:
```bash
echo "RUNPOD_API_KEY=your-key-here" > .env
```

**Checkpoint:** Running `echo $RUNPOD_API_KEY` should display your key.

---

## Your First Flash Project

### Step 1: Create a New Project

Create a new Flash project with the CLI:

```bash
flash init hello-flash
cd hello-flash
```

**What happened:**
- Created `hello-flash/` directory
- Generated project structure:
  - `main.py` - FastAPI application
  - `mothership.py` - Mothership endpoint config
  - `gpu_worker.py` - GPU worker template
  - `pyproject.toml` - Dependencies
  - `.env.example` - Environment variables template

**Checkpoint:** Run `ls -la` and verify you see these files.

---

### Step 2: Examine the Code

Open `gpu_worker.py` to see your first remote function:

```python
from runpod_flash import remote, LiveServerless, GpuGroup

gpu_config = LiveServerless(
    name="hello_flash_gpu",
    gpus=[GpuGroup.ANY],
    workersMin=0,
    workersMax=3,
    idleTimeout=300,
)

@remote(resource_config=gpu_config)
async def process_request(input_data: dict) -> dict:
    """Example GPU worker that processes requests."""
    # Your GPU processing logic here
    return {
        "status": "success",
        "message": "Hello from Flash GPU worker!",
        "input_received": input_data
    }
```

**Key concepts:**
- `@remote` decorator marks functions to be run in the Runpod cloud
- `LiveServerless` configures GPU resources for the function to be run on

---

### Step 3: Run Locally

Start the development server:

```bash
flash run
```

**Expected output:**
```
INFO: Started server process
INFO: Uvicorn running on http://localhost:8888 (Press CTRL+C to quit)
INFO: Application startup complete
```

**Checkpoint:** Server is running at http://localhost:8888

**What's happening:** Your FastAPI app runs locally on your machine, but when you call a `@remote` function, it executes on Runpod Serverless. This hybrid architecture gives you hot-reload for rapid development while testing real GPU/CPU workloads in the cloud. Endpoints created during `flash run` are prefixed with `live-` to keep them separate from production.

---

### Step 4: Test Your API

Open your browser and visit:
```
http://localhost:8888/docs
```

You'll see FastAPI's interactive Swagger UI with your endpoint.

**Test the endpoint:**

1. Click on the `POST` endpoint
2. Click "Try it out"
3. Enter test JSON:
   ```json
   {
     "input_data": {"message": "test"}
   }
   ```
4. Click "Execute"

**Expected response:**
```json
{
  "status": "success",
  "message": "Hello from Flash GPU worker!",
  "input_received": {
    "message": "test"
  }
}
```

**Checkpoint:** You successfully called your first Flash endpoint!

**Alternatively, test with curl:**
```bash
curl -X POST http://localhost:8888/process \
  -H "Content-Type: application/json" \
  -d '{"input_data": {"message": "test"}}'
```

---

### Step 5: Prepare for Deployment

Stop the development server (Ctrl+C), then create a deployment environment:

```bash
flash env create dev
```

**Expected output:**
```
Environment 'dev' created successfully
```

**What happened:**
- Created a deployment target named "dev"
- This environment will contain your deployed endpoints

**Checkpoint:** Run `flash env list` and verify "dev" appears.

---

### Step 6: Build Your Application

Package your application for deployment:

```bash
flash build
```

**Expected output:**
```
Building Flash application...
Installing dependencies...
Generating manifest...
Creating archive...
✓ Build complete: artifact.tar.gz (45.2 MB)
```

**What happened:**
- Created `.build/` directory with packaged application
- Installed dependencies for Linux x86_64
- Generated handler files for remote functions
- Created `artifact.tar.gz` deployment package

**Checkpoint:** Run `ls -lh artifact.tar.gz` to verify the archive exists.

---

### Step 7: Deploy to Runpod

Deploy your application to the "dev" environment:

```bash
flash deploy --env dev
```

**Expected output:**
```
Building Flash application...
✓ Build complete: artifact.tar.gz (45.2 MB)

Deploying to environment: dev
Uploading artifact...
Creating endpoints...

✓ Deployment successful!

Endpoints:
  hello_flash_gpu: https://abcd1234-hello-flash-gpu.runpod.io

Test your endpoint:
  curl -X POST https://abcd1234-hello-flash-gpu.runpod.io/run \
    -H "Authorization: Bearer $RUNPOD_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"input": {"input_data": {"message": "production test"}}}'
```

**What happened:**
- Built and uploaded your application
- Created Runpod serverless endpoint
- Configured autoscaling (0-3 workers)
- Endpoint is live and ready to handle requests

**Checkpoint:** Copy the curl command and test your deployed endpoint.

---

### Step 8: Test Your Deployed Endpoint

Use the curl command from the deployment output:

```bash
curl -X POST https://abcd1234-hello-flash-gpu.runpod.io/run \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {"input_data": {"message": "production test"}}}'
```

**Expected response:**
```json
{
  "delayTime": 123,
  "executionTime": 456,
  "id": "request-id-here",
  "status": "COMPLETED",
  "output": {
    "status": "success",
    "message": "Hello from Flash GPU worker!",
    "input_received": {
      "message": "production test"
    }
  }
}
```

**Checkpoint:** Your API is live on Runpod!

---

## What You've Learned

In the past 10 minutes, you've:

1. ✅ Created a Flash project with `flash init`
2. ✅ Run a development server with `flash run`
3. ✅ Tested locally via Swagger UI
4. ✅ Created a deployment environment
5. ✅ Built a deployment package with `flash build`
6. ✅ Deployed to Runpod with `flash deploy`
7. ✅ Tested your live production endpoint

---

## Next Steps

### Explore Examples

The flash-examples repository contains production-ready examples:

```bash
git clone https://github.com/runpod/flash-examples.git
cd flash-examples
flash run
# Visit http://localhost:8888/docs to explore all examples
```

**Example categories:**
- `01_getting_started/` - Basic concepts and patterns
- `02_ml_inference/` - Machine learning models
- `03_advanced_workers/` - Load balancing, retries, async
- `04_scaling_performance/` - Optimization techniques
- `05_data_workflows/` - Data processing pipelines
- `06_real_world/` - Complete production architectures

### Learn More Commands

**Development:**
- [flash run options](../CLI-REFERENCE.md#flash-run) - Custom host, port, auto-reload
- [flash build options](../CLI-REFERENCE.md#flash-build) - Size optimization, custom names

**Deployment:**
- [flash deploy options](../CLI-REFERENCE.md#flash-deploy) - Multiple environments, preview mode
- [flash env management](../CLI-REFERENCE.md#flash-env) - Create staging/production

**Cleanup:**
- [flash undeploy](../CLI-REFERENCE.md#flash-undeploy) - Delete endpoints

### Read Comprehensive Documentation

- **[CLI Reference](../CLI-REFERENCE.md)** - All commands with options and examples
- **[Commands Guide](commands.md)** - Exhaustive command documentation
- **[Workflows Guide](workflows.md)** - Common development workflows
- **[Troubleshooting](troubleshooting.md)** - Solutions to common problems

---

## Common Issues

### Command Not Found: flash

**Problem:** `bash: flash: command not found`

**Solution:**
```bash
pip install runpod-flash
# Verify installation
flash --version
```

### Port Already in Use

**Problem:** `ERROR: [Errno 48] Address already in use`

**Solution:**
```bash
# Use different port
flash run --port 9000

# Or find and kill process using port 8888
lsof -ti:8888 | xargs kill -9
```

### Missing API Key

**Problem:** `Error: RUNPOD_API_KEY environment variable not set`

**Solution:**
```bash
export RUNPOD_API_KEY=your-key-here
# Verify
echo $RUNPOD_API_KEY
```

### Build Too Large

**Problem:** `ERROR: Archive size (523MB) exceeds 500MB limit`

**Solution:**
```bash
# Exclude packages present in Runpod base image
flash build --exclude torch,torchvision,torchaudio
```

See [Troubleshooting Guide](troubleshooting.md) for more solutions.

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `flash init <name>` | Create new project |
| `flash run` | Run development server |
| `flash build` | Build deployment package |
| `flash deploy --env <name>` | Deploy to environment |
| `flash env create <name>` | Create environment |
| `flash env list` | List environments |
| `flash undeploy <name>` | Delete endpoint |

---

## Getting Help

- **CLI help:** `flash <command> --help`
- **Full reference:** [CLI-REFERENCE.md](../CLI-REFERENCE.md)
- **Examples:** https://github.com/runpod/flash-examples
- **Documentation:** https://docs.runpod.io
- **Issues:** https://github.com/runpod/flash/issues

## What's Next?

You've completed the getting started guide! Now choose your path:

- **Learn all commands:** [Commands Guide](commands.md)
- **Master workflows:** [Workflows Guide](workflows.md)
- **Solve problems:** [Troubleshooting Guide](troubleshooting.md)
- **Explore examples:** Clone flash-examples repository
