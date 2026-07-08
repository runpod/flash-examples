# Benchmark: direct volume cache vs VolumeCache

An A/B that measures **cold-start model-load time** for two ways of caching a
model on a Runpod network volume:

- **direct** (`bench_direct.py`) — `HF_HOME`/`HF_HUB_CACHE` point at a directory
  **on** the volume; the model is read from the network mount on every cold start.
- **volumecache** (`bench_volumecache.py`) — the HF cache stays on **local disk**
  and `runpod.serverless.VolumeCache` hydrates it from the volume before load and
  syncs new files back after; reads are local, the volume is a warm mirror.

Both load the same model (`stable-diffusion-v1-5`) and self-report metrics;
`benchmark.py` drives them and prints a comparison.

## What it measures

| Metric | Meaning |
| --- | --- |
| first-run load | Cold start with an empty cache — includes the download (and, for volumecache, the sync back). One-time per endpoint. |
| warm load (mean/min) | Cold start with the cache already populated — the number that matters at scale. For volumecache this **includes** the hydrate copy. |
| hydrate | Time volumecache spent copying volume → local (0 for direct). |
| volume / local | Bytes stored on the volume and on local disk (volumecache double-stores). |

## Prerequisites and status

- Both endpoints need a network volume attached (the workers declare one).
- **Direct arm: runnable on Flash today.**
- **VolumeCache arm requires a flash-worker image that includes `VolumeCache`
  (SLS-367 / [runpod-python PR #531](https://github.com/runpod/runpod-python/pull/531)).**
  It cannot be added at runtime via `dependencies` because the worker's `runpod`
  is already imported before the handler runs. Until flash-worker ships it, run
  the direct arm alone with `--skip-volumecache`.

This harness has **not been run yet** — no results are published here. Numbers
should be filled in from a real run.

## Running

```bash
# From this benchmark/ directory (so flash dev serves only the two bench workers):
uv run flash dev            # provisions real GPU endpoints; serves at :8888

# In another shell — direct arm only (runnable today):
python benchmark.py --skip-volumecache --warm-trials 3

# Full A/B (once the flash-worker image includes VolumeCache):
python benchmark.py --warm-trials 3
```

Confirm the exact routes at `http://localhost:8888/docs` and pass
`--direct-route` / `--vc-route` if they differ. `--cold-wait` (default 45s) must
exceed the workers' `idle_timeout` (30s) so each trial is a fresh cold start.

> Running provisions real GPU workers and a network volume — it costs money and
> cold starts are slow. Tear down with Ctrl+C on `flash dev` (or `flash undeploy`)
> and verify the endpoints are gone afterward.
