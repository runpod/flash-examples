
import asyncio
import logging

from runpod_flash import GpuGroup, LiveServerless, remote

logger = logging.getLogger(__name__)

gpu_config = LiveServerless(
    name="02_02_text_generation_gpu",  # Name shown for this serverless worker deployment.
    gpus=[GpuGroup.ADA_24],  # Request an NVIDIA L4 / 24GB-class GPU (Ada 24GB group).
    workersMin=0,  # Keep 0 warm workers to reduce idle cost.
    workersMax=3,  # Scale out to at most 3 workers under load.
    idleTimeout=30,  # Keep workers running for n seconds before scaling back down
)

@remote(
    resource_config=gpu_config,
    dependencies=["vllm"],  # Extra package(s) installed in the worker image at runtime.
)
class MinimalVLLM:
    _instance = None

    def __new__(cls):
        if cls._instance == None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self.MODEL = "Qwen/Qwen2.5-3B-Instruct"
        self.SYSTEM_PROMPT = (
            "You are a pirate-style rewriter. Rewrite user text in fun pirate voice. "
            "Keep original meaning. Keep it concise. Output only the rewritten text."
        )

        from vllm import LLM, SamplingParams
        from transformers import AutoTokenizer
        import os

        os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"  # Safer multiprocessing mode for CUDA workers.

        self.llm = LLM(
            model=self.MODEL,  # Hugging Face model id loaded by vLLM.
            enforce_eager=True,  # Skip CUDA graph capture; faster cold start, usually lower throughput.
            gpu_memory_utilization=0.6,  # Reserve ~60% of GPU memory for model/kv cache.
            max_model_len=1024,  # Max context window handled per request.
        )
        self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL)
        self.sampling = SamplingParams(
            temperature=0.6,  # Moderate creativity while preserving meaning.
            top_p=0.9,  # Nucleus sampling to avoid low-probability tails.
            max_tokens=500,  # Cap response length.
        )
        print("vLLM initialized successfully")

    def piratize(self, text: str) -> str:
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ]
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,  # Return plain prompt text for vLLM.
            add_generation_prompt=True,  # Append assistant prefix so model continues as assistant.
        )
        out = self.llm.generate([prompt], self.sampling)
        return out[0].outputs[0].text.strip()

    def generate_single(self, prompt: str) -> str:
        return self.piratize(prompt)


async def piratize_text(text: str) -> str:
    llm = MinimalVLLM()
    return await llm.generate_single(text)


if __name__ == "__main__":
    sample = "Want to go get something to eat? man, I sure do enjoy sailing."
    print(asyncio.run(piratize_text(sample)))
