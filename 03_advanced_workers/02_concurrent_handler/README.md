# Concurrent Handler

Demonstrates `max_concurrency` for QB endpoints.

## What This Shows

- `max_concurrency=5` on `@Endpoint` allows the worker to process 5 jobs simultaneously
- Handler must be `async` to benefit from concurrency
- The Runpod SDK's `concurrency_modifier` is configured automatically

## When to Use

- vLLM or TGI inference servers where the model handles batching internally
- Handlers that spend most of their time awaiting I/O (network, disk)
- Any async workload where a single GPU can serve multiple requests

## Usage

```bash
flash build
flash deploy
```

## How It Works

Flash generates a handler with `concurrency_modifier` in `runpod.serverless.start()`:

```python
runpod.serverless.start({
    "handler": handler,
    "concurrency_modifier": lambda current: 5,
})
```

The Runpod JobScaler then fetches and processes up to 5 jobs concurrently on each worker.
