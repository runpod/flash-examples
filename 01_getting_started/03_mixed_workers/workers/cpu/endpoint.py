from runpod_flash import CpuInstanceType, CpuLiveServerless, remote

# Preprocessing CPU worker (fast, cheap)
cpu_config = CpuLiveServerless(
    name="01_03_mixed_workers_cpu",
    instanceIds=[CpuInstanceType.CPU3G_2_8],  # Small instance - 2 vCPU, 8GB
    idleTimeout=3,
)


@remote(resource_config=cpu_config)
async def preprocess_text(input_data: dict) -> dict:
    """
    Preprocessing on CPU: cleaning and tokenization.

    Why CPU:
    - No ML operations
    - Fast text operations
    - 85% cheaper than GPU

    Note: Input validation handled by Pydantic at API layer
    """
    import re
    from datetime import datetime

    text = input_data.get("text", "")

    # Text cleaning
    cleaned_text = text.strip()
    cleaned_text = re.sub(r"\s+", " ", cleaned_text)  # Remove extra whitespace
    cleaned_text = re.sub(r"[^\w\s.,!?-]", "", cleaned_text)  # Remove special chars

    # Simple tokenization (word count, sentence count)
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
    """
    Postprocessing on CPU: formatting, aggregation, logging.

    Why CPU:
    - No ML operations
    - Simple data formatting
    - 85% cheaper than GPU
    """
    from datetime import datetime

    predictions = input_data.get("predictions", [])
    original_text = input_data.get("original_text", "")
    metadata = input_data.get("metadata", {})

    # Find top prediction
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

    # Format response
    formatted_result = {
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

    return formatted_result


# Test locally
if __name__ == "__main__":
    import asyncio

    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv())  # Find and load root .env file

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
