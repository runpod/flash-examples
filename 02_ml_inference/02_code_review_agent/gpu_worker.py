# Kimi-K2-Instruct inference via vLLM on 8xH100 GPUs.
# serves as the LLM backend for the code review agent.
# run with: flash run
# test directly: python gpu_worker.py
from runpod_flash import Endpoint, GpuType

MODEL_ID = "RedHatAI/Kimi-K2-Instruct-quantized.w4a16"
MAX_MODEL_LEN = 8192
TENSOR_PARALLEL_SIZE = 8
GPU_MEMORY_UTILIZATION = 0.95

# module-level state persists between invocations on the same worker pod.
# the entire module runs on the worker process, not just the function body.
_state = {}


def _get_engine():
    """Return the cached vLLM engine, initializing on first call."""
    if "engine" not in _state:
        from vllm import LLM

        _state["engine"] = LLM(
            model=MODEL_ID,
            tensor_parallel_size=TENSOR_PARALLEL_SIZE,
            gpu_memory_utilization=GPU_MEMORY_UTILIZATION,
            max_model_len=MAX_MODEL_LEN,
            distributed_executor_backend="ray",
        )
        _state["status"] = "ready"
    return _state["engine"]


@Endpoint(
    name="02_02_kimi_k2_gpu",
    gpu=GpuType.NVIDIA_H100_80GB_HBM3,
    gpu_count=8,
    workers=(0, 1),
    idle_timeout=600,
    dependencies=["vllm", "torch"],
)
async def generate(input_data: dict) -> dict:
    """
    Generate text using Kimi-K2-Instruct via vLLM.

    Input:
        messages: list[dict] - Chat messages with role and content
        max_tokens: int - Maximum tokens to generate (default: 4096)
        temperature: float - Sampling temperature (default: 0.1)
        top_p: float - Top-p sampling (default: 0.95)

    Returns:
        status: str - "success" or "error"
        text: str - Generated text
        usage: dict - Token usage stats
    """
    from vllm import SamplingParams

    messages = input_data.get("messages", [])
    if not messages:
        return {
            "status": "error",
            "error": "messages list is required and cannot be empty",
        }

    max_tokens = input_data.get("max_tokens", 4096)
    temperature = input_data.get("temperature", 0.1)
    top_p = input_data.get("top_p", 0.95)

    try:
        engine = _get_engine()
        tokenizer = engine.get_tokenizer()

        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        sampling_params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )

        outputs = engine.generate([prompt], sampling_params)
        output = outputs[0]
        generated_text = output.outputs[0].text

        return {
            "status": "success",
            "text": generated_text,
            "usage": {
                "prompt_tokens": len(output.prompt_token_ids),
                "completion_tokens": len(output.outputs[0].token_ids),
            },
        }

    except Exception as e:
        error_msg = str(e)
        if "out of memory" in error_msg.lower() or "oom" in error_msg.lower():
            return {
                "status": "error",
                "error": "Generation failed: OOM. Reduce diff size or max_tokens.",
                "detail": error_msg,
            }
        return {"status": "error", "error": error_msg}


@Endpoint(
    name="02_02_kimi_k2_gpu",
    gpu=GpuType.NVIDIA_H100_80GB_HBM3,
    gpu_count=8,
    dependencies=["vllm"],
)
async def health(input_data: dict) -> dict:
    """
    Check model loading status.

    Returns:
        status: str - "ready", "loading", or "error"
        model: str - Model identifier
        quantization: str - Quantization method
        gpu_count: int - Number of GPUs
    """
    try:
        _get_engine()
        return {
            "status": "ready",
            "model": MODEL_ID,
            "quantization": "W4A16",
            "gpu_count": TENSOR_PARALLEL_SIZE,
        }
    except Exception as e:
        if "engine" not in _state:
            return {
                "status": "loading",
                "model": MODEL_ID,
            }
        return {
            "status": "error",
            "model": MODEL_ID,
            "detail": str(e),
        }


if __name__ == "__main__":
    import asyncio

    print("Testing health check...")
    result = asyncio.run(health({}))
    print(f"Health: {result}\n")

    print("Testing generation...")
    test_payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2 + 2? Answer in one word."},
        ],
        "max_tokens": 32,
        "temperature": 0.0,
    }
    result = asyncio.run(generate(test_payload))
    if result["status"] == "success":
        print(f"Generated: {result['text']}")
        print(f"Usage: {result['usage']}")
    else:
        print(f"Error: {result}")
