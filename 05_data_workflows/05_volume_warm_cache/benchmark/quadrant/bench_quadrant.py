# Quadrant transport benchmark, as a Runpod serverless worker.
#
# Answers: when VolumeCache moves a cache tree between local disk and the network
# volume, which transport strategy is fastest — and does it depend on the tree's
# shape? Two costs compete: bulk throughput (large files) vs per-file metadata
# round-trips over the network mount (many small files). The right strategy
# should depend on file count x file size, so this sweeps a grid of shapes.
#
# Runs on serverless ON PURPOSE (not a pod): /runpod-volume here is the real
# MooseFS mount VolumeCache ships against, so we measure the actual substrate.
# CPU endpoint, no GPU — this is storage transport, not compute. VolumeCache
# itself isn't imported: the `serial` strategy IS what VolumeCache does today
# (per-file copy); `parallel` and `tar` are the candidates we're evaluating to
# add. So this needs neither a GPU nor a VolumeCache-capable worker image.
#
# One invocation runs ONE profile (the full sweep moves hundreds of GB — too
# long for a single request); the driver (benchmark.py) loops the profiles.
#
# Everything lives inside the handler method: @Endpoint ships only the function
# body to the worker, so module-level helpers/constants wouldn't exist remotely.
#
# deploy with: flash deploy   (see README.md)
import logging

from runpod_flash import CpuInstanceType, Endpoint, NetworkVolume

logger = logging.getLogger(__name__)

# Same volume as the other bench arms so every strategy competes on one medium.
volume = NetworkVolume(name="flash-05-bench-volume", size=50)


@Endpoint(
    name="bench_quadrant",
    cpu=CpuInstanceType.CPU3G_4_16,  # 4 vCPU / 16GB RAM / ~40GB disk, no GPU
    workers=(0, 1),
    idle_timeout=60,
    volume=volume,
)
class BenchQuadrant:
    def __init__(self):
        pass

    async def run(
        self, profile: str = "many_small", trials: int = 2, workers: int = 16
    ) -> dict:
        """Benchmark one profile: 3 strategies x 2 directions, cold page cache.

        Returns per-strategy mean mirror/hydrate seconds + MiB/s, plus the tree's
        file count and total bytes. A byte-for-byte gate aborts on any mismatch.
        """
        import os
        import shutil
        import statistics
        import subprocess
        import time
        from concurrent.futures import ThreadPoolExecutor

        KIB, MIB, GIB = 1 << 10, 1 << 20, 1 << 30
        WRITE_CHUNK = 8 << 20
        ZERO = b"\x00" * WRITE_CHUNK
        VOLUME = "/runpod-volume"
        VOL_ROOT = f"{VOLUME}/quadrant"
        LOCAL_SRC = "/quadrant-local/src"  # overlay disk, not tmpfs
        LOCAL_DST = "/quadrant-local/dst"

        # (files uniform) name -> (count, size_bytes); mixed uses parts below.
        catalog = {
            "few_small": [(8, 4 * MIB)],
            "few_large": [(8, 256 * MIB)],
            "many_small": [(40_000, 16 * KIB)],
            "many_medium": [(3_000, 1 * MIB)],
            "mixed_hf": [(4, 256 * MIB), (8_000, 8 * KIB)],
        }
        if profile not in catalog:
            raise ValueError(f"unknown profile {profile!r}; have {list(catalog)}")

        def write_file(path, size):
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
            try:
                left = size
                while left > 0:
                    n = WRITE_CHUNK if left >= WRITE_CHUNK else left
                    os.write(fd, ZERO if n == WRITE_CHUNK else ZERO[:n])
                    left -= n
            finally:
                os.close(fd)

        def generate(root, parts):
            # Fan files across subdirs (1000/dir) so a huge flat directory index
            # doesn't dominate; idempotent so re-invocations reuse the tree.
            base = 0
            for count, size in parts:
                for i in range(count):
                    sub = os.path.join(root, f"p{base}", f"d{i // 1000:04d}")
                    os.makedirs(sub, exist_ok=True)
                    tgt = os.path.join(sub, f"f{i:06d}.bin")
                    if os.path.exists(tgt) and os.path.getsize(tgt) == size:
                        continue
                    write_file(tgt, size)
                base += 1

        def tree_stats(path):
            count = total = 0
            for r, _d, fs in os.walk(path):
                for name in fs:
                    try:
                        total += os.path.getsize(os.path.join(r, name))
                        count += 1
                    except OSError:
                        pass
            return count, total

        def evict(path):
            # Drop pages so the next read hits storage. Containers can't write
            # /proc/sys/vm/drop_caches, so evict per file with posix_fadvise.
            subprocess.run(["sync"], check=False)
            if not hasattr(os, "posix_fadvise"):
                return
            for r, _d, fs in os.walk(path):
                for name in fs:
                    try:
                        fd = os.open(os.path.join(r, name), os.O_RDONLY)
                    except OSError:
                        continue
                    try:
                        os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
                    except OSError:
                        pass
                    finally:
                        os.close(fd)

        def pairs(src, dst):
            for r, _d, fs in os.walk(src):
                rel = os.path.relpath(r, src)
                for name in fs:
                    yield os.path.join(r, name), os.path.join(dst, rel, name)

        def copy_serial(src, dst):
            for s, d in pairs(src, dst):
                os.makedirs(os.path.dirname(d), exist_ok=True)
                shutil.copy2(s, d)

        def copy_parallel(src, dst):
            for r, _d, _fs in os.walk(src):
                os.makedirs(os.path.join(dst, os.path.relpath(r, src)), exist_ok=True)
            with ThreadPoolExecutor(max_workers=workers) as pool:
                list(pool.map(lambda p: shutil.copy2(*p), pairs(src, dst)))

        def tar_pack(src, area):
            subprocess.run(
                ["tar", "-C", src, "-cf", os.path.join(area, "cache.tar"), "."],
                check=True,
            )

        def tar_unpack(area, dst):
            subprocess.run(
                ["tar", "-C", dst, "-xf", os.path.join(area, "cache.tar")], check=True
            )

        # strategy -> (pack(src, area), unpack(area, dst), evict_source(area))
        mirror_sub = "mirror"
        strategies = {
            "serial": (
                lambda s, a: copy_serial(s, os.path.join(a, mirror_sub)),
                lambda a, d: copy_serial(os.path.join(a, mirror_sub), d),
                lambda a: os.path.join(a, mirror_sub),
            ),
            "parallel": (
                lambda s, a: copy_parallel(s, os.path.join(a, mirror_sub)),
                lambda a, d: copy_parallel(os.path.join(a, mirror_sub), d),
                lambda a: os.path.join(a, mirror_sub),
            ),
        }
        have_tar = shutil.which("tar") is not None
        if have_tar:
            strategies["tar"] = (tar_pack, tar_unpack, lambda a: a)

        def timed(fn):
            t0 = time.perf_counter()
            fn()
            return time.perf_counter() - t0

        # --- generate the source tree once (reused across strategies) ---
        src = os.path.join(LOCAL_SRC, profile)
        os.makedirs(src, exist_ok=True)
        os.makedirs(VOL_ROOT, exist_ok=True)
        generate(src, catalog[profile])
        count, total = tree_stats(src)

        results = {}
        for name, (pack, unpack, evict_src) in strategies.items():
            area = os.path.join(VOL_ROOT, profile, name)
            dst = os.path.join(LOCAL_DST, profile, name)
            mirror_t, hydrate_t = [], []
            for i in range(trials + 1):  # +1 warmup, discarded
                shutil.rmtree(area, ignore_errors=True)
                os.makedirs(area, exist_ok=True)
                evict(src)
                m = timed(lambda: pack(src, area))

                shutil.rmtree(dst, ignore_errors=True)
                os.makedirs(dst, exist_ok=True)
                evict(evict_src(area))
                h = timed(lambda: unpack(area, dst))

                got_count, got_bytes = tree_stats(dst)
                if got_bytes != total:
                    raise RuntimeError(
                        f"{name}: hydrate mismatch — expected {total} bytes, "
                        f"got {got_bytes} across {got_count} files"
                    )
                if i:
                    mirror_t.append(m)
                    hydrate_t.append(h)
            shutil.rmtree(area, ignore_errors=True)
            shutil.rmtree(dst, ignore_errors=True)

            def mbps(secs):
                return round((total / MIB) / secs, 1) if secs else 0.0

            mm, hh = statistics.fmean(mirror_t), statistics.fmean(hydrate_t)
            results[name] = {
                "mirror_s": round(mm, 3),
                "hydrate_s": round(hh, 3),
                "mirror_mibps": mbps(mm),
                "hydrate_mibps": mbps(hh),
                "mirror_stdev": round(statistics.pstdev(mirror_t), 3),
                "hydrate_stdev": round(statistics.pstdev(hydrate_t), 3),
            }

        # Clean the volume so repeated runs and the sibling arms start fresh.
        shutil.rmtree(os.path.join(VOL_ROOT, profile), ignore_errors=True)

        mirror_winner = min(results, key=lambda k: results[k]["mirror_s"])
        hydrate_winner = min(results, key=lambda k: results[k]["hydrate_s"])
        return {
            "profile": profile,
            "file_count": count,
            "total_bytes": total,
            "total_gib": round(total / GIB, 3),
            "trials": trials,
            "workers": workers,
            "tar_available": have_tar,
            "strategies": results,
            "mirror_winner": mirror_winner,
            "hydrate_winner": hydrate_winner,
        }
