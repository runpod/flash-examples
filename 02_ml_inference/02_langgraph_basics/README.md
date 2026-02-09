# LangGraph + Flash Integration

Build intelligent workflows that orchestrate distributed computation. This example demonstrates how LangGraph manages agentic logic while Flash handles scalable execution.

## What You'll Learn

- **LangGraph State Management**: Define and manage workflow state through sequential operations
- **Agentic Loops**: Implement conditional routing that adapts based on intermediate results
- **Flash Remote Execution**: Offload compute-intensive tasks to GPU workers
- **Integration Patterns**: Combine orchestration (LangGraph) with distributed execution (Flash)
- **Quality-Driven Workflows**: Make decisions based on data quality metrics

## Overview

This example implements a **Data Analysis Agent** that processes datasets through a multi-step workflow:

1. **Analyze**: Compute statistics and quality metrics
2. **Conditionally Refine**: Remove outliers if quality score < 0.8
3. **Summarize**: Generate insights and recommendations

The workflow uses conditional routing to decide whether refinement is needed, demonstrating how agentic systems adapt based on intermediate results.

## Architecture

```
┌─────────────┐
│   Client    │
│  Request    │
└──────┬──────┘
       │
       v
┌──────────────────────────────────────────────┐
│        LangGraph Orchestrator                │
│  (State Management + Routing Logic)          │
└──────────────────────────────────────────────┘
       │
       ├─────────────────────┬─────────────────┐
       │                     │                 │
       v                     v                 v
┌─────────────┐     ┌──────────────┐     ┌────────────┐
│   Analyze   │────>│   Refine     │────>│ Summarize  │
│  (Flash)    │     │  (Flash)     │     │  (Flash)   │
└─────────────┘     └──────────────┘     └────────────┘
       │ GPU           │ GPU               │ GPU
       │ Exec          │ Exec              │ Exec
       │               │                   │
       └───────────────┴───────────────────┘
                     │
                     v
            ┌─────────────────┐
            │   Response      │
            │  with Results   │
            └─────────────────┘
```

## How It Works

### Workflow States

The workflow maintains state as it progresses through analysis steps:

```python
AnalysisState = {
    "dataset": dict,              # Input data
    "analysis_result": dict,      # Analysis output
    "refined_dataset": dict,      # Refined data (if applied)
    "summary": dict,              # Final summary
    "quality_score": float,       # Quality metric (0-1)
    "needs_refinement": bool,     # Refinement decision
    "iteration_count": int,       # Step counter
}
```

### Conditional Routing

After the analyze step, the workflow decides whether to refine:

```python
def should_refine(state):
    if state["needs_refinement"] and state["iteration_count"] < 3:
        return "refine"  # Go to refine node
    return "summarize"   # Skip to summarize
```

This pattern enables workflows to adapt based on data characteristics, not just fixed pipelines.

### Remote Workers

Each computational step is a remote worker that executes on GPU infrastructure:

```python
@remote(resource_config=gpu_config)
async def analyze_data(dataset):
    # Uses GPU for tensor operations
    # Returns statistics and quality score
    pass
```

## Quick Start

### Prerequisites

- Python 3.10+
- Flash SDK installed
- Runpod API key (for cloud execution)

### Installation

```bash
cd 02_ml_inference/02_langgraph_basics
flash run
```

The server starts on `localhost:8888`. Open `http://localhost:8888/docs` to see the interactive API documentation.

### Test the Endpoint

Use curl to test the analysis endpoint:

```bash
curl -X POST "http://localhost:8888/gpu/analyze-dataset" \
  -H "Content-Type: application/json" \
  -d '{
    "values": [1.2, 3.4, 2.1, 5.6, 4.3, 2.8, 1.9, 3.2, 4.1, 2.5],
    "dataset_type": "numerical"
  }'
```

## API Endpoints

### POST /gpu/analyze-dataset

Analyze a dataset through the complete LangGraph workflow.

**Request**

```json
{
  "values": [1.0, 1.1, 0.9, 1.2, 1.0, 0.8, 1.1, 1.0, 0.9, 1.1],
  "dataset_type": "numerical"
}
```

**Response**

```json
{
  "status": "success",
  "iterations": 1,
  "quality_score": 0.92,
  "analysis": {
    "mean": 1.01,
    "std": 0.123,
    "outliers": 1,
    "quality_score": 0.92,
    "needs_refinement": false
  },
  "refined": null,
  "summary": {
    "summary": "Dataset analysis complete. Mean: 1.01, StdDev: 0.123, Quality: 0.92",
    "recommendations": [
      "Dataset is high-quality and ready for modeling",
      "Consider normalization before training"
    ],
    "final_quality": 0.92
  }
}
```

### GET /gpu/health

Health check endpoint.

**Response**

```json
{
  "status": "healthy",
  "service": "langgraph-flash-integration"
}
```

## Example Scenarios

### Scenario 1: High-Quality Dataset (No Refinement)

Input with low variance (clean data):

```bash
curl -X POST "http://localhost:8888/gpu/analyze-dataset" \
  -H "Content-Type: application/json" \
  -d '{"values": [1.0, 1.1, 0.9, 1.2, 1.0, 0.8, 1.1, 1.0, 0.9, 1.1]}'
```

Expected behavior:
- `iterations: 1` (skip refinement)
- `quality_score: 0.92`
- `refined: null` (no refinement applied)

### Scenario 2: Noisy Dataset (With Refinement)

Input with high variance (outliers):

```bash
curl -X POST "http://localhost:8888/gpu/analyze-dataset" \
  -H "Content-Type: application/json" \
  -d '{"values": [1.0, 5.0, 1.5, 10.0, 2.0, 8.0, 1.2, 6.0, 1.8, 7.0]}'
```

Expected behavior:
- `iterations: 2` (refinement triggered)
- Initial `quality_score: 0.75` → Final `quality_score: 0.92`
- `refined` contains cleaned dataset and removed outlier count

## Key Concepts

### LangGraph

LangGraph is a framework for building stateful, agentic applications. Key components:

- **StateGraph**: Defines the workflow structure
- **Nodes**: Functions that process state
- **Edges**: Connections between nodes
- **Conditional Edges**: Branching logic based on state

```python
workflow = StateGraph(dict)
workflow.add_node("analyze", analyze_node)
workflow.add_node("refine", refine_node)
workflow.add_conditional_edges("analyze", should_refine)
```

### Flash Remote Execution

The `@remote` decorator transforms functions into distributed workers:

```python
@remote(resource_config=gpu_config)
async def analyze_data(dataset):
    # Runs on Runpod GPU infrastructure
    return results
```

### State Immutability

Each node returns an updated state dictionary. LangGraph handles state flow:

```python
def analyze_node(state):
    result = asyncio.run(analyze_data(...))
    return {
        **state,                              # Preserve existing state
        "analysis_result": result,            # Add new result
        "quality_score": result["quality"],   # Update computed fields
    }
```

## Integration with Unified App

In the unified Flash Examples app, this example is discovered at:

```
/02_langgraph_basics/gpu/analyze-dataset
```

Routes are auto-discovered by scanning for `{worker_type}_router` exports (e.g., `gpu_router` in `gpu_worker.py`).

## Deployment Considerations

### Cost Estimates

For RTX 4090 GPU at $0.39/hour:

- Analysis only: ~$0.0008 (2 seconds)
- With refinement: ~$0.0016 (4 seconds)
- Monthly (1000 requests): ~$0.80

### Scaling

Worker configuration:

```python
gpu_config = LiveServerless(
    name="02_02_langgraph_analysis",
    gpus=[GpuGroup.ANY],
    workersMin=0,      # Scale to zero when idle
    workersMax=2,      # Handle 2 concurrent requests
    idleTimeout=300,   # Keep warm for 5 minutes
)
```

## Common Issues

### Issue: "Module not found" errors

**Solution**: Run `make consolidate-deps` from the flash-examples-2 root to ensure all dependencies are installed.

### Issue: Import errors for LangGraph

**Solution**: Ensure langgraph and langchain-core are in your environment:

```bash
pip install langgraph langchain-core
```

### Issue: Timeout during remote execution

**Solution**: Increase the timeout in your client or reduce dataset size. Remote execution adds network latency.

### Issue: GPU not detected

**Solution**: Remote execution automatically falls back to CPU. GPU detection happens at runtime on Runpod infrastructure.

## Testing Locally

Run all tests:

```bash
python -m pytest
```

Run the workflow without Flash (local simulation):

```bash
python gpu_worker.py
```

## Next Steps

After understanding this example:

1. **Parallel Workflows**: See `03_advanced_workers` for parallel multi-worker patterns
2. **Stateful Agents**: Build agents that maintain context across requests
3. **Complex Pipelines**: Chain multiple analysis steps with data passing
4. **Error Handling**: Add retry logic and error recovery to workflows

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Runpod Flash Documentation](https://docs.runpod.io/flash/overview)
- [Pydantic Validation](https://docs.pydantic.dev/)
