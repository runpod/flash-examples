#!/usr/bin/env python3
"""Drive the quadrant transport benchmark and print the crossover matrix.

The worker (bench_quadrant.py) runs one profile per invocation — 3 strategies
(serial / parallel / tar) x 2 directions (mirror local->volume, hydrate
volume->local) against the real /runpod-volume mount, with the page cache
dropped before every timed op. This runner calls it once per profile and renders
the fastest strategy per tree shape — the empirical basis for adaptive
transport thresholds in VolumeCache.

Two ways to reach the worker:

  flash dev (local dev server, dispatches to a real worker):
      python benchmark.py --base-url http://localhost:8888

  deployed endpoint (flash deploy):
      RUNPOD_API_KEY=... python benchmark.py --endpoint-id <id>

Confirm the exact route at <base-url>/docs (dev) — pass --route if it differs.
Results are printed and written to results.json for the README.
"""

import argparse
import json
import os
import time
import urllib.request

PROFILES = ("few_small", "few_large", "many_small", "many_medium", "mixed_hf")
QUADRANT_LABEL = {
    "few_small": "few / small",
    "few_large": "few / large",
    "many_small": "many / small",
    "many_medium": "many / medium",
    "mixed_hf": "mixed (HF-like)",
}


def _post(url: str, body: dict, headers: dict, timeout: int) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def call_profile(args, profile: str) -> dict:
    """Invoke the worker for one profile; return its output dict."""
    payload = {
        "input": {"profile": profile, "trials": args.trials, "workers": args.workers}
    }
    headers = {"Content-Type": "application/json"}
    if args.endpoint_id:
        url = f"https://api.runpod.ai/v2/{args.endpoint_id}/runsync"
        key = os.environ.get("RUNPOD_API_KEY")
        if not key:
            raise SystemExit("RUNPOD_API_KEY is required with --endpoint-id")
        headers["Authorization"] = f"Bearer {key}"
    else:
        url = f"{args.base_url.rstrip('/')}/{args.route.strip('/')}"
    resp = _post(url, payload, headers, args.timeout)
    # flash runsync / runpod both wrap the return under "output".
    return resp.get("output", resp)


def _mibps_row(name: str, s: dict) -> str:
    return (
        f"    {name:<10} "
        f"{s['mirror_s']:>7.2f}s ({s['mirror_mibps']:>7.1f})   "
        f"{s['hydrate_s']:>7.2f}s ({s['hydrate_mibps']:>7.1f})"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-url", default="http://localhost:8888")
    ap.add_argument("--route", default="bench_quadrant/run/runsync")
    ap.add_argument(
        "--endpoint-id", default="", help="deployed endpoint id (uses RUNPOD_API_KEY)"
    )
    ap.add_argument("--trials", type=int, default=2)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument(
        "--only", default="", help="comma-separated profiles (default: all)"
    )
    ap.add_argument("--out", default="results.json")
    args = ap.parse_args()

    selected = [p for p in PROFILES if not args.only or p in args.only.split(",")]
    if not selected:
        raise SystemExit(f"No profiles matched --only={args.only!r}")

    results = {}
    for profile in selected:
        print(f"\n=== {profile} ({QUADRANT_LABEL[profile]}) ===")
        t0 = time.perf_counter()
        out = call_profile(args, profile)
        results[profile] = out
        strat = out["strategies"]
        print(
            f"  {out['file_count']} files, {out['total_gib']:.2f}GiB  "
            f"(took {time.perf_counter() - t0:.0f}s)"
        )
        print(f"    {'strategy':<10} {'mirror (L->V)':<20} {'hydrate (V->L)':<20}")
        for name in strat:
            print(_mibps_row(name, strat[name]))
        print(
            f"    winner: mirror={out['mirror_winner']}  hydrate={out['hydrate_winner']}"
        )

    print("\n" + "=" * 72)
    print("SUMMARY — fastest strategy per quadrant")
    print("=" * 72)
    print(f"{'quadrant':<18} {'files':>7} {'size':>10}  {'mirror':<10} {'hydrate':<10}")
    for profile in selected:
        out = results[profile]
        print(
            f"{QUADRANT_LABEL[profile]:<18} "
            f"{out['file_count']:>7} "
            f"{out['total_gib']:>8.2f}GiB  "
            f"{out['mirror_winner']:<10} "
            f"{out['hydrate_winner']:<10}"
        )
    print(
        "\nWhere 'tar' wins, per-file metadata dominated; where 'parallel' wins, "
        "throughput did and threads hid the round-trips; where 'serial' ties, the "
        "tree was too small to matter."
    )

    with open(args.out, "w") as fh:
        json.dump(results, fh, indent=2)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
