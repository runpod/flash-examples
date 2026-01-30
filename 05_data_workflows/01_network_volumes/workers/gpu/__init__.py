from fastapi import APIRouter, Request
from pydantic import BaseModel

gpu_router = APIRouter()


class GenerateRequest(BaseModel):
    prompt: str


@gpu_router.post("/generate")
async def generate(request: GenerateRequest, req: Request):
    """Simple GPU worker endpoint."""
    # Use the shared model loaded in app startup.
    sd_model = req.app.state.sd_model
    result = await sd_model.generate_image(request.prompt)
    return result
