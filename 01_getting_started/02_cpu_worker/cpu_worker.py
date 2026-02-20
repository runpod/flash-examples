# CPU serverless worker -- lightweight processing without GPU.
# Run with: flash run
# Test directly: python cpu_worker.py
from runpod_flash import CpuInstanceType, CpuLiveServerless, remote

cpu_config = CpuLiveServerless(
    name="01_02_cpu_worker",
    instanceIds=[CpuInstanceType.CPU3C_1_2],
    workersMin=0,
    workersMax=3,
    idleTimeout=5,
)


@remote(resource_config=cpu_config)
async def cpu_hello(input_data: dict) -> dict:
    """Simple CPU worker that returns a greeting."""
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


if __name__ == "__main__":
    import asyncio

    test_payload = {"name": "Flash expert"}
    print(f"Testing CPU worker with payload: {test_payload}")
    result = asyncio.run(cpu_hello(test_payload))
    print(f"Result: {result}")
