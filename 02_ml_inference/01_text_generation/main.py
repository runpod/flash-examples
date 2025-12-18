## LLM demo: FastAPI router + serverless GPU worker
# This example exposes a simple local FastAPI app (this file) with a single LLM endpoint
# backed by a Runpod serverless GPU worker defined in `gpu_worker.py`.
#
# - Local API: runs on your machine via `flash run` (default: http://localhost:8888)
# - Remote compute: executed on Runpod serverless GPUs via `tetra_rp.remote`
#
# Main endpoint:
# - POST /gpu/llm  -> runs Llama chat inference on the remote GPU worker
#
# Note: The Llama model used in the worker is gated on Hugging Face, so you must provide
# `HF_TOKEN` (the worker reads it from the serverless env).

import logging
import os

from fastapi import FastAPI
from gpu_worker import gpu_router

logger = logging.getLogger(__name__)

# We define a simple FastAPI app to serve requests from localhost.
app = FastAPI(
    title="Flash Application",
    description="Distributed GPU computing with Runpod Flash",
    version="0.1.0",
)

# Attach gpu worker subrouters - this will route any requests to our
# app with the prefix /gpu to the gpu subrouter. To see the subrouter in action,
# start the app and execute the following command in another terminal window:
# curl -X POST http://localhost:8888/gpu/llm -d '{"message": "hello"}' -H "Content-Type: application/json"
app.include_router(
    gpu_router,
    prefix="/gpu",
    tags=["GPU Workers"],
)


# The homepage for our main endpoint will just return a plaintext json object
# containing the endpoints defined in this app.
@app.get("/")
def home():
    return {
        "message": "Flash Application",
        "docs": "/docs",
        "endpoints": {
            "gpu_hello": "/gpu/llm",
        },
    }


@app.get("/ping")
def ping():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("FLASH_HOST", "localhost")
    port = int(os.getenv("FLASH_PORT", 8888))
    logger.info(f"Starting Flash server on {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
    )
