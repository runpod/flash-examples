# Kimi-K2-Instruct inference via vLLM on 8xH100 GPUs.
# serves as the LLM backend for the code review agent.
# run with: flash run
# test directly: python gpu_worker.py
from runpod_flash import Endpoint, GpuType


@Endpoint(
    name="02_02_kimi_k2_gpu",
    gpu=GpuType.NVIDIA_H100_80GB_HBM3,
    gpu_count=8,
    workers=(0, 1),
    idle_timeout=600,
    dependencies=["vllm", "torch"],
)
class KimiK2:
    """Kimi-K2-Instruct LLM served via vLLM with W4A16 quantization."""

    def __init__(self):
        from vllm import LLM

        self.model_id = "RedHatAI/Kimi-K2-Instruct-quantized.w4a16"
        self.engine = LLM(
            model=self.model_id,
            tensor_parallel_size=8,
            gpu_memory_utilization=0.95,
            max_model_len=8192,
            distributed_executor_backend="ray",
        )
        self.tokenizer = self.engine.get_tokenizer()

    async def generate(self, input_data: dict) -> dict:
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
            prompt = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )

            sampling_params = SamplingParams(
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )

            outputs = self.engine.generate([prompt], sampling_params)
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

    async def health(self, input_data: dict) -> dict:
        """
        Check model loading status.

        Returns:
            status: str - "ready" or "error"
            model: str - Model identifier
            quantization: str - Quantization method
            gpu_count: int - Number of GPUs
        """
        return {
            "status": "ready",
            "model": self.model_id,
            "quantization": "W4A16",
            "gpu_count": 8,
        }


if __name__ == "__main__":
    import asyncio

    worker = KimiK2()

    print("Testing health check...")
    result = asyncio.run(worker.health({}))
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
    result = asyncio.run(worker.generate(test_payload))
    if result["status"] == "success":
        print(f"Generated: {result['text']}")
        print(f"Usage: {result['usage']}")
    else:
        print(f"Error: {result}")
