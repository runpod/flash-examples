## Hello world: CPU serverless workers
# In this part of the example code, we provision a CPU-based worker (no GPUs) and have it execute code.
# We can run the worker directly, or have it handle API requests to the router function.
# It's registered to a subrouter in the __init__.py file in this folder, and subsequently
# imported by main.py and attached to the FastAPI app there.
from fastapi import APIRouter
from pydantic import BaseModel

from tetra_rp import CpuInstanceType, CpuLiveServerless, remote

# Scaling behavior is controlled by configuration passed to the `CpuLiveServerless` class.
# Here, we'll define several variables that change the default behavior of our serverless endpoint.
# `workersMin` sets our endpoint to scale to 0 active containers; `workersMax` will allow our endpoint
# to run up to 5 workers in parallel as the endpoint receives more work.
# We also set an idle timeout of 5 minutes so that any active worker stays alive for 5 minutes after completing a request.
cpu_config = CpuLiveServerless(
    name="cpu_worker",
    instanceIds=[CpuInstanceType.ANY],
    workersMin=0,  # Scale to zero
    workersMax=3,
    idleTimeout=5,  # Leave workers alive for 5 minutes after they serve a request
)


# Decorating our function with `remote` will package up the function code and deploy it on the infrastructure
# according to the passed input config.
# In this example the function will return a greeting to the input string passed in the `name` key.
# The results are displayed in your terminal, but the work was performed by CPU workers on runpod infra.
@remote(resource_config=cpu_config)
async def cpu_hello(input_data: dict) -> dict:
    """Simple CPU worker example."""
    import platform
    from datetime import datetime

    message = f"Hello, {input_data.get('name', 'Anonymous Panda')}!"

    return {
        "status": "success",
        "message": message,
        "worker_type": "CPU",
        "timestamp": datetime.now().isoformat(),
        "platform": platform.system(),
        "python_version": platform.python_version(),
    }


cpu_router = APIRouter()


class MessageRequest(BaseModel):
    """Request model for CPU worker."""

    name: str = "Flash expert"


@cpu_router.post("/hello")
async def hello(request: MessageRequest):
    """Simple CPU worker endpoint."""
    result = await cpu_hello({"message": request.name})
    return result


# This code is packaged up as a "worker" that will handle requests sent to the endpoint at
# /cpu/hello, but you can also trigger it locally by running python -m workers.cpu.endpoint.
if __name__ == "__main__":
    import asyncio

    test_payload = {"name": "Flash expert"}
    print(f"Testing CPU worker with payload: {test_payload}")
    result = asyncio.run(cpu_hello(test_payload))
    print(f"Result: {result}")
