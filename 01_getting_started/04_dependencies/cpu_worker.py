# cpu workers demonstrating data science and zero-dependency patterns.
# run with: flash run
# test directly: python cpu_worker.py
from runpod_flash import CpuInstanceType, Endpoint

# worker with data science dependencies
@Endpoint(
    name="01_04_deps_data",
    cpu=CpuInstanceType.CPU3C_8_16,
    workers=(0, 3),
    dependencies=[
        "pandas==2.1.3",
        "numpy==1.26.2",
        "scipy>=1.11.0",
        "matplotlib",
    ],
)
async def process_data(input_data: dict) -> dict:
    """
    Worker with data science dependencies.

    Common data science stack:
    - pandas: Data manipulation
    - numpy: Numerical operations
    - scipy: Scientific computing
    - matplotlib: Plotting
    """
    from datetime import datetime

    import matplotlib
    import numpy as np
    import pandas as pd
    import scipy

    data = input_data.get("data", [[1, 2], [3, 4], [5, 6]])

    # create DataFrame and compute statistics
    df = pd.DataFrame(data, columns=["A", "B"])
    stats = {
        "mean": df.mean().to_dict(),
        "std": df.std().to_dict(),
        "sum": df.sum().to_dict(),
    }

    arr = np.array(data)
    numpy_result = {
        "shape": arr.shape,
        "mean": float(arr.mean()),
    }

    versions = {
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "matplotlib": matplotlib.__version__,
    }

    return {
        "status": "success",
        "stats": stats,
        "numpy_result": numpy_result,
        "versions": versions,
        "timestamp": datetime.now().isoformat(),
    }


# worker with no external dependencies
@Endpoint(
    name="01_04_deps_minimal",
    cpu=CpuInstanceType.CPU3C_1_2,
    workers=(0, 3),
)
async def minimal_process(input_data: dict) -> dict:
    """
    Worker with NO external dependencies.

    Benefits:
    - Fastest cold start
    - Smallest container size
    - No dependency conflicts
    - Best for simple operations
    """
    import re
    from datetime import datetime

    text = input_data.get("text", "")

    word_count = len(text.split())
    char_count = len(text)
    uppercase_count = sum(1 for c in text if c.isupper())

    result = {
        "text_analysis": {
            "word_count": word_count,
            "char_count": char_count,
            "uppercase_count": uppercase_count,
            "has_numbers": bool(re.search(r"\d", text)),
        },
        "python_version": f"3.{__import__('sys').version_info.minor}",
        "timestamp": datetime.now().isoformat(),
    }

    return {
        "status": "success",
        "result": result,
        "message": "No external dependencies needed!",
    }


if __name__ == "__main__":
    import asyncio

    async def test():
        print("\n=== Testing Data Dependencies ===")
        data_result = await process_data({"data": [[1, 2], [3, 4], [5, 6]]})
        print(f"Result: {data_result}\n")

        print("=== Testing Minimal Dependencies ===")
        minimal_result = await minimal_process({"text": "Hello World 123"})
        print(f"Result: {minimal_result}\n")

    asyncio.run(test())
