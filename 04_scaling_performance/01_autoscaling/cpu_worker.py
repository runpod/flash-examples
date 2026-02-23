# CPU autoscaling strategies -- scale-to-zero and burst-ready.
# Run with: flash run
# Test directly: python cpu_worker.py
from runpod_flash import CpuInstanceType, CpuLiveServerless, remote

# --- Strategy 1: Scale to Zero ---
# Cost-optimized for preprocessing tasks that tolerate cold starts.
cpu_scale_to_zero_config = CpuLiveServerless(
    name="04_01_cpu_scale_to_zero",
    instanceIds=[CpuInstanceType.CPU3C_1_2],
    workersMin=0,
    workersMax=5,
    idleTimeout=5,
)

# --- Strategy 2: Burst Ready ---
# Always-warm worker for API gateway or latency-sensitive CPU tasks.
cpu_burst_ready_config = CpuLiveServerless(
    name="04_01_cpu_burst_ready",
    instanceIds=[CpuInstanceType.CPU3G_2_8],
    workersMin=1,
    workersMax=10,
    idleTimeout=30,
)


@remote(resource_config=cpu_scale_to_zero_config)
async def cpu_scale_to_zero(payload: dict) -> dict:
    """CPU worker with scale-to-zero -- cost-optimized preprocessing."""
    import hashlib
    import json
    import time

    start_time = time.perf_counter()

    text = payload.get("text", "")

    # Simulate CPU-bound preprocessing: hashing, serialization, string ops
    text_hash = hashlib.sha256(text.encode()).hexdigest()
    normalized = " ".join(text.lower().split())
    tokens = normalized.split()
    serialized = json.dumps({"tokens": tokens, "hash": text_hash})
    byte_size = len(serialized.encode())

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return {
        "status": "success",
        "strategy": "cpu_scale_to_zero",
        "duration_ms": duration_ms,
        "result": {
            "text_hash": text_hash[:16],
            "token_count": len(tokens),
            "byte_size": byte_size,
        },
        "config": {"workersMin": 0, "workersMax": 5, "idleTimeout": 5},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


@remote(resource_config=cpu_burst_ready_config)
async def cpu_burst_ready(payload: dict) -> dict:
    """CPU worker with burst-ready scaling -- always-warm for low latency."""
    import hashlib
    import json
    import time

    start_time = time.perf_counter()

    text = payload.get("text", "")

    # Simulate CPU-bound API gateway work: validation, transformation, routing
    text_hash = hashlib.sha256(text.encode()).hexdigest()
    words = text.split()
    word_lengths = [len(w) for w in words]
    avg_word_length = sum(word_lengths) / len(word_lengths) if word_lengths else 0
    serialized = json.dumps(
        {"words": words, "hash": text_hash, "avg_len": avg_word_length}
    )
    byte_size = len(serialized.encode())

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return {
        "status": "success",
        "strategy": "cpu_burst_ready",
        "duration_ms": duration_ms,
        "result": {
            "text_hash": text_hash[:16],
            "word_count": len(words),
            "avg_word_length": round(avg_word_length, 2),
            "byte_size": byte_size,
        },
        "config": {"workersMin": 1, "workersMax": 10, "idleTimeout": 30},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


if __name__ == "__main__":
    import asyncio

    async def test_all():
        test_payload = {
            "text": "Autoscaling CPU workers for preprocessing and validation"
        }

        print("=== CPU Scale to Zero ===")
        result = await cpu_scale_to_zero(test_payload)
        print(
            f"Duration: {result['duration_ms']}ms | Tokens: {result['result']['token_count']}\n"
        )

        print("=== CPU Burst Ready ===")
        result = await cpu_burst_ready(test_payload)
        print(
            f"Duration: {result['duration_ms']}ms | Words: {result['result']['word_count']}\n"
        )

    asyncio.run(test_all())
