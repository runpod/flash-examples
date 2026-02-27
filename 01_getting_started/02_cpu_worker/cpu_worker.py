# cpu serverless worker -- lightweight processing without GPU.
# run with: flash run
# test directly: python cpu_worker.py
from runpod_flash import CpuInstanceType, Endpoint


@Endpoint(
    name="01_02_cpu_worker",
    cpu=CpuInstanceType.CPU3C_1_2,
    workers=(0, 3),
    idle_timeout=5,
)
async def cpu_hello(input_data: dict) -> dict:
    """CPU worker that returns a greeting."""
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
