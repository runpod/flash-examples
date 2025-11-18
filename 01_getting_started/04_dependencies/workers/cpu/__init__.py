from fastapi import APIRouter
from pydantic import BaseModel, field_validator

from .endpoint import minimal_process, process_data

cpu_router = APIRouter()


class DataRequest(BaseModel):
    """Request model for data processing."""

    data: list[list[int]]

    @field_validator("data")
    @classmethod
    def validate_two_columns(cls, v):
        if not v:
            raise ValueError("Data cannot be empty")
        if len(v) < 2:
            raise ValueError(
                f"Need at least 2 rows to compute statistics, got {len(v)}. "
                f'Example: {{"data": [[1, 2], [3, 4]]}}'
            )
        for i, row in enumerate(v):
            if len(row) != 2:
                raise ValueError(
                    f"Row {i} has {len(row)} columns, expected exactly 2. "
                    f'Example: {{"data": [[1, 2], [3, 4]]}}'
                )
        return v


class TextRequest(BaseModel):
    """Request model for text processing."""

    text: str


@cpu_router.post("/data")
async def data_endpoint(request: DataRequest):
    """Test worker with data science dependencies (pandas, numpy, scipy)."""
    result = await process_data({"data": request.data})
    return result


@cpu_router.post("/minimal")
async def minimal_endpoint(request: TextRequest):
    """Test worker with NO dependencies (fastest cold start)."""
    result = await minimal_process({"text": request.text})
    return result
