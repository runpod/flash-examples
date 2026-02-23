# GPU worker that orchestrates calls to RunPod serverless endpoints.
# Demonstrates chaining endpoint calls within a GPU-accelerated pipeline.
# Run with: flash run
# Test directly: python gpu_worker.py
import logging
import os

from runpod_flash import GpuGroup, LiveServerless, remote

logger = logging.getLogger(__name__)

gpu_config = LiveServerless(
    name="03_03_public_endpoints_gpu",
    gpus=[GpuGroup.ADA_24],
    workersMin=0,
    workersMax=2,
    idleTimeout=5,
)


@remote(resource_config=gpu_config, dependencies=["runpod", "torch"])
async def gpu_pipeline_with_endpoint(input_data: dict) -> dict:
    """
    GPU pipeline that combines local GPU processing with a remote endpoint call.

    This demonstrates a common pattern: preprocess data locally on GPU,
    then send it to a specialized RunPod endpoint for inference.

    Input:
        endpoint_id: str - RunPod endpoint ID for the LLM
        text: str - Text to analyze
    Returns:
        Combined result from GPU processing and endpoint call
    """
    import time

    import runpod
    import torch

    api_key = os.getenv("RUNPOD_API_KEY")
    if not api_key:
        return {"status": "error", "error": "RUNPOD_API_KEY not set"}

    runpod.api_key = api_key

    endpoint_id = input_data.get("endpoint_id", "")
    text = input_data.get("text", "RunPod makes GPU computing accessible.")

    if not endpoint_id:
        return {"status": "error", "error": "endpoint_id is required"}

    # Step 1: Local GPU preprocessing (e.g., embeddings, tokenization)
    start = time.perf_counter()
    gpu_available = torch.cuda.is_available()
    device = "cuda" if gpu_available else "cpu"

    # Simulate GPU preprocessing (in production: compute embeddings, etc.)
    tokens = text.split()
    token_ids = torch.tensor(
        [hash(t) % 50000 for t in tokens], device=device, dtype=torch.float32
    )
    token_embedding = torch.nn.functional.normalize(token_ids.unsqueeze(0), dim=-1)
    embedding_norm = token_embedding.norm().item()
    preprocess_ms = (time.perf_counter() - start) * 1000

    # Step 2: Call remote endpoint for LLM inference
    start = time.perf_counter()
    endpoint = runpod.Endpoint(endpoint_id)
    try:
        result = endpoint.run_sync(
            {
                "input": {
                    "prompt": f"Summarize this text in one sentence: {text}",
                    "max_tokens": 128,
                }
            },
            timeout=120,
        )
        endpoint_ms = (time.perf_counter() - start) * 1000
        endpoint_output = result
    except Exception as e:
        endpoint_ms = (time.perf_counter() - start) * 1000
        endpoint_output = {"error": str(e)}

    return {
        "status": "success",
        "input_text": text,
        "preprocessing": {
            "device": device,
            "token_count": len(tokens),
            "embedding_norm": round(embedding_norm, 4),
            "elapsed_ms": round(preprocess_ms, 2),
        },
        "endpoint_result": {
            "output": endpoint_output,
            "elapsed_ms": round(endpoint_ms, 2),
        },
    }


@remote(resource_config=gpu_config, dependencies=["runpod", "torch"])
async def batch_endpoint_calls(input_data: dict) -> dict:
    """
    Send multiple requests to a RunPod endpoint concurrently.

    Demonstrates async batching: submit multiple jobs simultaneously
    and collect results. Useful for processing batches of data.

    Input:
        endpoint_id: str - RunPod endpoint ID
        prompts: list[str] - List of prompts to process
        max_tokens: int - Max tokens per response (default: 128)
    Returns:
        List of results from all concurrent endpoint calls
    """
    import time

    import runpod

    api_key = os.getenv("RUNPOD_API_KEY")
    if not api_key:
        return {"status": "error", "error": "RUNPOD_API_KEY not set"}

    runpod.api_key = api_key

    endpoint_id = input_data.get("endpoint_id", "")
    prompts = input_data.get("prompts", ["Hello!", "What is AI?"])
    max_tokens = input_data.get("max_tokens", 128)

    if not endpoint_id:
        return {"status": "error", "error": "endpoint_id is required"}

    endpoint = runpod.Endpoint(endpoint_id)

    # Submit all jobs asynchronously using endpoint.run()
    start = time.perf_counter()
    jobs = []
    for prompt in prompts:
        job = endpoint.run({"input": {"prompt": prompt, "max_tokens": max_tokens}})
        jobs.append({"job": job, "prompt": prompt})

    # Collect results using Job.output() which blocks until complete
    results = []
    for job_info in jobs:
        try:
            job = job_info["job"]
            output = job.output()
            results.append(
                {
                    "prompt": job_info["prompt"],
                    "job_id": job.job_id,
                    "status": "COMPLETED",
                    "output": output,
                }
            )
        except Exception as e:
            results.append(
                {
                    "prompt": job_info["prompt"],
                    "job_id": job_info["job"].job_id,
                    "status": "error",
                    "error": str(e),
                }
            )

    elapsed = (time.perf_counter() - start) * 1000

    return {
        "status": "success",
        "total_prompts": len(prompts),
        "results": results,
        "total_elapsed_ms": round(elapsed, 2),
    }


if __name__ == "__main__":
    import asyncio

    async def test():
        endpoint_id = os.getenv("TEST_ENDPOINT_ID", "your-endpoint-id-here")

        print("=== Test 1: GPU Pipeline + Endpoint ===")
        result = await gpu_pipeline_with_endpoint(
            {
                "endpoint_id": endpoint_id,
                "text": "RunPod provides serverless GPU computing for AI workloads.",
            }
        )
        print(f"Result: {result}\n")

        print("=== Test 2: Batch Endpoint Calls ===")
        result = await batch_endpoint_calls(
            {
                "endpoint_id": endpoint_id,
                "prompts": ["What is RunPod?", "Explain vLLM.", "What is Flash?"],
                "max_tokens": 64,
            }
        )
        print(f"Result: {result}\n")

    asyncio.run(test())
