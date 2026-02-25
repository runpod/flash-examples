# classification pipeline: CPU preprocess -> GPU inference -> CPU postprocess.
# demonstrates cross-worker orchestration via a load-balanced endpoint.
# run with: flash run
from cpu_worker import postprocess_results, preprocess_text
from gpu_worker import gpu_inference
from runpod_flash import Endpoint

pipeline = Endpoint(name="01_03_classify_pipeline", cpu="cpu3c-1-2", workers=(1, 3))


@pipeline.post("/classify")
async def classify(text: str) -> dict:
    """Complete ML pipeline: CPU preprocess -> GPU inference -> CPU postprocess."""
    preprocess_result = await preprocess_text({"text": text})

    gpu_result = await gpu_inference(
        {
            "cleaned_text": preprocess_result["cleaned_text"],
            "word_count": preprocess_result["word_count"],
        }
    )

    return await postprocess_results(
        {
            "predictions": gpu_result["predictions"],
            "original_text": text,
            "metadata": {
                "word_count": preprocess_result["word_count"],
                "sentence_count": preprocess_result["sentence_count"],
                "model": gpu_result["model_info"],
            },
        }
    )


if __name__ == "__main__":
    import asyncio

    test_text = "This is a test message for the classification pipeline."
    print(f"Testing classify with text: {test_text}")
    result = asyncio.run(classify(test_text))
    print(f"Result: {result}")
