# Classification pipeline: CPU preprocess -> GPU inference -> CPU postprocess.
# Demonstrates cross-worker orchestration via a load-balanced endpoint.
# Run with: flash run
from cpu_worker import postprocess_results, preprocess_text
from gpu_worker import gpu_inference
from runpod_flash import CpuLiveLoadBalancer, remote

pipeline_config = CpuLiveLoadBalancer(
    name="01_03_classify_pipeline",
    workersMin=1,
)


@remote(resource_config=pipeline_config, method="POST", path="/classify")
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
