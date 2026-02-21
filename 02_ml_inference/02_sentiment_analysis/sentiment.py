from runpod_flash import remote, LiveServerless, CpuInstanceType

cpu_config = LiveServerless(
    name="flash-ai-sentiment",
    instanceIds=[CpuInstanceType.CPU3G_2_8],
    workersMax=1,
)

@remote(
    resource_config=cpu_config,
    dependencies=[
        "transformers",
        "torch",
        "safetensors",
        "huggingface_hub",
    ],
)
def classify(text: str) -> dict:
    from transformers import pipeline

    clf = pipeline("sentiment-analysis")  # defaults to a reasonable pretrained model
    out = clf(text)[0]  # e.g. {"label": "POSITIVE", "score": 0.999...}

    return {
        "input": text,
        "label": out["label"],
        "score": float(out["score"]),
    }
