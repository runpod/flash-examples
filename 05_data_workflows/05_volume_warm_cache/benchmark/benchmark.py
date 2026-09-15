#!/usr/bin/env python3
"""Drive the direct vs VolumeCache cold-start A/B and print a comparison.

Each worker measures its own model-load time during a cold start (in __init__)
and returns it from `benchmark()`. This runner triggers cold starts, collects
first-run and warm-run metrics for both strategies, and prints a table.

Prerequisites:
- Both endpoints deployed/served (see benchmark/README.md). The volumecache arm
  additionally requires a flash-worker image built against runpod>=1.12.0.
- A trial only measures a true cold start if the wait exceeds that arm's worker
  idle_timeout so it scales to 0 first (direct=30s, volumecache=180s). cold-wait
  is derived per arm from each idle_timeout plus a margin; a single shared wait
  would leave the longer-lived volumecache worker alive and report warm reuse as
  a cold start.

Usage:
    python benchmark.py --base-url http://localhost:8888 --warm-trials 3

Confirm the exact routes and response shape at <base-url>/docs; adjust
--direct-route / --vc-route if your deployment differs.
"""

import argparse
import json
import statistics
import time
import urllib.request

# Each benchmark worker's idle_timeout, mirrored from bench_direct.py /
# bench_volumecache.py. A warm trial only measures a real cold start if we wait
# past the worker's idle_timeout so it scales to 0 first; a shorter wait reuses
# the still-alive worker and silently reports warm-reuse time as a cold start.
DIRECT_IDLE_TIMEOUT = 30
VOLUMECACHE_IDLE_TIMEOUT = 180
# Extra seconds over idle_timeout to be sure the worker has scaled to 0.
COLD_WAIT_MARGIN = 15


def call(base_url: str, route: str, timeout: int) -> dict:
    """POST an empty job to a worker and return its benchmark metrics."""
    url = f"{base_url.rstrip('/')}/{route.strip('/')}"
    body = json.dumps({"input": {}}).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read())
    # flash runsync wraps the return value under "output"; tolerate either shape.
    return payload.get("output", payload)


def run_arm(base_url, route, warm_trials, cold_wait, timeout):
    """First-run (cold, empty cache) + N warm cold-starts for one strategy."""
    results = {"first_run": None, "warm": []}
    print(f"  [{route}] first run (empty cache; includes download)...")
    results["first_run"] = call(base_url, route, timeout)
    for i in range(warm_trials):
        print(
            f"  [{route}] waiting {cold_wait}s for scale-to-0, then warm cold start {i + 1}/{warm_trials}..."
        )
        time.sleep(cold_wait)
        results["warm"].append(call(base_url, route, timeout))
    return results


def gb(n):
    return f"{(n or 0) / (1024**3):.2f} GB"


def summarize(name, arm):
    warm_loads = [r["load_seconds"] for r in arm["warm"]] or [float("nan")]
    first = arm["first_run"]
    warm0 = arm["warm"][0] if arm["warm"] else {}
    return {
        "name": name,
        "first_run_load": first.get("load_seconds"),
        "warm_load_mean": round(statistics.fmean(warm_loads), 2),
        "warm_load_min": round(min(warm_loads), 2),
        "hydrate_seconds": warm0.get("hydrate_seconds", 0.0),
        "volume_bytes": warm0.get("volume_bytes", first.get("volume_bytes")),
        "local_bytes": warm0.get("local_bytes", first.get("local_bytes")),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8888")
    ap.add_argument("--direct-route", default="bench_direct/runsync")
    ap.add_argument("--vc-route", default="bench_volumecache/runsync")
    ap.add_argument("--warm-trials", type=int, default=3)
    ap.add_argument(
        "--cold-wait",
        type=int,
        default=None,
        help="override the scale-to-0 wait (seconds) for BOTH arms; by default "
        "each arm derives its own from its worker idle_timeout + margin "
        f"(direct {DIRECT_IDLE_TIMEOUT + COLD_WAIT_MARGIN}s, volumecache "
        f"{VOLUMECACHE_IDLE_TIMEOUT + COLD_WAIT_MARGIN}s)",
    )
    ap.add_argument("--timeout", type=int, default=1200)
    ap.add_argument(
        "--skip-volumecache",
        action="store_true",
        help="run only the direct arm (e.g. before flash-worker ships VolumeCache)",
    )
    args = ap.parse_args()

    direct_cold_wait = args.cold_wait or DIRECT_IDLE_TIMEOUT + COLD_WAIT_MARGIN
    vc_cold_wait = args.cold_wait or VOLUMECACHE_IDLE_TIMEOUT + COLD_WAIT_MARGIN

    print("Direct arm:")
    direct = run_arm(
        args.base_url,
        args.direct_route,
        args.warm_trials,
        direct_cold_wait,
        args.timeout,
    )
    rows = [summarize("direct", direct)]

    if not args.skip_volumecache:
        print("VolumeCache arm:")
        vc = run_arm(
            args.base_url, args.vc_route, args.warm_trials, vc_cold_wait, args.timeout
        )
        rows.append(summarize("volumecache", vc))

    print("\n=== Results ===")
    header = f"{'strategy':<14}{'first-run load':>16}{'warm load (mean)':>18}{'warm load (min)':>17}{'hydrate':>10}{'volume':>12}{'local':>12}"
    print(header)
    print("-" * len(header))
    for r in rows:
        print(
            f"{r['name']:<14}"
            f"{str(r['first_run_load']) + 's':>16}"
            f"{str(r['warm_load_mean']) + 's':>18}"
            f"{str(r['warm_load_min']) + 's':>17}"
            f"{str(r['hydrate_seconds']) + 's':>10}"
            f"{gb(r['volume_bytes']):>12}"
            f"{gb(r['local_bytes']):>12}"
        )


if __name__ == "__main__":
    main()
