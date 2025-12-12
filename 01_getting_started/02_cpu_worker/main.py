## Example 2: Hello world (with CPU workers)
# This is an example of a simple Flash application.
# It consists of an API router (this file) that routes requests to a local endpoint on your machine to
# worker code. Worker code is executed on Runpod infrastructure on low-cost, cpu-based serverless workers.

# Subrouters and associated worker function code are defined in the ./workers/ dir
# and attached to the main router in this file. By default, running `flash run`
# will start the local API server on your machine serving requests from port 8888.

# There are two worker resource configurations for this app: a gpu and a cpu config.
# A CPU-only configured worker allows you to execute code that doesn't require GPUs on
# runpod infrastructure for a lower cost. It will return a simple greeting when you invoke the code directly
# or send a request to its corresponding endpoint. The GPU worker will return information about the infrastructure
# it executes on.

import logging
import os

from cpu_worker import cpu_router
from fastapi import FastAPI

logger = logging.getLogger(__name__)

# We define a simple FastAPI app to serve requests from localhost.
app = FastAPI(
    title="Flash Application",
    description="Distributed GPU and CPU computing with Runpod Flash",
    version="0.1.0",
)

# Attach gpu and cpu worker subrouters - this will route any requests to our app
# with the prefix /cpu to our CPU subrouter. Try out the following command
# in a separate terminal window after starting your app:
# curl -X POST http://localhost:8888/cpu/hello -d '{"input": "hello"}' -H "Content-Type: application/json"
app.include_router(cpu_router, prefix="/cpu", tags=["CPU Workers"])


# The homepage for our main endpoint will just return a plaintext json object containing the endpoints defined in this app.
@app.get("/")
def home():
    return {
        "message": "Flash Application",
        "docs": "/docs",
        "endpoints": {"gpu_hello": "/gpu/hello", "cpu_hello": "/cpu/hello"},
    }


@app.get("/ping")
def ping():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("FLASH_HOST", "localhost")
    port = int(os.getenv("FLASH_PORT", 8888))
    logger.info(f"Starting Flash server on {host}:{port}")

    uvicorn.run(app, host=host, port=port)
