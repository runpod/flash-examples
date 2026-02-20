# GPU serverless worker -- detects available GPU hardware.
# Run with: flash run
# Test directly: python gpu_worker.py
from runpod_flash import GpuGroup, LiveServerless, remote

gpu_config = LiveServerless(
    name="01_01_gpu_worker",
    gpus=[GpuGroup.ANY],
    workersMin=0,
    workersMax=3,
    idleTimeout=5,
)


@remote(resource_config=gpu_config)
async def gpu_hello(input_data: dict) -> dict:
    """Simple GPU worker that returns GPU hardware info."""
    import platform
    from datetime import datetime

    import torch

    gpu_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0)
    gpu_count = torch.cuda.device_count()
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)

    message = input_data.get("message", "Hello from GPU worker!")

    return {
        "status": "success",
        "message": message,
        "worker_type": "GPU",
        "gpu_info": {
            "available": gpu_available,
            "name": gpu_name,
            "count": gpu_count,
            "memory_gb": round(gpu_memory, 2),
        },
        "timestamp": datetime.now().isoformat(),
        "platform": platform.system(),
        "python_version": platform.python_version(),
    }


if __name__ == "__main__":
    import asyncio

    test_payload = {"message": "Testing GPU worker"}
    print(f"Testing GPU worker with payload: {test_payload}")
    result = asyncio.run(gpu_hello(test_payload))
    print(f"Result: {result}")
