# Quadrant benchmark: which transport strategy for which tree shape?

The `rigorous/` benchmark answered *should you cache on the volume at all*. This
one answers the follow-up: **when VolumeCache moves a tree between local disk and
the network volume, which transport strategy is fastest — and does the answer
depend on the tree's shape?**

VolumeCache today copies files one at a time. That is not obviously optimal.
Moving a cache tree pays two competing costs:

- **bulk throughput** — bytes/sec the volume can stream. Dominates for large
  files; the wire is the limit.
- **per-file metadata** — one open/create/stat round-trip per file over the
  network mount. Dominates for many small files; latency is the limit.

So the right strategy should depend on the tree's *shape*. This harness sweeps a
grid of shapes and, for each, times three strategies in both directions.

## Why serverless (not a pod)

This runs as a **Runpod serverless worker**, deliberately:

- `/runpod-volume` on a worker is the **real MooseFS mount VolumeCache ships
  against**. A pod is only a proxy for it; measuring on the actual substrate is
  what makes the thresholds trustworthy.
- It's a **CPU endpoint, no GPU** — this is storage transport, not compute.
- Page cache is dropped before every timed op with `posix_fadvise(DONTNEED)`,
  which needs no root and works inside the container — so none of the pod-only
  machinery (privileged `drop_caches`, cold-start control) is required.
- We control cache/dir state explicitly *within one invocation*, so there are no
  cold-start games to play — a single request measures clean transport.

`VolumeCache` itself is not imported: the `serial` strategy **is** what
VolumeCache does today (per-file copy); `parallel` and `tar` are the candidates
we're evaluating to add. So this needs neither a GPU nor a VolumeCache-capable
worker image.

## The quadrants (tree shapes)

| profile | files | per-file | total | stresses |
| --- | --- | --- | --- | --- |
| `few_small` | 8 | 4 MiB | 32 MiB | nothing — a cheap control |
| `few_large` | 8 | 256 MiB | 2 GiB | bulk throughput |
| `many_small` | 40,000 | 16 KiB | ~640 MiB | per-file metadata |
| `many_medium` | 3,000 | 1 MiB | ~3 GiB | the crossover zone |
| `mixed_hf` | 4 × 256 MiB + 8,000 × 8 KiB | — | ~2 GiB | both at once (like a real HF cache) |

Sized to fit a CPU endpoint's container disk (vCPU × 10 GB — `CPU3G_4_16` gives
~40 GB) and to keep each profile's invocation to a few minutes.

## The strategies

| strategy | mirror (local → volume) | hydrate (volume → local) |
| --- | --- | --- |
| `serial` | `copy2` each file, one at a time (today's VolumeCache) | same, reversed |
| `parallel` | `copy2` each file across N threads (default 16) | same, reversed |
| `tar` | one `tar` archive written to the volume (packed, no compression) | `tar -x` from the volume |

`tar` collapses N per-file metadata round-trips into a single sequential stream,
**but only if the volume stores the archive packed** — which the
write-once/read-many serverless cache lifecycle makes safe (one atomic writer
during mirror, readers only afterward).

## Method

- **N trials + 1 discarded warmup** per strategy per direction; reports mean,
  stdev, and MiB/s.
- **Cold page cache before every timed op** via `posix_fadvise(DONTNEED)` on the
  side about to be read.
- **Correctness gate.** After every hydrate the reconstructed tree is compared
  byte-for-byte against the source; a mismatch aborts the run.
- **Idempotent, zero-filled sources** written to overlay disk (not tmpfs). `tar`
  runs without compression and MooseFS doesn't dedup, so the bytes on the wire
  are real.
- **One profile per invocation** — the full sweep moves hundreds of GB, too long
  for a single request. The driver loops the profiles.

## Running

1. Deploy the worker (from this directory):

   ```bash
   flash deploy bench_quadrant.py
   ```

   It's a CPU endpoint with the `flash-05-bench-volume` network volume attached;
   no GPU, no extra dependencies.

2. Drive it. Against a deployed endpoint:

   ```bash
   RUNPOD_API_KEY=... python benchmark.py --endpoint-id <id> --trials 2
   ```

   Or against a local `flash dev` server (which dispatches to a real worker):

   ```bash
   flash dev            # in one shell
   python benchmark.py --base-url http://localhost:8888 --trials 2
   ```

   Confirm the route at `http://localhost:8888/docs` and pass `--route` if it
   differs. `--only many_small,few_large` runs a subset.

## Reading the output

Per profile you get mean seconds and MiB/s per strategy per direction, then a
summary matrix — the fastest strategy for each quadrant:

```
quadrant             files      size  mirror     hydrate
few / large              8     2.00GiB  parallel   parallel
many / small         40000     0.62GiB  tar        tar
mixed (HF-like)       8004     2.06GiB  ???        ???
```

The crossover is the whole point:

- **`tar` wins** → per-file metadata dominated; packing paid off.
- **`parallel` wins** → throughput dominated and threads hid the round-trips.
- **`serial` ties** → the tree was too small for strategy to matter.

Where the winner *flips* between `many_small` and `few_large` is the empirical
threshold (file count and/or mean file size) an adaptive VolumeCache should
switch on. The `mixed_hf` row shows whether one strategy serves a realistic tree
or whether a **bucketed hybrid** (tar the small-file tail, parallel-copy the
large-file head) is warranted.

## Results (measured 2026-07-09)

Runpod CPU serverless (`cpu3g-4-16`), 50 GB MooseFS network volume in EU-RO-1,
page cache evicted before every timed op. `trials=2` except `many_small`
(`trials=1`). The tables below are the record of that run; re-running the
benchmark writes its own `results.json` locally (gitignored).

### Summary matrix — fastest strategy per quadrant

| quadrant | files | mean file | mirror winner | hydrate winner |
| --- | ---: | ---: | --- | --- |
| few / small | 8 | 4 MiB | parallel | parallel |
| few / large | 8 | 256 MiB | parallel | parallel |
| many / medium | 3,000 | 1 MiB | parallel | parallel |
| mixed (HF-like) | 8,004 | ~139 KiB* | **tar** | **tar** |
| many / small | 40,000 | 16 KiB | **tar** | **tar** |

\* `mixed_hf` is bimodal: 4 × 256 MiB weights + 8,000 × 8 KiB metadata.

### Per-profile mirror (local → volume), mean seconds (MiB/s)

| profile | serial | parallel | tar |
| --- | --- | --- | --- |
| few_small | 0.09s (351) | **0.05s (659)** | 0.09s (355) |
| few_large | 2.67s (767) | **0.59s (3445)** | 5.32s (385) |
| many_medium | 31.5s (95) | **4.03s (745)** | 9.36s (321) |
| mixed_hf | 92.0s (12) | 12.6s (86) | **3.48s (312)** |
| many_small | 428.7s (1.5) | 62.0s (10) | **5.91s (106)** |

Hydrate (volume → local) tracks the same winners — see the hydrate column of the
summary matrix above.

### What the crossover says

The deciding variable is **mean file size** — throughput vs per-file metadata:

- **Large files (≥ ~1 MiB), any count → `parallel`.** On `few_large` and
  `many_medium`, 16 threads overlap the modest metadata round-trips and saturate
  throughput (3445 / 745 MiB/s). `tar` is pure overhead here — it serializes
  everything through one stream and actually *lost* `few_large` mirror at 5.32s
  vs parallel's 0.59s.
- **Many small files (≤ ~16 KiB) → `tar`.** On `many_small`, per-file metadata
  dominates: `tar` collapses 40,000 round-trips into one sequential stream and
  mirrors in **5.9s vs 62s parallel vs 428s serial** — **72× faster than serial,
  10× faster than parallel**.
- **`serial` (today's VolumeCache) never wins**, and degrades catastrophically
  with file count: 428s to mirror 40k tiny files (1.5 MiB/s). It is not viable as
  the sole strategy for small-file-heavy caches.
- **The mixed tree validates a bucketed hybrid.** `mixed_hf` is 1 GiB of big
  weights + 8,000 tiny files; `tar` won overall (3.48s) because the small-file
  *count* dominates the round-trip cost — but those 4 big files would move
  fastest via `parallel`. One uniform strategy leaves time on the table.

### Adaptive-transport thresholds for VolumeCache

1. **Profile the tree during the walk** (free): file count and a size histogram.
2. **Bucket by size at ~256 KiB.**
   - Files **< 256 KiB** → **tar** them into one packed archive on the volume
     (metadata collapse). The crossover sits between `many_medium` (1 MiB →
     parallel) and `mixed_hf`/`many_small` (≤139 KiB → tar); 256 KiB is a safe
     switch point.
   - Files **≥ 256 KiB** → **parallel** per-file copy (throughput + overlap).
3. **Degenerate cases collapse to one bucket:** an all-large tree is pure
   parallel; an all-tiny tree is a single tar — no hybrid overhead.
4. **Write an on-volume manifest** recording the layout (which files are in the
   archive vs copied) so hydrate is deterministic and can run the inverse in
   parallel. The write-once/read-many serverless lifecycle makes the packed
   archive safe: one atomic writer during mirror, readers only afterward.

Net: replacing `serial` with this size-bucketed tar+parallel hybrid turns the
worst case (40k small files: 428s) into ~6s and keeps the large-file case at
full parallel throughput.

## Note

The `many_small` (`serial`, 40k files) arm ran 428s and pushed the invocation to
1,408s total — long enough that the driver's `runsync` returned before the job
finished. The result was recovered from the endpoint's job-status API. In
production a small-file cache would use `tar`, not `serial`, so this is a
benchmark artifact, not a usage path.
