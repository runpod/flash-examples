# GPU and CPU workers sharing a common dependency (numpy).
# Demonstrates that dependencies work correctly across both runtime environments:
#   - GPU images (runpod/pytorch:*) have numpy pre-installed
#   - CPU images (python-slim) install numpy from the build artifact
#
# run with: flash run
# test directly: python mixed_worker.py
from runpod_flash import CpuInstanceType, Endpoint, GpuType


@Endpoint(
    name="01_04_deps_gpu_numpy",
    gpu=GpuType.NVIDIA_GEFORCE_RTX_4090,
    workers=(0, 3),
    dependencies=["numpy"],
)
async def gpu_matrix_multiply(input_data: dict) -> dict:
    """GPU-instance worker running CPU-bound numpy matrix operations.

    This endpoint runs on a GPU instance type, but uses standard numpy,
    so all computations execute on the CPU. On GPU images, numpy is
    pre-installed in the base image; the build artifact also includes
    it, so both paths work, with the image's copy taking precedence.
    """
    import numpy as np

    size = min(max(int(input_data.get("size", 100)), 1), 10_000)
    a = np.random.rand(size, size)
    b = np.random.rand(size, size)
    result = np.dot(a, b)

    return {
        "status": "success",
        "worker_type": "GPU",
        "matrix_size": size,
        "result_shape": list(result.shape),
        "result_trace": float(np.trace(result)),
        "numpy_version": np.__version__,
    }


@Endpoint(
    name="01_04_deps_cpu_numpy",
    cpu=CpuInstanceType.CPU3C_1_2,
    workers=(0, 3),
    dependencies=["numpy"],
)
async def cpu_statistics(input_data: dict) -> dict:
    """CPU worker using numpy for statistical computations.

    On CPU images (python-slim), numpy is NOT pre-installed. The build
    artifact must include it. Flash's build pipeline ships numpy in the
    tarball for CPU endpoints.
    """
    import numpy as np

    raw_values = input_data.get("values", [1.0, 2.0, 3.0, 4.0, 5.0])
    if not isinstance(raw_values, list) or len(raw_values) > 100_000:
        return {
            "status": "error",
            "message": "values must be a list with at most 100000 elements",
        }
    values = raw_values
    arr = np.array(values)

    return {
        "status": "success",
        "worker_type": "CPU",
        "count": len(values),
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "median": float(np.median(arr)),
        "numpy_version": np.__version__,
    }


if __name__ == "__main__":
    import asyncio

    async def test():
        print("\n=== Testing GPU numpy (matrix multiply) ===")
        gpu_result = await gpu_matrix_multiply({"size": 50})
        print(f"Result: {gpu_result}\n")

        print("=== Testing CPU numpy (statistics) ===")
        cpu_result = await cpu_statistics({"values": [10, 20, 30, 40, 50]})
        print(f"Result: {cpu_result}\n")

    asyncio.run(test())
