from tetra_rp import CpuInstanceType, CpuLiveServerless, remote

# Worker with data science dependencies
data_config = CpuLiveServerless(
    name="01_04_deps_data",
    instanceIds=[CpuInstanceType.CPU3C_8_16],
    workersMin=0,
    workersMax=3,
)

# Worker with minimal dependencies
minimal_config = CpuLiveServerless(
    name="01_04_deps_minimal",
    instanceIds=[CpuInstanceType.CPU3C_1_2],
    workersMin=0,
    workersMax=3,
)


@remote(
    resource_config=data_config,
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

    # Create DataFrame and compute statistics
    df = pd.DataFrame(data, columns=["A", "B"])
    stats = {
        "mean": df.mean().to_dict(),
        "std": df.std().to_dict(),
        "sum": df.sum().to_dict(),
    }

    # Numpy operation
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


@remote(resource_config=minimal_config)  # No dependencies!
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

    # Built-in operations only
    word_count = len(text.split())
    char_count = len(text)
    uppercase_count = sum(1 for c in text if c.isupper())

    # JSON manipulation
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

    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv())  # Find and load root .env file

    async def test():
        print("\n=== Testing Data Dependencies ===")
        data_result = await process_data({"data": [[1, 2], [3, 4], [5, 6]]})
        print(f"Result: {data_result}\n")

        print("=== Testing Minimal Dependencies ===")
        minimal_result = await minimal_process({"text": "Hello World 123"})
        print(f"Result: {minimal_result}\n")

    asyncio.run(test())
