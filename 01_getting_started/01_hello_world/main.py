## Example 1: Hello world
# This is an example of a simple Flash application.
# It consists of an API router (this file) that routes requests to a local
# endpoint on your machine to worker code. Worker code is executed on Runpod
# infrastructure on gpu and cpu-based serverless workers.

# Subrouters and associated worker function code are defined in the ./workers/
# dir and attached to the main router in this file. By default, running
# `flash run` will start the local API server on your machine serving requests
# from port 8888.

# We'll define a resource configuration for a GPU worker on a Runpod serverless
# endpoint. The GPU worker will return information about the infrastructure
# it executes on.

import logging
import os

from fastapi import FastAPI
from gpu_worker import gpu_router

logger = logging.getLogger(__name__)

# We define a simple FastAPI app to serve requests from localhost.
app = FastAPI(
    title="Flash Application",
    description="Distributed GPU and CPU computing with Runpod Flash",
    version="0.1.0",
)

# Attach gpu and cpu worker subrouters - this will route any requests to our
# app with the prefix /gpu and /cpu to get sent to the gpu and cpu subrouters,
# respectively. For example, curl -X POST http://localhost:{PORT}/cpu will be
# handled entirely by the cpu subrouter.
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
            "gpu_hello": "/gpu/hello",
        },
    }


@app.get("/ping")
def ping():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    port = int(
        os.getenv(
            "PORT",
            8888,
        )
    )
    logger.info(f"Starting Flash server on port {port}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
    )
