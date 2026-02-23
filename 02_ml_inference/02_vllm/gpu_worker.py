# vLLM inference worker using RunPod's official vLLM Docker image.
# Deploys an OpenAI-compatible LLM endpoint on serverless GPUs.
# Run with: flash run
# Test directly: python gpu_worker.py
import logging

from runpod_flash import ServerlessEndpoint, remote

logger = logging.getLogger(__name__)

# --- Llama 3.1 8B via vLLM ---
# Uses RunPod's official vLLM worker image, which provides:
# - OpenAI-compatible /v1/chat/completions and /v1/completions
# - Automatic tensor parallelism for multi-GPU
# - Continuous batching for high throughput
# - KV cache management
#
# Environment variables configure the vLLM server inside the container.
# See: https://github.com/runpod-workers/worker-vllm
llama_config = ServerlessEndpoint(
    name="02_02_vllm_llama",
    dockerImage="runpod/worker-v1-vllm-v1:stable-cuda12.8.1",
    gpuIds=["NVIDIA GeForce RTX 4090"],
    workersMin=0,
    workersMax=3,
    idleTimeout=300,
    env={
        "MODEL_NAME": "meta-llama/Llama-3.1-8B-Instruct",
        "MAX_MODEL_LEN": "8192",
        "DTYPE": "half",
        "GPU_MEMORY_UTILIZATION": "0.90",
        "DEFAULT_BATCH_SIZE": "1",
        # HuggingFace token for gated models
        # "HF_TOKEN": "hf_xxxxx",
    },
)


@remote(resource_config=llama_config)
async def llama_chat(input_data: dict) -> dict:
    """
    Chat completion using Llama 3.1 8B via vLLM.

    The RunPod vLLM worker accepts OpenAI-compatible request formats.
    This function sends the request payload to the vLLM container.

    Input:
        messages: list[dict] - Chat messages in OpenAI format
            [{"role": "user", "content": "Hello!"}]
        max_tokens: int - Max tokens to generate (default: 512)
        temperature: float - Sampling temperature (default: 0.7)
        top_p: float - Nucleus sampling (default: 0.9)
        stream: bool - Enable streaming (default: false)
    Returns:
        OpenAI-compatible chat completion response
    """
    messages = input_data.get("messages", [{"role": "user", "content": "Hello!"}])
    max_tokens = input_data.get("max_tokens", 512)
    temperature = input_data.get("temperature", 0.7)
    top_p = input_data.get("top_p", 0.9)
    stream = input_data.get("stream", False)

    # vLLM worker expects OpenAI-compatible format
    return {
        "openai_route": "/v1/chat/completions",
        "openai_input": {
            "model": "meta-llama/Llama-3.1-8B-Instruct",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": stream,
        },
    }


# --- Mistral 7B via vLLM ---
# Demonstrates deploying a second model with different configuration.
mistral_config = ServerlessEndpoint(
    name="02_02_vllm_mistral",
    dockerImage="runpod/worker-v1-vllm-v1:stable-cuda12.8.1",
    gpuIds=["NVIDIA GeForce RTX 4090"],
    workersMin=0,
    workersMax=2,
    idleTimeout=300,
    env={
        "MODEL_NAME": "mistralai/Mistral-7B-Instruct-v0.3",
        "MAX_MODEL_LEN": "8192",
        "DTYPE": "half",
        "GPU_MEMORY_UTILIZATION": "0.90",
    },
)


@remote(resource_config=mistral_config)
async def mistral_chat(input_data: dict) -> dict:
    """
    Chat completion using Mistral 7B Instruct via vLLM.

    Same OpenAI-compatible interface, different model.

    Input:
        messages: list[dict] - Chat messages in OpenAI format
        max_tokens: int - Max tokens to generate (default: 512)
        temperature: float - Sampling temperature (default: 0.7)
    Returns:
        OpenAI-compatible chat completion response
    """
    messages = input_data.get("messages", [{"role": "user", "content": "Hello!"}])
    max_tokens = input_data.get("max_tokens", 512)
    temperature = input_data.get("temperature", 0.7)

    return {
        "openai_route": "/v1/chat/completions",
        "openai_input": {
            "model": "mistralai/Mistral-7B-Instruct-v0.3",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
    }


# --- Text Completion (non-chat) ---
# vLLM also supports raw text completions.
@remote(resource_config=llama_config)
async def text_completion(input_data: dict) -> dict:
    """
    Raw text completion using vLLM's /v1/completions endpoint.

    Useful for code generation, text continuation, and non-conversational tasks.

    Input:
        prompt: str - Text prompt to complete
        max_tokens: int - Max tokens to generate (default: 256)
        temperature: float - Sampling temperature (default: 0.8)
        stop: list[str] - Stop sequences (optional)
    Returns:
        OpenAI-compatible text completion response
    """
    prompt = input_data.get("prompt", "def fibonacci(n):")
    max_tokens = input_data.get("max_tokens", 256)
    temperature = input_data.get("temperature", 0.8)
    stop = input_data.get("stop", [])

    return {
        "openai_route": "/v1/completions",
        "openai_input": {
            "model": "meta-llama/Llama-3.1-8B-Instruct",
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stop": stop if stop else None,
        },
    }


if __name__ == "__main__":
    import asyncio

    async def test():
        print("=== Test 1: Llama 3.1 Chat ===")
        result = await llama_chat(
            {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is vLLM and why is it fast?"},
                ],
                "max_tokens": 256,
            }
        )
        print(f"Result: {result}\n")

        print("=== Test 2: Mistral Chat ===")
        result = await mistral_chat(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "Explain serverless computing in 2 sentences.",
                    },
                ],
                "max_tokens": 128,
            }
        )
        print(f"Result: {result}\n")

        print("=== Test 3: Text Completion ===")
        result = await text_completion(
            {
                "prompt": "# Python function to check if a number is prime\ndef is_prime(n):",
                "max_tokens": 128,
                "stop": ["\n\n"],
            }
        )
        print(f"Result: {result}\n")

    asyncio.run(test())
