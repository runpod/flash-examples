# 01 - Dependency Benchmarking

Compare performance and correctness across Python package versions and system dependency versions.

## What This Demonstrates

- **Version verification** - Confirm installed versions match declared dependencies
- **Performance benchmarking** - Measure execution time of deterministic workloads
- **Correctness checking** - Detect computation differences across versions via result hashes
- **Version comparison workflow** - Deploy two endpoints with different pinned versions, compare output

## Quick Start

**Prerequisites**: Complete the [repository setup](../../README.md#quick-start) first (clone, `make dev`, set API key).

### Files

| File | What it benchmarks |
|------|-------------------|
| `numpy_benchmark.py` | Matrix multiply, array sort, FFT, element-wise ops (Python dep) |
| `ffmpeg_benchmark.py` | Audio encode, video encode, format conversion (system dep) |

### Run This Example

```bash
cd 07_benchmarking/01_dependency_benchmark
flash run
```

Server starts at http://localhost:8888. Hit the benchmark endpoint to get JSON results.

## Version Comparison Workflow

To compare two versions of a Python dependency:

### 1. Copy the worker file

```bash
cp numpy_benchmark.py numpy_benchmark_v2.py
```

### 2. Change the endpoint name and version

In `numpy_benchmark_v2.py`, update the decorator:

```python
@Endpoint(
    name="07_numpy_v2",                # Changed from 07_numpy_v1
    cpu="cpu3c-1-2",
    dependencies=["numpy==2.0.0"],     # Changed from 1.26.4
)
```

### 3. Deploy both

```bash
flash run    # Discovers both files automatically
flash deploy # Or deploy to serverless
```

### 4. Compare JSON output

Both endpoints return the same response structure. Compare side-by-side:

**numpy 1.26.4 (`07_numpy_v1`):**
```json
{
  "version": {"installed": "1.26.4"},
  "benchmarks": {
    "matrix_multiply": {"time_ms": 42.3, "result_hash": "a1b2c3d4e5f6"},
    "fft": {"time_ms": 31.2, "result_hash": "g7h8i9j0k1l2"}
  },
  "total_time_ms": 100.3
}
```

**numpy 2.0.0 (`07_numpy_v2`):**
```json
{
  "version": {"installed": "2.0.0"},
  "benchmarks": {
    "matrix_multiply": {"time_ms": 38.1, "result_hash": "a1b2c3d4e5f6"},
    "fft": {"time_ms": 25.8, "result_hash": "g7h8i9j0k1l2"}
  },
  "total_time_ms": 82.7
}
```

Same `result_hash` = identical computation. Different `time_ms` = performance difference.

**File naming convention:** `<name>_v2.py`, `<name>_v3.py`, etc.

## System Dependencies

The copy-and-compare workflow applies to **Python dependencies only**, where versions can be pinned in the decorator (e.g., `numpy==1.26.4`).

System dependencies are installed via `apt-get` and cannot be pinned to specific versions. The `ffmpeg_benchmark.py` example demonstrates baseline performance measurement of whatever ffmpeg version the system provides. Run it at different times or on different base images to observe version differences.

## Notes

- **Result hash reproducibility**: Floating-point results can differ across CPU architectures and BLAS backends even with the same numpy version. Compare hashes across runs on the same infrastructure for meaningful results.
- **CPU endpoints**: Both benchmarks use CPU endpoints to keep costs low. The workloads do not require GPU.
