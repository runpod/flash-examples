"""LangGraph + Flash integration example.

This example demonstrates how LangGraph manages agentic workflows while Flash
handles distributed execution of compute-intensive tasks. The agent analyzes
datasets through sequential analysis steps with conditional refinement based
on data quality scores.
"""

import logging
from typing import Any

from fastapi import APIRouter
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from tetra_rp import GpuGroup, LiveServerless, remote

logger = logging.getLogger(__name__)


# Define the state that flows through the LangGraph workflow
class AnalysisState(dict):
    """State definition for the data analysis workflow.

    Attributes:
        dataset: Original input dataset
        analysis_result: Results from data analysis step
        refined_dataset: Dataset after refinement (if applied)
        summary: Final summary of analysis
        quality_score: Quality metric (0.0 to 1.0)
        needs_refinement: Whether refinement is needed
        iteration_count: Number of iterations completed
    """

    pass


# Configure GPU worker for analysis tasks
gpu_config = LiveServerless(
    name="02_02_langgraph_analysis",
    gpus=[GpuGroup.ANY],
    workersMin=0,
    workersMax=2,
    idleTimeout=300,
)


@remote(resource_config=gpu_config)
async def analyze_data(dataset: dict) -> dict:
    """Analyze dataset and compute statistics.

    This remote function executes on GPU infrastructure. It simulates
    using GPU-accelerated tensor operations for analysis.

    Args:
        dataset: Dictionary with 'values' list of numbers

    Returns:
        Dictionary with analysis results including mean, std, outlier count
    """
    import numpy as np
    import torch

    values = dataset.get("values", [])

    if not values:
        return {"mean": 0.0, "std": 0.0, "outliers": 0, "error": "Empty dataset"}

    # Use GPU tensor operations if available
    try:
        if torch.cuda.is_available():
            tensor = torch.tensor(values, dtype=torch.float32, device="cuda")
            mean = float(tensor.mean())
            std = float(tensor.std())
        else:
            # Fallback to numpy
            mean = float(np.mean(values))
            std = float(np.std(values))
    except Exception as e:
        return {"error": str(e)}

    # Simulate outlier detection
    outliers = int(std * 10) if std > 0 else 0

    # Calculate quality score based on data variance
    quality_score = 0.92 if std > 1.0 else 0.75

    return {
        "mean": round(mean, 3),
        "std": round(std, 3),
        "outliers": outliers,
        "quality_score": round(quality_score, 2),
        "needs_refinement": quality_score < 0.8,
    }


@remote(resource_config=gpu_config)
async def refine_data(dataset: dict) -> dict:
    """Refine dataset by removing outliers.

    This remote function removes simulated outliers from the dataset
    using statistical methods.

    Args:
        dataset: Dictionary with 'values' list and 'mean', 'std' from analysis

    Returns:
        Dictionary with refined dataset and metadata
    """
    values = dataset.get("values", [])
    mean = dataset.get("mean", 0)
    std = dataset.get("std", 1)

    if not values or std == 0:
        return {"cleaned_values": values, "removed_count": 0, "quality_score": 0.92}

    # Remove values beyond 2 standard deviations
    threshold = 2 * std
    cleaned_values = [v for v in values if abs(v - mean) < threshold]
    removed_count = len(values) - len(cleaned_values)

    # After refinement, quality improves
    quality_score = 0.92

    return {
        "cleaned_values": cleaned_values,
        "removed_count": removed_count,
        "quality_score": round(quality_score, 2),
    }


@remote(resource_config=gpu_config)
async def summarize_data(state: dict) -> dict:
    """Generate final summary of analysis.

    This remote function creates a human-readable summary and
    provides recommendations for the dataset.

    Args:
        state: Current workflow state with all analysis results

    Returns:
        Dictionary with summary and recommendations
    """
    analysis = state.get("analysis_result", {})
    refined = state.get("refined_dataset")
    mean = analysis.get("mean", 0)
    std = analysis.get("std", 0)
    quality = state.get("quality_score", 0)

    summary = f"Dataset analysis complete. Mean: {mean}, StdDev: {std}, Quality: {quality:.2f}"

    recommendations = []
    if quality > 0.9:
        recommendations.append("Dataset is high-quality and ready for modeling")
    elif quality > 0.8:
        recommendations.append("Dataset quality is acceptable with minor cleaning")
    else:
        recommendations.append("Consider additional data validation")

    if refined and refined.get("removed_count", 0) > 0:
        removed = refined.get("removed_count", 0)
        recommendations.append(f"Removed {removed} outliers during refinement")

    if std < 0.5:
        recommendations.append("Consider normalization before training")

    return {
        "summary": summary,
        "recommendations": recommendations,
        "final_quality": round(quality, 2),
    }


# LangGraph Workflow Nodes
def analyze_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node: Call analysis worker and update state."""
    import asyncio

    dataset = state.get("dataset", {})

    # Call remote analysis worker
    result = asyncio.run(analyze_data(dataset))

    return {
        **state,
        "analysis_result": result,
        "quality_score": result.get("quality_score", 0.5),
        "needs_refinement": result.get("needs_refinement", False),
        "iteration_count": state.get("iteration_count", 0) + 1,
    }


def refine_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node: Call refinement worker and update state."""
    import asyncio

    dataset = state.get("dataset", {})
    analysis = state.get("analysis_result", {})

    # Prepare input for refinement worker
    refine_input = {
        "values": dataset.get("values", []),
        "mean": analysis.get("mean", 0),
        "std": analysis.get("std", 1),
    }

    # Call remote refinement worker
    result = asyncio.run(refine_data(refine_input))

    return {
        **state,
        "refined_dataset": result,
        "quality_score": result.get("quality_score", 0.92),
        "needs_refinement": False,  # Refinement complete
        "iteration_count": state.get("iteration_count", 0) + 1,
    }


def summarize_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node: Call summarization worker and update state."""
    import asyncio

    # Call remote summarization worker
    result = asyncio.run(summarize_data(state))

    return {
        **state,
        "summary": result,
        "iteration_count": state.get("iteration_count", 0) + 1,
    }


def should_refine(state: dict[str, Any]) -> str:
    """Conditional routing: Determine if refinement is needed.

    Routes to 'refine' node if data quality is low and iterations remaining,
    otherwise routes to 'summarize'.
    """
    needs_refinement = state.get("needs_refinement", False)
    iteration_count = state.get("iteration_count", 0)
    max_iterations = 3

    if needs_refinement and iteration_count < max_iterations:
        return "refine"
    return "summarize"


# Build the LangGraph workflow
def build_workflow() -> StateGraph:
    """Construct the LangGraph state machine for data analysis.

    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(dict)

    # Add nodes
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("refine", refine_node)
    workflow.add_node("summarize", summarize_node)

    # Set entry point
    workflow.set_entry_point("analyze")

    # Add edges with conditional routing
    workflow.add_conditional_edges(
        "analyze",
        should_refine,
        {"refine": "refine", "summarize": "summarize"},
    )
    workflow.add_edge("refine", "summarize")
    workflow.add_edge("summarize", END)

    return workflow.compile()


# FastAPI Router Setup
gpu_router = APIRouter()


class DatasetRequest(BaseModel):
    """Request model for dataset analysis."""

    values: list[float] = Field(
        ...,
        description="Dataset values to analyze",
        min_length=10,
        max_length=10000,
    )
    dataset_type: str = Field(default="numerical", description="Type of dataset")


class AnalysisResponse(BaseModel):
    """Response model for analysis results."""

    status: str
    iterations: int
    quality_score: float
    analysis: dict[str, Any]
    refined: dict[str, Any] | None
    summary: dict[str, Any]


@gpu_router.post("/analyze-dataset", response_model=AnalysisResponse)
async def analyze_dataset_endpoint(request: DatasetRequest) -> AnalysisResponse:
    """Analyze dataset using LangGraph + Flash workflow.

    Executes a multi-step analysis with conditional refinement:
    1. Analyze data to compute statistics and quality score
    2. Refine data if quality < 0.8 (remove outliers)
    3. Summarize and provide recommendations

    Args:
        request: DatasetRequest with values and dataset_type

    Returns:
        AnalysisResponse with full analysis results
    """
    try:
        # Initialize workflow state
        initial_state = {
            "dataset": {
                "values": request.values,
                "dataset_type": request.dataset_type,
            },
            "analysis_result": None,
            "refined_dataset": None,
            "summary": None,
            "quality_score": 0.0,
            "needs_refinement": False,
            "iteration_count": 0,
        }

        # Build and execute workflow
        workflow = build_workflow()
        final_state = workflow.invoke(initial_state)

        # Extract results
        analysis = final_state.get("analysis_result", {})
        refined = final_state.get("refined_dataset")
        summary = final_state.get("summary", {})
        iterations = final_state.get("iteration_count", 1)
        quality = final_state.get("quality_score", 0.0)

        return AnalysisResponse(
            status="success",
            iterations=iterations,
            quality_score=round(quality, 2),
            analysis=analysis,
            refined=refined,
            summary=summary,
        )

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise


@gpu_router.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "langgraph-flash-integration"}


if __name__ == "__main__":
    import json

    # Test the workflow locally
    test_payload = {
        "dataset": {
            "values": [1.2, 3.4, 2.1, 5.6, 4.3, 2.8, 1.9, 3.2, 4.1, 2.5],
            "dataset_type": "numerical",
        },
        "analysis_result": None,
        "refined_dataset": None,
        "summary": None,
        "quality_score": 0.0,
        "needs_refinement": False,
        "iteration_count": 0,
    }

    print("Testing LangGraph + Flash workflow locally...")
    print(json.dumps(test_payload, indent=2))

    workflow = build_workflow()
    result = workflow.invoke(test_payload)

    print("\nWorkflow result:")
    print(
        json.dumps(
            {
                "iterations": result.get("iteration_count"),
                "quality_score": result.get("quality_score"),
                "analysis": result.get("analysis_result"),
                "refined": result.get("refined_dataset"),
                "summary": result.get("summary"),
            },
            indent=2,
        )
    )
