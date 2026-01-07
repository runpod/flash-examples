import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from workers.cpu import cpu_router
from workers.gpu import gpu_router
from workers.gpu.endpoint import SimpleSD

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load the model into app.state
    logger.info("Loading SimpleSD model...")
    app.state.sd_model = SimpleSD()
    logger.info("Model loaded successfully")

    yield

    # Shutdown: Clean up
    logger.info("Cleaning up resources...")
    if hasattr(app.state, "sd_model"):
        del app.state.sd_model
    logger.info("Cleanup complete")


app = FastAPI(
    lifespan=lifespan,
    title="Flash Application",
    description="Distributed GPU and CPU computing with Runpod Flash",
    version="0.1.0",
)

# Include routers
app.include_router(gpu_router, prefix="/gpu", tags=["GPU Workers"])
app.include_router(cpu_router, prefix="/cpu", tags=["CPU Workers"])


@app.get("/")
def home():
    return {
        "message": "Flash Application",
        "docs": "/docs",
    }


@app.get("/ping")
def ping():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8888))
    logger.info(f"Starting Flash server on port {port}")
    logger.info(f"Try generating an image with a prompt by sending a POST request to http://localhost:8888/generate")
    logger.info(f"List generated images by querying /images")

    uvicorn.run(app, host="0.0.0.0", port=port)
