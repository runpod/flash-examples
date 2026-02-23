# CPU worker that calls RunPod's public serverless endpoints.
# Demonstrates using the RunPod SDK to call pre-deployed public endpoints.
# Run with: flash run
# Test directly: python cpu_worker.py
import logging
import os

from runpod_flash import CpuInstanceType, CpuLiveServerless, remote

logger = logging.getLogger(__name__)

cpu_config = CpuLiveServerless(
    name="03_03_public_endpoints_cpu",
    instanceIds=[CpuInstanceType.CPU3C_1_2],
    workersMin=0,
    workersMax=3,
    idleTimeout=5,
)


@remote(resource_config=cpu_config, dependencies=["runpod"])
async def call_llm_endpoint(input_data: dict) -> dict:
    """
    Call a RunPod serverless endpoint using the RunPod SDK.

    RunPod public endpoints are pre-deployed, always-available serverless
    endpoints for common AI workloads. You can also call your own deployed
    endpoints using the same SDK pattern.

    Input:
        endpoint_id: str - RunPod endpoint ID (from console or flash deploy)
        prompt: str - Text prompt to send
        max_tokens: int - Max tokens to generate (default: 256)
        mode: str - "sync" for blocking, "async" for fire-and-forget (default: "sync")
    Returns:
        Response from the serverless endpoint
    """
    import runpod

    api_key = os.getenv("RUNPOD_API_KEY")
    if not api_key:
        return {"status": "error", "error": "RUNPOD_API_KEY not set"}

    runpod.api_key = api_key

    endpoint_id = input_data.get("endpoint_id", "")
    if not endpoint_id:
        return {
            "status": "error",
            "error": "endpoint_id is required. Get it from the RunPod console or flash deploy output.",
        }

    prompt = input_data.get("prompt", "Hello!")
    max_tokens = input_data.get("max_tokens", 256)
    mode = input_data.get("mode", "sync")

    endpoint = runpod.Endpoint(endpoint_id)
    request_payload = {
        "input": {
            "prompt": prompt,
            "max_tokens": max_tokens,
        }
    }

    try:
        if mode == "async":
            # Fire-and-forget: returns a job ID immediately
            run_request = endpoint.run(request_payload)
            return {
                "status": "submitted",
                "job_id": run_request.job_id,
                "message": "Job submitted. Use check_job_status to poll for results.",
            }

        # Synchronous: blocks until the job completes (up to timeout)
        run_request = endpoint.run_sync(request_payload, timeout=120)
        return {
            "status": "success",
            "output": run_request,
        }

    except runpod.error.QueryError as e:
        return {"status": "error", "error": f"Query error: {e}"}
    except TimeoutError:
        return {"status": "error", "error": "Request timed out after 120s"}
    except Exception as e:
        logger.error("Endpoint call failed", exc_info=True)
        return {"status": "error", "error": str(e)}


@remote(resource_config=cpu_config, dependencies=["httpx"])
async def check_job_status(input_data: dict) -> dict:
    """
    Check the status of an async job on a RunPod endpoint.

    Use this after submitting a job with mode="async" to poll for results.
    Uses the RunPod REST API directly since the SDK's Job object is not
    available across separate function calls.

    Input:
        endpoint_id: str - RunPod endpoint ID
        job_id: str - Job ID from the async submission
    Returns:
        Job status and output (if completed)
    """
    import httpx

    api_key = os.getenv("RUNPOD_API_KEY")
    if not api_key:
        return {"status": "error", "error": "RUNPOD_API_KEY not set"}

    endpoint_id = input_data.get("endpoint_id", "")
    job_id = input_data.get("job_id", "")

    if not endpoint_id or not job_id:
        return {"status": "error", "error": "endpoint_id and job_id are required"}

    url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return {
                "status": "success",
                "job_id": job_id,
                "job_status": data.get("status"),
                "output": data.get("output"),
            }
    except Exception as e:
        logger.error("Status check failed", exc_info=True)
        return {"status": "error", "error": str(e)}


@remote(resource_config=cpu_config, dependencies=["runpod"])
async def call_endpoint_with_webhook(input_data: dict) -> dict:
    """
    Call a RunPod endpoint with a webhook for completion notification.

    Instead of polling, RunPod calls your webhook URL when the job finishes.
    Ideal for long-running tasks where you don't want to hold a connection.

    Input:
        endpoint_id: str - RunPod endpoint ID
        prompt: str - Text prompt to send
        webhook_url: str - URL to receive completion notification
    Returns:
        Job submission confirmation with job_id
    """
    import runpod

    api_key = os.getenv("RUNPOD_API_KEY")
    if not api_key:
        return {"status": "error", "error": "RUNPOD_API_KEY not set"}

    runpod.api_key = api_key

    endpoint_id = input_data.get("endpoint_id", "")
    prompt = input_data.get("prompt", "Hello!")
    webhook_url = input_data.get("webhook_url", "")

    if not endpoint_id:
        return {"status": "error", "error": "endpoint_id is required"}
    if not webhook_url:
        return {"status": "error", "error": "webhook_url is required"}

    endpoint = runpod.Endpoint(endpoint_id)

    try:
        run_request = endpoint.run(
            {
                "input": {"prompt": prompt},
                "webhook": webhook_url,
            }
        )
        return {
            "status": "submitted",
            "job_id": run_request.job_id,
            "webhook_url": webhook_url,
            "message": "Job submitted. Results will be POSTed to webhook_url on completion.",
        }
    except Exception as e:
        logger.error("Webhook submission failed", exc_info=True)
        return {"status": "error", "error": str(e)}


@remote(resource_config=cpu_config, dependencies=["httpx"])
async def call_endpoint_raw(input_data: dict) -> dict:
    """
    Call a RunPod serverless endpoint using raw HTTP (without the SDK).

    Demonstrates the underlying REST API for environments where the
    RunPod SDK is not available, or for custom HTTP integrations.

    Input:
        endpoint_id: str - RunPod endpoint ID
        prompt: str - Text prompt to send
        max_tokens: int - Max tokens to generate (default: 256)
    Returns:
        Raw API response from RunPod
    """
    import httpx

    api_key = os.getenv("RUNPOD_API_KEY")
    if not api_key:
        return {"status": "error", "error": "RUNPOD_API_KEY not set"}

    endpoint_id = input_data.get("endpoint_id", "")
    if not endpoint_id:
        return {"status": "error", "error": "endpoint_id is required"}

    prompt = input_data.get("prompt", "Hello!")
    max_tokens = input_data.get("max_tokens", 256)

    url = f"https://api.runpod.ai/v2/{endpoint_id}/runsync"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "input": {
            "prompt": prompt,
            "max_tokens": max_tokens,
        }
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return {
                "status": "success",
                "output": response.json(),
            }
    except httpx.HTTPStatusError as e:
        return {
            "status": "error",
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
        }
    except Exception as e:
        logger.error("Raw API call failed", exc_info=True)
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    import asyncio

    async def test():
        # These tests require a valid RUNPOD_API_KEY and endpoint_id
        endpoint_id = os.getenv("TEST_ENDPOINT_ID", "your-endpoint-id-here")

        print("=== Test 1: Sync Call ===")
        result = await call_llm_endpoint(
            {
                "endpoint_id": endpoint_id,
                "prompt": "What is RunPod?",
                "max_tokens": 128,
                "mode": "sync",
            }
        )
        print(f"Result: {result}\n")

        print("=== Test 2: Async Call + Status Check ===")
        result = await call_llm_endpoint(
            {
                "endpoint_id": endpoint_id,
                "prompt": "Explain serverless computing.",
                "mode": "async",
            }
        )
        print(f"Submitted: {result}")
        if result.get("job_id"):
            status = await check_job_status(
                {"endpoint_id": endpoint_id, "job_id": result["job_id"]}
            )
            print(f"Status: {status}\n")

        print("=== Test 3: Raw HTTP Call ===")
        result = await call_endpoint_raw(
            {
                "endpoint_id": endpoint_id,
                "prompt": "Hello from raw HTTP!",
                "max_tokens": 64,
            }
        )
        print(f"Result: {result}\n")

    asyncio.run(test())
