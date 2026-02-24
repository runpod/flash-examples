# GPU autoscaling strategies -- scale-to-zero, always-on, high-throughput.
# Run with: flash run
# Test directly: python gpu_worker.py
from runpod_flash import GpuGroup, LiveServerless, ServerlessScalerType, remote

# --- Strategy 1: Scale to Zero ---
# Sporadic or batch workloads where cost matters more than cold-start latency.
# Workers scale down to zero after 5 minutes of idle time.
scale_to_zero_config = LiveServerless(
    name="04_01_scale_to_zero",
    gpus=[GpuGroup.ANY],
    workersMin=0,
    workersMax=3,
    idleTimeout=5,
    scalerType=ServerlessScalerType.QUEUE_DELAY,
    scalerValue=4,
)

# --- Strategy 2: Always On ---
# Steady traffic where low latency matters more than cost.
# At least one worker stays warm to avoid cold starts.
always_on_config = LiveServerless(
    name="04_01_always_on",
    gpus=[GpuGroup.ANY],
    workersMin=1,
    workersMax=3,
    idleTimeout=60,
    scalerType=ServerlessScalerType.QUEUE_DELAY,
    scalerValue=4,
)

# --- Strategy 3: High Throughput ---
# Bursty traffic where throughput matters most.
# Starts with 2 warm workers, scales aggressively to 10 based on request count.
high_throughput_config = LiveServerless(
    name="04_01_high_throughput",
    gpus=[GpuGroup.ANY],
    workersMin=2,
    workersMax=10,
    idleTimeout=30,
    scalerType=ServerlessScalerType.REQUEST_COUNT,
    scalerValue=3,
)


@remote(resource_config=scale_to_zero_config)
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
        "config": {"workersMin": 0, "workersMax": 3, "idleTimeout": 5},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


@remote(resource_config=always_on_config)
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


@remote(resource_config=high_throughput_config)
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
