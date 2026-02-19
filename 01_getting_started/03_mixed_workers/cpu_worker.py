# CPU workers for text preprocessing and postprocessing.
# Part of the mixed CPU/GPU pipeline example.
# Run with: flash run
# Test directly: python cpu_worker.py
from runpod_flash import CpuInstanceType, CpuLiveServerless, remote

cpu_config = CpuLiveServerless(
    name="01_03_mixed_workers_cpu",
    instanceIds=[CpuInstanceType.CPU3G_2_8],
    idleTimeout=3,
)


@remote(resource_config=cpu_config)
async def preprocess_text(input_data: dict) -> dict:
    """Preprocess text: cleaning and tokenization (cheap CPU work)."""
    import re
    from datetime import datetime

    text = input_data.get("text", "")

    cleaned_text = text.strip()
    cleaned_text = re.sub(r"\s+", " ", cleaned_text)
    cleaned_text = re.sub(r"[^\w\s.,!?-]", "", cleaned_text)

    words = cleaned_text.split()
    sentences = len(re.split(r"[.!?]+", cleaned_text))

    return {
        "status": "success",
        "original_text": text,
        "cleaned_text": cleaned_text,
        "word_count": len(words),
        "sentence_count": sentences,
        "char_count": len(cleaned_text),
        "timestamp": datetime.now().isoformat(),
        "worker_type": "CPU Preprocessing",
    }


@remote(resource_config=cpu_config)
async def postprocess_results(input_data: dict) -> dict:
    """Postprocess GPU results: formatting and aggregation (cheap CPU work)."""
    from datetime import datetime

    predictions = input_data.get("predictions", [])
    original_text = input_data.get("original_text", "")
    metadata = input_data.get("metadata", {})

    if predictions:
        top_prediction = max(predictions, key=lambda x: x["confidence"])
        confidence_level = (
            "high"
            if top_prediction["confidence"] > 0.8
            else "medium"
            if top_prediction["confidence"] > 0.5
            else "low"
        )
    else:
        top_prediction = None
        confidence_level = "none"

    return {
        "status": "success",
        "text_preview": original_text[:100] + "..." if len(original_text) > 100 else original_text,
        "classification": {
            "label": top_prediction["label"] if top_prediction else "unknown",
            "confidence": top_prediction["confidence"] if top_prediction else 0,
            "confidence_level": confidence_level,
        },
        "all_predictions": predictions,
        "metadata": metadata,
        "processing_pipeline": {
            "steps": ["preprocessing", "gpu_inference", "postprocessing"],
            "completed_at": datetime.now().isoformat(),
        },
        "worker_type": "CPU Postprocessing",
    }


if __name__ == "__main__":
    import asyncio

    async def test_workers():
        print("\n=== Testing Preprocessing ===")
        preprocess_result = await preprocess_text(
            {"text": "This is a test message with  extra   spaces and CAPS!"}
        )
        print(f"Result: {preprocess_result}\n")

        print("=== Testing Postprocessing ===")
        postprocess_result = await postprocess_results(
            {
                "predictions": [
                    {"label": "positive", "confidence": 0.9},
                    {"label": "negative", "confidence": 0.1},
                ],
                "original_text": "This is a test message",
                "metadata": {"word_count": 5},
            }
        )
        print(f"Result: {postprocess_result}\n")

    asyncio.run(test_workers())
