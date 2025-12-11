import logging
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from workers.cpu import cpu_router
from workers.cpu.endpoint import postprocess_results, preprocess_text
from workers.gpu import gpu_router
from workers.gpu.endpoint import gpu_inference

logger = logging.getLogger(__name__)


app = FastAPI(
    title="Mixed GPU/CPU Flash Application",
    description="Cost-effective ML pipeline combining CPU preprocessing with GPU inference",
    version="0.1.0",
)

# Include individual worker routers
app.include_router(gpu_router, prefix="/gpu", tags=["GPU Workers"])
app.include_router(cpu_router, prefix="/cpu", tags=["CPU Workers"])


class ClassifyRequest(BaseModel):
    """Request model for complete classification pipeline."""

    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        if len(v) < 3:
            raise ValueError(
                'Text too short (minimum 3 characters). Example: {"text": "Hello world"}'
            )
        if len(v) > 10000:
            raise ValueError(f"Text too long (maximum 10,000 characters). Got {len(v)} characters.")
        return v


@app.post("/classify", tags=["Pipeline"])
async def classify_text(request: ClassifyRequest):
    """
    Complete ML pipeline: CPU → GPU → CPU

    Pipeline stages:
    1. CPU Preprocessing: Validate and clean text (fast, cheap)
    2. GPU Inference: Run ML model (expensive, necessary)
    3. CPU Postprocessing: Format results (fast, cheap)

    This architecture minimizes GPU usage and maximizes cost-effectiveness.
    """
    try:
        # Stage 1: Preprocess on CPU (fast, cheap)
        # Note: Input validation already done by Pydantic at API layer
        preprocess_result = await preprocess_text({"text": request.text})

        # Stage 2: GPU inference (expensive, necessary)
        gpu_result = await gpu_inference(
            {
                "cleaned_text": preprocess_result["cleaned_text"],
                "word_count": preprocess_result["word_count"],
            }
        )

        # Stage 3: Postprocess on CPU (fast, cheap)
        final_result = await postprocess_results(
            {
                "predictions": gpu_result["predictions"],
                "original_text": request.text,
                "metadata": {
                    "word_count": preprocess_result["word_count"],
                    "sentence_count": preprocess_result["sentence_count"],
                    "model": gpu_result["model_info"],
                },
            }
        )

        return final_result

    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {e!s}") from e


@app.get("/", tags=["Info"])
def home():
    return {
        "message": "Mixed GPU/CPU Flash Application",
        "description": "Cost-effective ML pipeline combining CPU and GPU workers",
        "docs": "/docs",
        "pipeline": {
            "classify": "POST /classify - Complete pipeline (CPU → GPU → CPU)",
            "cpu_preprocess": "POST /cpu/preprocess - CPU text preprocessing",
            "gpu_inference": "POST /gpu/inference - GPU ML inference",
            "cpu_postprocess": "POST /cpu/postprocess - CPU result formatting",
        },
        "architecture": {
            "pattern": "CPU (cheap) → GPU (expensive) → CPU (cheap)",
            "cost_savings": "85% vs GPU-only pipeline",
        },
    }


@app.get("/health", tags=["Info"])
def health():
    return {
        "status": "healthy",
        "workers": {
            "cpu_preprocess": "ready",
            "gpu_inference": "ready",
            "cpu_postprocess": "ready",
        },
    }


if __name__ == "__main__":
    import uvicorn

    host = str(os.getenv("FLASH_HOST", "localhost"))
    port = int(os.getenv("FLASH_PORT", 8888))
    logger.info(f"Starting Mixed GPU/CPU Flash server on {host}:{port}")

    uvicorn.run(app, host=host, port=port)
