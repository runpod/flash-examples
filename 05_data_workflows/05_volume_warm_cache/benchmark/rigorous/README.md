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
pip install "runpod @ git+https://github.com/runpod/runpod-python.git@deanquinanola/sls-367-network-volume-warm-cache-for-serverless-volumecache" \
            diffusers transformers accelerate torch
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

## Note

This script uses `runpod.serverless.VolumeCache` directly (no Flash). It is
Flash-independent and could equally live in the runpod-python repo; it sits here
alongside the rest of the VolumeCache benchmark work.
