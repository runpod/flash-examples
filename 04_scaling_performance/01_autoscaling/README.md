# Autoscaling: Worker Scaling Strategies

Configure Flash worker autoscaling for different workload patterns. This example demonstrates five scaling configurations across GPU and CPU workers, from cost-optimized scale-to-zero to latency-optimized always-on.

## Quick Start

**Prerequisites**: Complete the [repository setup](../../README.md#quick-start) first, or run `flash login` to authenticate.

```bash
cd 04_scaling_performance/01_autoscaling
flash run
```

Server starts at http://localhost:8888 -- visit http://localhost:8888/docs for interactive API docs.

### Test Individual Strategies

```bash
# Scale-to-zero GPU worker
curl -X POST http://localhost:8888/gpu_worker/runsync \
  -H "Content-Type: application/json" \
  -d '{"matrix_size": 512}'

# Always-on GPU worker (same payload, different endpoint)
curl -X POST http://localhost:8888/gpu_worker/runsync \
  -H "Content-Type: application/json" \
  -d '{"matrix_size": 512}'

# CPU scale-to-zero
curl -X POST http://localhost:8888/cpu_worker/runsync \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello autoscaling"}'
```

## Scaling Strategies

### GPU Workers (`gpu_worker.py`)

| Strategy | workersMin | workersMax | idleTimeout | scalerType | scalerValue | Use Case |
|----------|-----------|-----------|-------------|------------|-------------|----------|
| Scale to Zero | 0 | 3 | 5 min | QUEUE_DELAY | 4 | Sporadic/batch, cost-first |
| Always On | 1 | 3 | 60 min | QUEUE_DELAY | 4 | Steady traffic, latency-first |
| High Throughput | 2 | 10 | 30 min | REQUEST_COUNT | 3 | Bursty traffic, throughput-first |

### CPU Workers (`cpu_worker.py`)

| Strategy | workersMin | workersMax | idleTimeout | Use Case |
|----------|-----------|-----------|-------------|----------|
| Scale to Zero | 0 | 5 | 5 min | Cost-optimized preprocessing |
| Burst Ready | 1 | 10 | 30 min | Always-warm API gateway |

## How Autoscaling Works

```
Requests arrive
    |
    v
+-------------------+
|   Request Queue   |  <-- scalerType monitors this
+-------------------+
    |
    v
+-------------------+     scale up
|   Scaler Logic    | ----------------> Start new workers
| (QUEUE_DELAY or   |                   (up to workersMax)
|  REQUEST_COUNT)   |
+-------------------+
    |
    v
+-------------------+     idle > idleTimeout
|   Active Workers  | ----------------> Terminate worker
| (workersMin..Max) |                   (down to workersMin)
+-------------------+
```

**Scaler types:**

- **QUEUE_DELAY** -- Scales based on how long requests wait in the queue. `scalerValue` is the target queue delay in seconds. Good for latency-sensitive workloads.
- **REQUEST_COUNT** -- Scales based on pending request count per worker. `scalerValue` is the target requests per worker. Good for throughput-sensitive workloads.

## Configuration Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `workersMin` | int | 0 | Minimum workers kept warm (0 = scale to zero) |
| `workersMax` | int | 3 | Maximum concurrent workers |
| `idleTimeout` | int | 5 | Minutes before idle workers terminate |
| `scalerType` | ServerlessScalerType | QUEUE_DELAY | Scaling trigger metric |
| `scalerValue` | int | 4 | Target value for the scaler metric |
| `gpus` | list[GpuGroup] | -- | GPU types for LiveServerless |
| `instanceIds` | list[CpuInstanceType] | -- | CPU instance types for CpuLiveServerless |

## Cost Analysis

### Scale-to-Zero vs Always-On (GPU)

Assumptions: GPU cost ~$0.0015/sec, 8 hours of actual compute per day.

**Scale to Zero (workersMin=0):**
```
Compute: 8h x 3600s x $0.0015 = $43.20/day
Cold starts: ~5-30s penalty per scale-up event
Monthly: ~$1,296
```

**Always On (workersMin=1):**
```
Baseline: 24h x 3600s x $0.0015 = $129.60/day (1 worker always running)
Extra compute: handled by autoscaling
Monthly: ~$3,888+ (baseline alone)
```

**When to choose each:**

- **Scale to Zero**: Traffic is sporadic (< 4 hours/day of active use), batch processing, dev/staging environments, cost is primary concern.
- **Always On**: Traffic is steady (> 8 hours/day), SLA requires < 1s p99 latency, cold start penalty is unacceptable.
- **High Throughput**: Traffic is bursty with unpredictable spikes, throughput matters more than per-request latency, willing to pay for warm capacity.

### CPU Cost Comparison

CPU workers cost ~10x less than GPU. Use CPU for preprocessing, validation, and orchestration to reduce overall spend.

```
CPU worker: ~$0.0002/sec
GPU worker: ~$0.0015/sec
Ratio: ~7.5x cheaper
```

## Load Testing

Use `load_test.py` to observe scaling behavior:

```bash
# Default: 20 requests, concurrency 10, 10s pause
python load_test.py

# Target a specific endpoint
python load_test.py --endpoint /gpu_worker/runsync --requests 50

# Longer pause to observe scale-down
python load_test.py --pause 60 --concurrency 20

# Test CPU workers
python load_test.py --endpoint /cpu_worker/runsync --requests 100 --concurrency 50
```

**Requires:** `pip install aiohttp`

### Interpreting Results

- **First burst p95 vs second burst p95**: If pause > idleTimeout, second burst includes cold start latency. A large gap indicates scale-down occurred.
- **Error rate > 0%**: Workers may be overwhelmed. Increase `workersMax` or reduce `scalerValue`.
- **High p99 with low p50**: Queue delay is building up. Consider switching to `REQUEST_COUNT` scaler.

## Cold Start Mitigation

Cold starts occur when `workersMin=0` and all workers have been terminated.

**Strategies:**

1. **Set workersMin=1** -- Keeps one worker warm. Simplest fix, costs ~$130/day for GPU.
2. **Increase idleTimeout** -- Workers stay alive longer between requests. Good for intermittent traffic.
3. **Warm-up requests** -- Send periodic health checks to prevent scale-down. Application-level solution.
4. **Optimize container startup** -- Reduce model load time with smaller models, model caching, or quantization.

## Production Checklist

- [ ] Choose scaling strategy based on traffic pattern (sporadic, steady, bursty)
- [ ] Set `workersMax` based on budget and peak load
- [ ] Set `idleTimeout` based on traffic gaps (longer = fewer cold starts, higher cost)
- [ ] Choose `scalerType` based on priority (latency = QUEUE_DELAY, throughput = REQUEST_COUNT)
- [ ] Tune `scalerValue` after load testing (lower = more aggressive scaling)
- [ ] Run load test to verify scaling behavior
- [ ] Monitor cold start frequency in production
- [ ] Set up cost alerts for unexpected scaling

## Next Steps

- [02_gpu_optimization](../02_gpu_optimization/) -- GPU memory management and optimization
- [03_concurrency](../03_concurrency/) -- Async patterns and concurrency control
- [04_monitoring](../04_monitoring/) -- Logging, metrics, and observability
