# numpy version benchmark -- measures performance across numpy versions.
# run with: flash run
# test directly: python numpy_benchmark.py
from runpod_flash import Endpoint


@Endpoint(
    name="07_numpy_v1",
    cpu="cpu3c-1-2",
    dependencies=["numpy==1.26.4"],
)
async def numpy_benchmark(payload: dict) -> dict:
    """Benchmark numpy operations and report version + timing + correctness hashes."""
    import hashlib
    import time

    import numpy as np

    np.random.seed(42)
    installed_version = np.__version__
    benchmarks = {}
    total_start = time.perf_counter()

    # matrix multiplication: 1000x1000 dot product
    a = np.random.rand(1000, 1000)
    b = np.random.rand(1000, 1000)
    start = time.perf_counter()
    result = np.dot(a, b)
    elapsed = (time.perf_counter() - start) * 1000
    result_hash = hashlib.sha256(result.tobytes()).hexdigest()[:12]
    benchmarks["matrix_multiply"] = {
        "time_ms": round(elapsed, 2),
        "result_hash": result_hash,
    }

    # array sort: 1M random elements
    arr = np.random.rand(1_000_000)
    start = time.perf_counter()
    sorted_arr = np.sort(arr)
    elapsed = (time.perf_counter() - start) * 1000
    result_hash = hashlib.sha256(sorted_arr.tobytes()).hexdigest()[:12]
    benchmarks["array_sort"] = {
        "time_ms": round(elapsed, 2),
        "result_hash": result_hash,
    }

    # FFT: 1D FFT on 1M points
    signal = np.random.rand(1_000_000)
    start = time.perf_counter()
    fft_result = np.fft.fft(signal)
    elapsed = (time.perf_counter() - start) * 1000
    result_hash = hashlib.sha256(fft_result.tobytes()).hexdigest()[:12]
    benchmarks["fft"] = {"time_ms": round(elapsed, 2), "result_hash": result_hash}

    # element-wise: sin + cos on 1M elements
    arr = np.random.rand(1_000_000)
    start = time.perf_counter()
    result = np.sin(arr) + np.cos(arr)
    elapsed = (time.perf_counter() - start) * 1000
    result_hash = hashlib.sha256(result.tobytes()).hexdigest()[:12]
    benchmarks["elementwise"] = {
        "time_ms": round(elapsed, 2),
        "result_hash": result_hash,
    }

    total_ms = round((time.perf_counter() - total_start) * 1000, 2)

    return {
        "version": {"installed": installed_version},
        "benchmarks": benchmarks,
        "total_time_ms": total_ms,
    }


if __name__ == "__main__":
    import asyncio
    import json

    async def test():
        print("\n=== Numpy Benchmark ===")
        result = await numpy_benchmark({})
        print(json.dumps(result, indent=2))

    asyncio.run(test())
