## Hello world: GPU serverless workers
# In this part of the example code, we provision a GPU-based worker and have it
# execute code. We can run the worker directly, or have it handle API requests
# to the router function. It's registered to a subrouter in the __init__.py
# file in this folder, and subsequently imported by main.py and attached to the
# FastAPI app there.

# Scaling behavior is controlled by configuration passed to the
# `LiveServerless` class.
from fastapi import APIRouter
from pydantic import BaseModel

from tetra_rp import (
    GpuGroup,
    LiveServerless,
    remote,
)

# Here, we'll define several variables that change the
# default behavior of our serverless endpoint. `workersMin` sets our endpoint
# to scale to 0 active containers; `workersMax` will allow our endpoint to run
# up to 3 workers in parallel as the endpoint receives more work. We also set
# an idle timeout of 5 minutes so that any active worker stays alive for 5
# minutes after completing a request.
gpu_config = LiveServerless(
    name="01_01_gpu_worker",
    gpus=[GpuGroup.ANY],  # Run on any GPU
    workersMin=0,
    workersMax=3,
    idleTimeout=5,
)


# Decorating our function with `remote` will package up the function code and
# deploy it on the infrastructure according to the passed input config. The
# results from the worker will be returned to your terminal. In this example
# the function will return a greeting to the input string passed in the `name`
# key. The code itself will run on a GPU worker, and information about the GPU
# the worker has access to will be included in the response.
@remote(resource_config=gpu_config)
async def gpu_hello(
    input_data: dict,
) -> dict:
    """Simple GPU worker example with GPU detection."""
    import platform
    from datetime import datetime

    import torch

    gpu_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0)
    gpu_count = torch.cuda.device_count()
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)

    message = input_data.get(
        "message",
        "Hello from GPU worker!",
    )

    return {
        "status": "success",
        "message": message,
        "worker_type": "GPU",
        "gpu_info": {
            "available": gpu_available,
            "name": gpu_name,
            "count": gpu_count,
            "memory_gb": round(
                gpu_memory,
                2,
            ),
        },
        "timestamp": datetime.now().isoformat(),
        "platform": platform.system(),
        "python_version": platform.python_version(),
    }


# We define a subrouter for our gpu worker so that our main router in `main.py`
# can attach it for routing gpu-specific requests.
gpu_router = APIRouter()


class MessageRequest(BaseModel):
    """Request model for GPU worker."""

    message: str = "Hello from GPU!"


@gpu_router.post("/hello")
async def hello(
    request: MessageRequest,
):
    """Simple GPU worker endpoint."""
    result = await gpu_hello({"message": request.message})
    return result


# This code is packaged up as a "worker" that will handle requests sent to the
# endpoint at /gpu/hello, but you can also trigger it directly by running
# python -m workers.gpu.endpoint
if __name__ == "__main__":
    import asyncio

    test_payload = {"message": "Testing GPU worker"}
    print(f"Testing GPU worker with payload: {test_payload}")
    result = asyncio.run(gpu_hello(test_payload))
    print(f"Result: {result}")
