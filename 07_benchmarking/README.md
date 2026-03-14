# 07 - Benchmarking

Measure and compare performance across configuration changes. Unlike `04_scaling_performance` (which shows how to configure scaling), this section shows how to measure and compare the impact of different configurations.

## Examples

### [01_dependency_benchmark](01_dependency_benchmark/)
Compare Python package and system dependency versions.

**What you'll learn:**
- Benchmarking Python dependency versions (numpy 1.x vs 2.x)
- Measuring system dependency performance (ffmpeg)
- Version verification at runtime
- Structured benchmark output for comparison

### 02_gpu_type_benchmark _(coming soon)_
Compare performance across GPU types.

**What you'll learn:**
- Running identical workloads on different GpuType values (4090, A100, H100)
- Throughput and latency measurement
- Cost-performance tradeoff analysis

### 03_cold_start_benchmark _(coming soon)_
Measure endpoint startup time with varying dependency counts.

**What you'll learn:**
- Cold start impact of 0, 5, and 20 dependencies
- Startup time measurement methodology
- Dependency count optimization

### 04_scaling_benchmark _(coming soon)_
Compare autoscaling strategies under load.

**What you'll learn:**
- Measuring autoscaling response time
- Throughput comparison across strategies
- Load testing patterns

### 05_cpu_vs_gpu_benchmark _(coming soon)_
Compare the same computation on CPU vs GPU endpoints.

**What you'll learn:**
- Cost-performance tradeoff measurement
- Identifying GPU-appropriate vs CPU-appropriate workloads
- Break-even analysis

## Next Steps

After benchmarking your configurations:
- Review dependency management in [01_getting_started/04_dependencies](../01_getting_started/04_dependencies/)
- Configure scaling in [04_scaling_performance](../04_scaling_performance/)
