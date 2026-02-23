# GPU worker using a custom Docker image for serverless deployment.
# Demonstrates deploying pre-built containers to RunPod via Flash.
# Run with: flash run
# Test directly: python gpu_worker.py
import logging

from runpod_flash import GpuGroup, LiveServerless, ServerlessEndpoint, remote

logger = logging.getLogger(__name__)

# --- Local Development ---
# LiveServerless runs your code on RunPod's managed infrastructure.
# Flash installs dependencies and ships your code automatically.
local_config = LiveServerless(
    name="03_02_docker_local",
    gpus=[GpuGroup.ADA_24],
    workersMin=0,
    workersMax=3,
    idleTimeout=5,
)


@remote(resource_config=local_config, dependencies=["torch"])
async def gpu_inference_managed(input_data: dict) -> dict:
    """
    GPU inference using Flash's managed infrastructure.

    Flash handles packaging, Docker image creation, and deployment.
    Use this approach when you don't need a custom Docker image.

    Input:
        prompt: str - Text prompt to process
    Returns:
        result with GPU info and processed prompt
    """
    from datetime import datetime

    import torch

    prompt = input_data.get("prompt", "Hello from managed worker!")

    gpu_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if gpu_available else "No GPU"
    gpu_memory = (
        torch.cuda.get_device_properties(0).total_memory / (1024**3)
        if gpu_available
        else 0
    )

    return {
        "status": "success",
        "mode": "managed",
        "prompt": prompt,
        "gpu_info": {
            "available": gpu_available,
            "name": gpu_name,
            "memory_gb": round(gpu_memory, 2),
        },
        "timestamp": datetime.now().isoformat(),
    }


# --- Production with Custom Docker Image ---
# ServerlessEndpoint lets you bring your own Docker image.
# The image must implement the RunPod serverless handler protocol.
# See: https://github.com/runpod/runpod-python
docker_config = ServerlessEndpoint(
    name="03_02_docker_custom",
    dockerImage="runpod/worker-v1-vllm-v1:stable-cuda12.8.1",
    gpuIds=["NVIDIA GeForce RTX 4090"],
    workersMin=0,
    workersMax=3,
    idleTimeout=300,
    env={
        "MODEL_NAME": "microsoft/Phi-3-mini-4k-instruct",
        "MAX_MODEL_LEN": "4096",
    },
)


@remote(resource_config=docker_config)
async def gpu_inference_docker(input_data: dict) -> dict:
    """
    GPU inference using a custom Docker image.

    This function's code runs INSIDE the Docker container specified by
    `dockerImage` in the ServerlessEndpoint config. The container must
    implement the RunPod handler protocol.

    When deployed, RunPod pulls the Docker image, starts the container,
    and routes requests to it. Your function body defines the handler logic.

    Input:
        prompt: str - Text prompt to generate from
        max_tokens: int - Maximum tokens to generate (default: 128)
    Returns:
        Generated text from the model running in the container
    """
    prompt = input_data.get("prompt", "What is serverless computing?")
    max_tokens = input_data.get("max_tokens", 128)

    return {
        "prompt": prompt,
        "max_tokens": max_tokens,
        "sampling_params": {
            "temperature": 0.7,
            "top_p": 0.9,
        },
    }


# --- Custom Docker Image with System Dependencies ---
# Use a custom image when you need specific system libraries,
# CUDA versions, or pre-installed ML frameworks.
custom_system_config = ServerlessEndpoint(
    name="03_02_docker_system",
    dockerImage="runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04",
    gpuIds=["NVIDIA GeForce RTX 4090"],
    workersMin=0,
    workersMax=2,
    idleTimeout=300,
    env={
        "CUDA_VISIBLE_DEVICES": "0",
    },
)


@remote(resource_config=custom_system_config)
async def gpu_custom_cuda(input_data: dict) -> dict:
    """
    GPU worker running on a custom PyTorch/CUDA Docker image.

    This uses RunPod's official PyTorch image with CUDA 12.4.1,
    ideal when you need a specific CUDA version or system libraries
    that are hard to install at runtime.

    Input:
        operation: str - "matmul", "fft", or "info" (default: "info")
        size: int - Matrix/tensor size (default: 1000)
    Returns:
        Operation result with timing and GPU details
    """
    import time

    import torch

    operation = input_data.get("operation", "info")
    size = input_data.get("size", 1000)

    if operation == "info":
        return {
            "status": "success",
            "cuda_version": torch.version.cuda,
            "pytorch_version": torch.__version__,
            "gpu_available": torch.cuda.is_available(),
            "gpu_name": torch.cuda.get_device_name(0)
            if torch.cuda.is_available()
            else None,
        }

    device = "cuda" if torch.cuda.is_available() else "cpu"

    if operation == "matmul":
        a = torch.randn(size, size, device=device)
        b = torch.randn(size, size, device=device)
        torch.cuda.synchronize() if device == "cuda" else None
        start = time.perf_counter()
        _ = torch.matmul(a, b)
        torch.cuda.synchronize() if device == "cuda" else None
        elapsed = time.perf_counter() - start
        return {
            "status": "success",
            "operation": "matmul",
            "size": f"{size}x{size}",
            "elapsed_ms": round(elapsed * 1000, 2),
            "device": device,
        }

    if operation == "fft":
        signal = torch.randn(size, size, device=device)
        torch.cuda.synchronize() if device == "cuda" else None
        start = time.perf_counter()
        _ = torch.fft.fft2(signal)
        torch.cuda.synchronize() if device == "cuda" else None
        elapsed = time.perf_counter() - start
        return {
            "status": "success",
            "operation": "fft2",
            "size": f"{size}x{size}",
            "elapsed_ms": round(elapsed * 1000, 2),
            "device": device,
        }

    return {"status": "error", "error": f"Unknown operation: {operation}"}


if __name__ == "__main__":
    import asyncio

    async def test():
        print("=== Test 1: Managed Infrastructure ===")
        result = await gpu_inference_managed({"prompt": "Testing managed worker"})
        print(f"Result: {result}\n")

        print("=== Test 2: Custom Docker Image (vLLM) ===")
        result = await gpu_inference_docker(
            {"prompt": "Explain GPUs", "max_tokens": 64}
        )
        print(f"Result: {result}\n")

        print("=== Test 3: Custom CUDA Image (info) ===")
        result = await gpu_custom_cuda({"operation": "info"})
        print(f"Result: {result}\n")

        print("=== Test 4: Custom CUDA Image (matmul) ===")
        result = await gpu_custom_cuda({"operation": "matmul", "size": 512})
        print(f"Result: {result}\n")

    asyncio.run(test())
