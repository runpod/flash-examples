## LLM chat inference on a serverless GPU
# This example runs a small chat LLM (Llama 3.2 1B Instruct) on Runpod serverless GPUs
# using `transformers.pipeline`.
#
# Call it via the FastAPI endpoint (`POST /gpu/llm`) or run this module directly for
# a quick smoke test.
#
# Scaling behavior is controlled by the `LiveServerless` config below.
import os

from fastapi import APIRouter
from pydantic import BaseModel

from tetra_rp import (
    GpuGroup,
    LiveServerless,
    remote,
)

# Here, we'll define several variables that change the
# default behavior of our serverless endpoint. `workersMin` sets our endpoint
# to scale to 0 active containers; `workersMax` will allow our endpoint to run
# up to 3 workers in parallel as the endpoint receives more work. We also set
# an idle timeout of 5 minutes so that any active worker stays alive for 5
# minutes after completing a request.
#
# Hugging Face auth:
# Many `meta-llama/*` models are gated on Hugging Face. Local shell env vars are NOT
# automatically forwarded into serverless containers, so we pass `HF_TOKEN` via `env=...`
# so the remote worker can download the model.
_hf_token = os.getenv("HF_TOKEN")
_worker_env = {"HF_TOKEN": _hf_token} if _hf_token else {}
gpu_config = LiveServerless(
    name="02_01_text_generation_gpu_worker",
    gpus=[GpuGroup.ANY],  # Run on any GPU
    env=_worker_env,
    workersMin=0,
    workersMax=3,
    idleTimeout=5,
)


# Decorating our function with `remote` will package up the function code and
# deploy it on the infrastructure according to the passed input config. The
# results from the worker will be returned to your terminal. In this example
# the function will return a greeting to the input string passed in the `name`
# key. The code itself will run on a GPU worker, and information about the GPU
# the worker has access to will be included in the response.
# Declare worker dependencies so they're installed in the remote execution environment.
# (Local `requirements.txt` is not automatically shipped to the worker.)
@remote(
    resource_config=gpu_config,
    dependencies=[
        "torch",
        "transformers",
        "accelerate",
    ],
)
async def gpu_hello(
    input_data: dict,
) -> dict:
    """Generate one chat response using Llama 3.2 1B Instruct on a serverless GPU."""
    import os
    import platform
    from datetime import datetime

    import torch
    from transformers import pipeline

    gpu_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0)
    gpu_count = torch.cuda.device_count()
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)

    # Inputs:
    # - Simple: {"message": "...", "system_prompt": "...", "max_new_tokens": 512}
    # - Full chat: {"messages": [{"role": "...", "content": "..."}, ...], "max_new_tokens": 512}
    system_prompt = input_data.get(
        "system_prompt",
        "You are a helpful assistant chatbot who always responds in a friendly and helpful manner!",
    )
    message = input_data.get("message", "What is gpu?")
    messages = input_data.get("messages") or [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message},
    ]

    model_id = "meta-llama/Llama-3.2-1B-Instruct"

    # Hugging Face auth for gated repos:
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise RuntimeError("HF_TOKEN is required to download gated models (e.g. meta-llama/*).")

    pipe = pipeline(
        "text-generation",
        model=model_id,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        token=hf_token,
    )

    outputs = pipe(
        messages,
        max_new_tokens=int(input_data.get("max_new_tokens", 512)),
    )
    generated = outputs[0]["generated_text"]
    last = generated[-1] if isinstance(generated, list) and generated else generated
    assistant_message = last.get("content") if isinstance(last, dict) else str(last)
    print(assistant_message)

    return {
        "status": "success",
        "message": assistant_message,
        "worker_type": "GPU",
        "gpu_info": {
            "available": gpu_available,
            "name": gpu_name,
            "count": gpu_count,
            "memory_gb": round(
                gpu_memory,
                2,
            ),
        },
        "timestamp": datetime.now().isoformat(),
        "platform": platform.system(),
        "python_version": platform.python_version(),
    }


# We define a subrouter for our gpu worker so that our main router in `main.py`
# can attach it for routing gpu-specific requests.
gpu_router = APIRouter()


class MessageRequest(BaseModel):
    """Request model for GPU worker."""

    message: str = "What is gpu?"
    system_prompt: str = (
        "You are a helpful assistant chatbot who always responds in a friendly and helpful manner!"
    )
    max_new_tokens: int = 512


@gpu_router.post("/llm")
async def llm(
    request: MessageRequest,
):
    """Simple GPU worker endpoint."""
    result = await gpu_hello(
        {
            "message": request.message,
            "system_prompt": request.system_prompt,
            "max_new_tokens": request.max_new_tokens,
        }
    )
    return result


# This code is packaged up as a "worker" that will handle requests sent to the
# endpoint at /gpu/llm, but you can also trigger it directly by running
# python -m workers.gpu.endpoint
if __name__ == "__main__":
    import asyncio

    test_payload = {"message": "Testing GPU worker"}
    print(f"Testing GPU worker with payload: {test_payload}")
    result = asyncio.run(gpu_hello(test_payload))
    print(f"Result: {result}")
