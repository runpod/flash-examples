# GPU autoscaling strategies -- scale-to-zero, always-on, high-throughput.
# Run: python gpu_worker.py
# Alternative: flash run (for HTTP API testing)
from runpod_flash import Endpoint, GpuType, ServerlessScalerType


# --- strategy 1: scale to zero ---
# sporadic or batch workloads where cost matters more than cold-start latency.
# workers scale down to zero after 5 minutes of idle time.
@Endpoint(
    name="04_01_scale_to_zero",
    gpu=GpuType.NVIDIA_GEFORCE_RTX_4090,
    workers=(0, 3),
    idle_timeout=300,
    scaler_type=ServerlessScalerType.QUEUE_DELAY,
    scaler_value=4,
)
async def scale_to_zero_inference(payload: dict) -> dict:
    """GPU inference with scale-to-zero -- cost-optimized for sporadic workloads."""
    import asyncio
    import time

    import torch

    start_time = time.perf_counter()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    size = payload.get("matrix_size", 512)
    a = torch.randn(size, size, device=device)
    b = torch.randn(size, size, device=device)
    _ = torch.mm(a, b)

    await asyncio.sleep(0.5)

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return {
        "status": "success",
        "strategy": "scale_to_zero",
        "duration_ms": duration_ms,
        "gpu_info": {
            "available": torch.cuda.is_available(),
            "device": device,
            "name": torch.cuda.get_device_name(0)
            if torch.cuda.is_available()
            else "N/A",
        },
        "config": {"workersMin": 0, "workersMax": 3, "idleTimeout": 300},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


# --- strategy 2: always on ---
# steady traffic where low latency matters more than cost.
# at least one worker stays warm to avoid cold starts.
@Endpoint(
    name="04_01_always_on",
    gpu=GpuType.NVIDIA_GEFORCE_RTX_4090,
    workers=(1, 3),
    idle_timeout=60,
    scaler_type=ServerlessScalerType.QUEUE_DELAY,
    scaler_value=4,
)
async def always_on_inference(payload: dict) -> dict:
    """GPU inference with always-on worker -- latency-optimized for steady traffic."""
    import asyncio
    import time

    import torch

    start_time = time.perf_counter()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    size = payload.get("matrix_size", 512)
    a = torch.randn(size, size, device=device)
    b = torch.randn(size, size, device=device)
    _ = torch.mm(a, b)

    await asyncio.sleep(0.5)

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return {
        "status": "success",
        "strategy": "always_on",
        "duration_ms": duration_ms,
        "gpu_info": {
            "available": torch.cuda.is_available(),
            "device": device,
            "name": torch.cuda.get_device_name(0)
            if torch.cuda.is_available()
            else "N/A",
        },
        "config": {"workersMin": 1, "workersMax": 3, "idleTimeout": 60},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


# --- strategy 3: high throughput ---
# bursty traffic where throughput matters most.
# starts with 2 warm workers, scales aggressively to 10 based on request count.
@Endpoint(
    name="04_01_high_throughput",
    gpu=GpuType.NVIDIA_GEFORCE_RTX_4090,
    workers=(2, 10),
    idle_timeout=30,
    scaler_type=ServerlessScalerType.REQUEST_COUNT,
    scaler_value=3,
)
async def high_throughput_inference(payload: dict) -> dict:
    """GPU inference with high-throughput scaling -- optimized for bursty traffic."""
    import asyncio
    import time

    import torch

    start_time = time.perf_counter()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    size = payload.get("matrix_size", 512)
    a = torch.randn(size, size, device=device)
    b = torch.randn(size, size, device=device)
    _ = torch.mm(a, b)

    await asyncio.sleep(1.0)

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return {
        "status": "success",
        "strategy": "high_throughput",
        "duration_ms": duration_ms,
        "gpu_info": {
            "available": torch.cuda.is_available(),
            "device": device,
            "name": torch.cuda.get_device_name(0)
            if torch.cuda.is_available()
            else "N/A",
        },
        "config": {"workersMin": 2, "workersMax": 10, "idleTimeout": 30},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


if __name__ == "__main__":
    import asyncio

    async def test_all():
        test_payload = {"matrix_size": 256}

        print("=== Scale to Zero Strategy ===")
        result = await scale_to_zero_inference(test_payload)
        print(
            f"Duration: {result['duration_ms']}ms | Device: {result['gpu_info']['device']}\n"
        )

        print("=== Always On Strategy ===")
        result = await always_on_inference(test_payload)
        print(
            f"Duration: {result['duration_ms']}ms | Device: {result['gpu_info']['device']}\n"
        )

        print("=== High Throughput Strategy ===")
        result = await high_throughput_inference(test_payload)
        print(
            f"Duration: {result['duration_ms']}ms | Device: {result['gpu_info']['device']}\n"
        )

    asyncio.run(test_all())
