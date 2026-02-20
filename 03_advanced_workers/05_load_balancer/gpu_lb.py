# GPU load-balanced endpoints with custom HTTP routes.
# Run with: flash run
# Test directly: python gpu_lb.py
from runpod_flash import LiveLoadBalancer, remote

gpu_config = LiveLoadBalancer(
    name="03_05_load_balancer_gpu",
    workersMin=1,
)


@remote(gpu_config, method="GET", path="/health")
async def gpu_health() -> dict:
    """Health check endpoint for GPU service."""
    return {"status": "healthy", "service": "gpu"}


@remote(gpu_config, method="POST", path="/compute")
async def compute_intensive(numbers: list[float]) -> dict:
    """Perform compute-intensive operation on GPU.

    Args:
        numbers: List of numbers to process

    Returns:
        Computation results
    """
    import time
    from datetime import datetime, timezone

    start_time = time.time()

    # Simulate GPU-intensive computation
    result = sum(x**2 for x in numbers)
    mean = sum(numbers) / len(numbers) if numbers else 0
    max_val = max(numbers) if numbers else None
    min_val = min(numbers) if numbers else None

    compute_time = (time.time() - start_time) * 1000

    return {
        "status": "success",
        "input_count": len(numbers),
        "sum_of_squares": result,
        "mean": mean,
        "max": max_val,
        "min": min_val,
        "compute_time_ms": round(compute_time, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@remote(gpu_config, method="GET", path="/info")
async def gpu_info() -> dict:
    """Get GPU availability information."""
    try:
        import torch

        if torch.cuda.is_available():
            info = {
                "available": True,
                "device": torch.cuda.get_device_name(0),
                "count": torch.cuda.device_count(),
            }
        else:
            info = {"available": False, "device": "No GPU", "count": 0}
    except Exception as e:
        info = {"available": False, "device": str(e), "count": 0}

    return info


if __name__ == "__main__":
    import asyncio

    async def test():
        print("Testing GPU worker endpoints...\n")

        print("1. Health check:")
        result = await gpu_health()
        print(f"   {result}\n")

        print("2. Compute intensive:")
        result = await compute_intensive([1.0, 2.0, 3.0, 4.0, 5.0])
        print(f"   Sum of squares: {result['sum_of_squares']}")
        print(f"   Mean: {result['mean']}\n")

        print("3. GPU Info:")
        result = await gpu_info()
        print(f"   {result}")

    asyncio.run(test())
