# 05_volume_warm_cache

Warm-cache a model on a Runpod network volume with `VolumeCache`, so cold starts
restore the model from the volume instead of re-downloading it.

## Status

`VolumeCache` is a `runpod-python` serverless primitive added in
**SLS-367 / [runpod-python PR #531](https://github.com/runpod/runpod-python/pull/531)**.
It is not yet in a released `runpod-python`. This example runs end-to-end once:

1. PR #531 is merged and released, and
2. the deployed **flash-worker** image is built against a `runpod-python` that
   includes `VolumeCache` (the model load runs inside the remote GPU worker, so
   it is that image's `runpod`, not this example's local env, that must have it).

Until then this example is illustrative. `requirements.txt` pins `runpod` to the
PR branch so the local environment and any custom worker build can resolve
`VolumeCache` today; switch it to the released version once available.

## Overview

`VolumeCache` keeps a browsable mirror of local cache directories on a mounted
network volume and reconciles them on each use:

- **On enter** (`hydrate`): copy files that are missing or newer on the volume
  into the container.
- **On exit** (`sync`): copy files that are missing or newer in the container
  back to the volume (in the background).

The GPU worker wraps its Stable Diffusion load in `with VolumeCache(...)`. The
first cold worker downloads the weights and syncs them to the volume; every later
cold worker hydrates from the volume and skips the download.

## How this differs from `01_network_volumes`

`01_network_volumes` sets `HF_HUB_CACHE` to a path **on** the volume, so every
model read hits the network mount. This example keeps the Hugging Face cache on
**local disk** and uses `VolumeCache` to mirror it to the volume — inference
reads stay local (fast) while cold starts stay warm (persisted).

| | 01_network_volumes | 02_volume_warm_cache |
| --- | --- | --- |
| Model cache location | On the network volume (`HF_HUB_CACHE` → `/runpod-volume/...`) | Local disk (default `~/.cache/huggingface`) |
| Volume role | Live cache (read/written directly) | Warm mirror (hydrated in, synced out) |
| Inference read speed | Network mount | Local disk |
| Cold-start download | Skipped (reads from volume) | Skipped (restored to local disk) |

## Quick Start

```bash
uv pip install -r 05_data_workflows/05_volume_warm_cache/requirements.txt
uv run flash login          # or set RUNPOD_API_KEY in .env
uv run flash dev            # serves at http://localhost:8888
```

Generate an image (provisions a real GPU worker with the volume attached):

```bash
curl -X POST http://localhost:8888/gpu_worker/runsync \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a sunset over mountains"}'
```

## Benchmark: direct vs VolumeCache

`benchmark/` contains an A/B that measures cold-start model-load time for the two
caching strategies (direct HF-on-volume vs local-disk-mirrored-to-volume),
reporting first-run vs warm load time and volume/local storage. See
[benchmark/README.md](./benchmark/README.md). The direct arm is runnable today;
the VolumeCache arm needs a flash-worker image that includes VolumeCache (#531).

## What You'll Learn

- How to warm-cache model weights across cold starts with `runpod.serverless.VolumeCache`
- Why mirroring a local cache to a volume differs from mounting the cache on the volume
- The `with VolumeCache(dirs=[...]):` closure pattern inside a Flash `@Endpoint`
