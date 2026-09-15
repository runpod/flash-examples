# Rigorous benchmark: direct-on-volume vs VolumeCache

A controlled A/B of two model-caching strategies on a Runpod network volume:

- **direct** — HF cache lives on the volume; every load reads the model from the
  network mount.
- **volumecache** — HF cache on local disk, mirrored to the volume; a fresh
  worker hydrates (copies volume → local) once, then loads from local.

This is a **Pod-based** benchmark, not serverless — on purpose.

## Why not the serverless harness

The serverless benchmark (one directory up) couldn't produce trustworthy numbers:

- **Page cache.** A model loaded once sits in RAM; the next load hits RAM, not
  disk, and looks instant (~1s). The serverless "warm" numbers were page-cache
  hits, not storage reads.
- **No control over cold starts.** Forcing scale-to-0 via idle timeout + sleep
  was unreliable; workers persisted and warm reuse contaminated the results.
- **Wrong question.** A single cold start doesn't reveal the tradeoff. On one
  load, VolumeCache does *more* I/O than direct — it reads the model from the
  volume during hydrate *and* again from local during load, while direct reads
  from the volume once. VolumeCache can only win when the model is loaded enough
  times per worker for cheaper local reads to amortize the one-time hydrate.

This harness fixes all three: it runs as root and **drops the OS page cache
before every timed read**, controls cache state explicitly, repeats N trials for
variance, and reports the **per-reload cost and the breakeven point**.

## What it measures (per strategy, N trials, warmup discarded, cold page cache)

| Metric | Meaning |
| --- | --- |
| direct load (volume) | Load the model reading from the volume mount. |
| vc hydrate (volume→local) | Copy the mirror from volume to local disk. |
| vc first load (local) | Load right after hydrate (files warm in cache, as a real worker sees). |
| vc reload (local) | Load with the model already local, cold page cache — the steady-state local read. |
| storage | Bytes on the volume (direct + mirror) and local disk. |
| breakeven | How many loads per worker before VolumeCache beats direct. |

## Running

Provision a **Pod** with a GPU and the network volume attached (mounted at
`/runpod-volume`), then on the pod (as root):

```bash
pip install "runpod>=1.12.0" diffusers transformers accelerate torch
python benchmark.py --trials 5 --reloads 5
```

First run downloads the model once to seed both caches (needs internet + HF
access); subsequent runs reuse them.

## Interpreting

- If **vc reload < direct load**, local reads beat volume reads; VolumeCache pays
  off after `hydrate / (direct_load − vc_reload)` loads per worker.
- If **vc reload ≥ direct load**, the volume read isn't the bottleneck, so
  VolumeCache only adds a hydrate copy + double storage — direct-on-volume is the
  simpler, faster choice for this model/volume.

The point isn't a single winner: it's the crossover. Frequent reloads or a slow
volume favor VolumeCache; a single load per cold start on a fast volume favors
direct.

## Results (measured 2026-07-09)

RTX 4090 pod, EU-RO-1, 50GB MooseFS network volume, `stable-diffusion-v1-5`
(~8.5GB), 5 trials each, page cache evicted (`posix_fadvise`) before every read.

| metric | mean | stdev |
| --- | --- | --- |
| direct load (from volume) | **6.45s** | 0.19 |
| vc hydrate (volume→local copy) | 4.81s | 0.04 |
| vc first load (from local, after hydrate) | 2.21s | 0.02 |
| vc reload (from local, cold cache) | **1.76s** | 0.01 |

Storage: direct = 8.5GB on the volume; VolumeCache = ~4.3GB volume mirror + local copy (roughly double).

**Reading local is ~3.7× faster than reading the MooseFS volume** (1.76s vs 6.45s) — the volume read is a real bottleneck.

**Breakeven ≈ 1 load per worker:**
- Load **once** per cold worker: direct ≈ 6.45s vs VolumeCache ≈ hydrate 4.81s + load 2.21s ≈ **7.0s** — direct is simpler and marginally faster.
- Load **twice or more** per worker: VolumeCache wins decisively — each extra reload is 1.76s vs 6.45s. `direct = K×6.45` vs `volumecache = 4.81 + K×1.76`.

**Takeaway:** on this network volume, VolumeCache pays off when a worker (re)loads the model more than once (or for read-heavy repeated access); for a single load per cold start, caching directly on the volume is the simpler choice with equivalent latency. Both beat re-downloading from Hugging Face.

## Note

This script uses `runpod.serverless.VolumeCache` directly (no Flash). It is
Flash-independent and could equally live in the runpod-python repo; it sits here
alongside the rest of the VolumeCache benchmark work.
