"""Concurrent handler example.

Demonstrates max_concurrency for QB endpoints. Simulates a vLLM-style
inference server where a single GPU model handles multiple requests
concurrently via async batching.

With max_concurrency=5, the Runpod worker processes up to 5 jobs
simultaneously on the same GPU. The handler must be async so the
event loop can interleave requests while each awaits model inference.
"""

import asyncio

from runpod_flash import Endpoint, GpuGroup


@Endpoint(name="concurrent-worker", gpu=GpuGroup.ADA_24, max_concurrency=5)
async def generate(prompt: str, max_tokens: int = 128) -> dict:
    """Simulate async inference. Real usage would call vLLM/TGI engine here."""
    await asyncio.sleep(0.5)
    return {
        "prompt": prompt,
        "generated_text": f"Response to: {prompt}",
        "tokens_generated": max_tokens,
    }
