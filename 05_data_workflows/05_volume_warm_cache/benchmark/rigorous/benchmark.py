#!/usr/bin/env python3
"""Rigorous A/B: HF cache directly on a network volume vs runpod VolumeCache.

Runs on a Runpod **Pod** (GPU + a network volume at /runpod-volume), as root.
Deliberately NOT serverless: a pod gives a stable environment, root access to
drop the OS page cache between reads, and no cold-start scheduling noise — so we
measure the actual I/O tradeoff instead of worker-boot jitter.

Why this design (vs the naive serverless benchmark):
- Page cache is controlled. A model loaded once sits in RAM; a second load then
  hits RAM, not disk, and looks instant. We drop the page cache before every
  timed read so we measure true storage reads, not cache hits.
- We measure the PER-RELOAD cost and the BREAKEVEN, not one cold start. Key
  insight: on a single load, VolumeCache does more I/O than direct (it reads the
  model from the volume during hydrate AND reads it again from local during
  load; direct reads from the volume once). VolumeCache only wins when the model
  is (re)loaded enough times per worker for cheaper local reads to amortize the
  one-time hydrate copy. This harness finds that crossover.

Setup on the pod:
    pip install "runpod @ git+https://github.com/runpod/runpod-python.git@deanquinanola/sls-367-network-volume-warm-cache-for-serverless-volumecache" \
                diffusers transformers accelerate torch
    python benchmark.py --trials 5 --reloads 5

Requires root (for /proc/sys/vm/drop_caches) and a mounted network volume.
"""

import argparse
import gc
import os
import shutil
import statistics
import subprocess
import time

MODEL = "runwayml/stable-diffusion-v1-5"
VOLUME = "/runpod-volume"
VOLUME_HF = f"{VOLUME}/bench-hf-direct"  # direct strategy: HF cache ON the volume
LOCAL_HF = "/root/bench-hf-local"  # volumecache strategy: HF cache on local disk
VC_NAMESPACE = "bench-volumecache"


def evict(path):
    """Drop each file's pages from the page cache so the next read hits storage.

    Containers can't write /proc/sys/vm/drop_caches (read-only, needs a
    privileged host), so we evict per file with posix_fadvise(DONTNEED) — which
    needs no root and targets exactly the tree we're about to read.
    """
    subprocess.run(["sync"], check=False)
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                fd = os.open(os.path.join(root, name), os.O_RDONLY)
            except OSError:
                continue
            try:
                os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
            except OSError:
                pass
            finally:
                os.close(fd)


def dir_bytes(path):
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total


def load_model(cache_dir):
    """Load the pipeline from cache_dir; return load seconds. Frees it after."""
    import torch
    from diffusers import StableDiffusionPipeline

    t0 = time.perf_counter()
    pipe = StableDiffusionPipeline.from_pretrained(
        MODEL,
        cache_dir=cache_dir,
        torch_dtype=torch.float16,
        safety_checker=None,
        requires_safety_checker=False,
        use_safetensors=True,
        low_cpu_mem_usage=True,
    ).to("cuda")
    dt = time.perf_counter() - t0
    del pipe
    gc.collect()
    torch.cuda.empty_cache()
    return dt


def stats(label, xs, unit="s"):
    xs = list(xs)
    return (
        f"{label:<28} n={len(xs)}  "
        f"mean={statistics.fmean(xs):.2f}{unit}  "
        f"median={statistics.median(xs):.2f}{unit}  "
        f"min={min(xs):.2f}{unit}  max={max(xs):.2f}{unit}  "
        f"stdev={statistics.pstdev(xs):.2f}{unit}"
    )


def seed(vc):
    """One-time: populate the on-volume direct cache and the VolumeCache mirror."""
    if dir_bytes(VOLUME_HF) == 0:
        print("seeding direct cache on volume (download)...")
        os.makedirs(VOLUME_HF, exist_ok=True)
        _download(VOLUME_HF)
    if dir_bytes(LOCAL_HF) == 0:
        print("seeding local cache (download)...")
        os.makedirs(LOCAL_HF, exist_ok=True)
        _download(LOCAL_HF)
    print("syncing local -> volume mirror (blocking)...")
    t0 = time.perf_counter()
    vc.sync(background=False)
    print(
        f"  sync completed in {time.perf_counter() - t0:.1f}s; "
        f"mirror={dir_bytes(vc._mirror_root) / 1e9:.2f}GB"
    )


def _download(cache_dir):
    # Download only what this load config needs (~4GB safetensors), not the full
    # ~33GB repo (all .ckpt/.bin variants) — the volume quota and container disk
    # can't hold two full copies.
    import torch
    from diffusers import StableDiffusionPipeline

    StableDiffusionPipeline.from_pretrained(
        MODEL,
        cache_dir=cache_dir,
        torch_dtype=torch.float16,
        safety_checker=None,
        requires_safety_checker=False,
        use_safetensors=True,
    )
    del torch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--trials", type=int, default=5, help="first-load trials per strategy"
    )
    ap.add_argument("--reloads", type=int, default=5, help="reload trials per strategy")
    args = ap.parse_args()

    from runpod.serverless import VolumeCache

    if not os.path.isdir(VOLUME):
        raise SystemExit(f"No network volume mounted at {VOLUME}.")

    vc = VolumeCache(dirs=[LOCAL_HF], namespace=VC_NAMESPACE, volume_path=VOLUME)
    seed(vc)

    model_gb = dir_bytes(VOLUME_HF) / 1e9

    # --- Direct: every load reads the model from the volume (cold page cache) ---
    direct_loads = []
    for i in range(args.trials + 1):  # +1 warmup, discarded
        evict(VOLUME_HF)
        dt = load_model(VOLUME_HF)
        if i:
            direct_loads.append(dt)
        print(f"  direct load [{i}] {dt:.2f}s{' (warmup)' if not i else ''}")

    # --- VolumeCache first load on a fresh worker: hydrate (volume->local) + load ---
    vc_hydrate, vc_first_load = [], []
    for i in range(args.trials + 1):
        shutil.rmtree(
            LOCAL_HF, ignore_errors=True
        )  # simulate a fresh worker's empty local disk
        evict(vc._mirror_root)  # hydrate should read the mirror cold from the volume
        t0 = time.perf_counter()
        vc.hydrate()  # copy mirror (volume) -> local
        h = time.perf_counter() - t0
        # Load from local. In reality the just-copied files are warm in page cache
        # (a real cold worker benefits from this), so we do NOT drop caches here.
        ll = load_model(LOCAL_HF)
        if i:
            vc_hydrate.append(h)
            vc_first_load.append(ll)
        print(
            f"  vc first [{i}] hydrate={h:.2f}s load={ll:.2f}s{' (warmup)' if not i else ''}"
        )

    # --- Reload cost with the model already on local disk (cold page cache each) ---
    vc_reloads = []
    for i in range(args.reloads + 1):
        evict(LOCAL_HF)
        dt = load_model(LOCAL_HF)
        if i:
            vc_reloads.append(dt)
        print(f"  vc reload (local) [{i}] {dt:.2f}s{' (warmup)' if not i else ''}")

    # --- Report ---
    print("\n" + "=" * 72)
    print(f"Model: {MODEL}  (~{model_gb:.2f}GB)   volume={VOLUME}")
    print("=" * 72)
    print(stats("direct load (volume)", direct_loads))
    print(stats("vc hydrate (volume->local)", vc_hydrate))
    print(stats("vc first load (local)", vc_first_load))
    print(stats("vc reload (local)", vc_reloads))
    print(
        f"storage: volume(direct)={dir_bytes(VOLUME_HF) / 1e9:.2f}GB  "
        f"volume(mirror)={dir_bytes(vc._mirror_root) / 1e9:.2f}GB  "
        f"local={dir_bytes(LOCAL_HF) / 1e9:.2f}GB"
    )

    d = statistics.fmean(direct_loads)  # per-load cost, direct (volume)
    h = statistics.fmean(vc_hydrate)  # one-time hydrate cost, volumecache
    r = statistics.fmean(vc_reloads)  # per-load cost, volumecache (local)
    print("\n--- when does VolumeCache win? ---")
    print(f"direct cost for K loads      = K * {d:.2f}s")
    print(f"volumecache cost for K loads = {h:.2f}s (hydrate) + K * {r:.2f}s")
    if r < d:
        breakeven = h / (d - r)
        print(
            f"local reload is {d - r:.2f}s cheaper than a volume load; "
            f"VolumeCache breaks even at K = {breakeven:.1f} loads per worker."
        )
    else:
        print(
            f"local reload ({r:.2f}s) is NOT cheaper than a volume load ({d:.2f}s) here, "
            f"so VolumeCache never wins for this model/volume — direct is simpler and faster."
        )


if __name__ == "__main__":
    main()
