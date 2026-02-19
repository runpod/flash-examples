# GPU worker for ML inference (sentiment classification).
# Part of the mixed CPU/GPU pipeline example.
# Run with: flash run
# Test directly: python gpu_worker.py
from runpod_flash import GpuGroup, LiveServerless, remote

gpu_config = LiveServerless(
    name="01_03_mixed_inference",
    gpus=[GpuGroup.ADA_24],
    workersMin=0,
    workersMax=3,
    idleTimeout=5,
)


@remote(resource_config=gpu_config, dependencies=["torch"])
async def gpu_inference(input_data: dict) -> dict:
    """GPU inference: mock sentiment classification."""
    import random
    from datetime import datetime

    import torch

    cleaned_text = input_data.get("cleaned_text", "")
    word_count = input_data.get("word_count", 0)

    gpu_available = torch.cuda.is_available()
    if gpu_available:
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    else:
        gpu_name = "No GPU (running locally)"
        gpu_memory = 0

    predictions = []
    positive_words = ["good", "great", "excellent", "love", "best", "happy", "wonderful"]
    negative_words = ["bad", "terrible", "worst", "hate", "poor", "awful", "horrible"]
    text_lower = cleaned_text.lower()

    positive_score = sum(1 for word in positive_words if word in text_lower)
    negative_score = sum(1 for word in negative_words if word in text_lower)

    if positive_score > negative_score:
        predictions = [
            {"label": "positive", "confidence": 0.75 + random.uniform(0, 0.24)},
            {"label": "neutral", "confidence": random.uniform(0.05, 0.15)},
            {"label": "negative", "confidence": random.uniform(0.01, 0.10)},
        ]
    elif negative_score > positive_score:
        predictions = [
            {"label": "negative", "confidence": 0.75 + random.uniform(0, 0.24)},
            {"label": "neutral", "confidence": random.uniform(0.05, 0.15)},
            {"label": "positive", "confidence": random.uniform(0.01, 0.10)},
        ]
    else:
        predictions = [
            {"label": "neutral", "confidence": 0.60 + random.uniform(0, 0.30)},
            {"label": "positive", "confidence": random.uniform(0.10, 0.30)},
            {"label": "negative", "confidence": random.uniform(0.10, 0.30)},
        ]

    total = sum(p["confidence"] for p in predictions)
    for p in predictions:
        p["confidence"] = round(p["confidence"] / total, 4)

    if gpu_available:
        dummy_tensor = torch.randn(100, 100, device="cuda")
        _ = torch.matmul(dummy_tensor, dummy_tensor)

    return {
        "status": "success",
        "predictions": predictions,
        "model_info": {
            "model_type": "sentiment_classifier",
            "version": "1.0.0",
            "gpu_name": gpu_name,
            "gpu_memory_gb": round(gpu_memory, 2) if gpu_memory else 0,
        },
        "input_stats": {
            "cleaned_text": cleaned_text[:100] + "..." if len(cleaned_text) > 100 else cleaned_text,
            "word_count": word_count,
        },
        "timestamp": datetime.now().isoformat(),
        "worker_type": "GPU Inference",
    }


if __name__ == "__main__":
    import asyncio

    test_payload = {
        "cleaned_text": "This is a great product! I love it.",
        "word_count": 8,
    }
    print(f"Testing GPU inference with payload: {test_payload}")
    result = asyncio.run(gpu_inference(test_payload))
    print(f"Result: {result}")
