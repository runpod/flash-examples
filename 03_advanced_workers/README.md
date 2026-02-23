# 03 - Advanced Workers

Production-ready worker patterns for building robust, scalable applications.

## Examples

### 02_docker_images
Using custom Docker images for RunPod serverless workers.

**What you'll learn:**
- Using `ServerlessEndpoint` with `dockerImage` for custom containers
- Comparing managed (`LiveServerless`) vs custom Docker deployment
- Configuring environment variables for Docker-based workers
- Using RunPod's official Docker images (PyTorch, vLLM, etc.)

**Use cases:**
- Specific CUDA versions
- Pre-built model caches
- Specialized ML frameworks
- RunPod worker images (vLLM, TGI, etc.)

**Resources:**
- `ServerlessEndpoint` - Custom Docker images
- `LiveServerless` - Managed infrastructure (comparison)

### 03_public_endpoints
Calling RunPod serverless endpoints from Flash workers.

**What you'll learn:**
- Using the `runpod` Python SDK to call serverless endpoints
- Synchronous vs asynchronous endpoint invocation
- Job status polling and webhook patterns
- Building GPU pipelines that chain endpoint calls
- Concurrent batch processing

**Use cases:**
- Orchestrating multiple AI services
- GPU preprocessing + remote LLM inference
- Calling community or public endpoints
- Fire-and-forget job submission

**Resources:**
- `CpuLiveServerless` - CPU orchestration workers
- `LiveServerless` - GPU pipeline workers

### 05_load_balancer
Load-balancer endpoints with custom HTTP routes.

**What you'll learn:**
- Creating load-balanced endpoints
- Custom HTTP routing (GET, POST, PUT, DELETE, PATCH)
- Low-latency request/response patterns
- Multiple routes on a single endpoint

**Use cases:**
- Real-time APIs
- REST services
- Direct HTTP communication
- Low-latency inference services

**Resources:**
- `LiveLoadBalancer` - Local development
- `LoadBalancerSlsResource` - Production deployment

### 01_streaming _(coming soon)_
Streaming responses with Server-Sent Events (SSE) and WebSockets.

**What you'll learn:**
- Implementing SSE for text streaming
- WebSocket connections for bidirectional communication
- Handling client disconnections
- Error recovery in streams

**Use cases:**
- LLM text generation streaming
- Real-time progress updates
- Live inference results

### 02_batch_processing _(coming soon)_
Batch inference optimization for throughput.

**What you'll learn:**
- Batching requests for efficiency
- Dynamic batch sizing
- Timeout handling
- Queue management

**Use cases:**
- Bulk image processing
- Batch embeddings
- Dataset processing

### 03_caching _(coming soon)_
Model and result caching strategies.

**What you'll learn:**
- Model weight caching
- Result caching with Redis
- Cache invalidation strategies
- Memory vs disk caching

**Patterns:**
- Warm start optimization
- Multi-level caching
- Cache-aside pattern

### 04_custom_images
See [02_docker_images](02_docker_images/) for custom Docker image examples.

## Design Principles

Examples in this section emphasize:
- **Reliability**: Error handling and recovery
- **Performance**: Optimization techniques
- **Cost efficiency**: Resource utilization
- **Maintainability**: Clean, testable code

## Common Patterns

- **Circuit breakers**: Handle downstream failures
- **Retry logic**: Transient error recovery
- **Timeouts**: Prevent hanging requests
- **Graceful degradation**: Fallback strategies

## Next Steps

After mastering advanced patterns:
- Apply scaling concepts from [04_scaling_performance](../04_scaling_performance/)
- Implement data workflows from [05_data_workflows](../05_data_workflows/)
- Build complete applications in [06_real_world](../06_real_world/)
