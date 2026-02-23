"""Load test script for autoscaling examples.

Sends concurrent requests in phases to observe scaling behavior:
1. Warm-up -- single request to establish baseline
2. Burst -- concurrent requests to trigger scale-up
3. Pause -- idle period to observe scale-down
4. Second burst -- measure cold vs warm start difference

Usage:
    python load_test.py
    python load_test.py --url http://localhost:8888 --concurrency 10 --requests 50
    python load_test.py --endpoint /gpu_worker/runsync --pause 30
"""

import argparse
import asyncio
import statistics
import time

import aiohttp

DEFAULT_URL = "http://localhost:8888"
DEFAULT_ENDPOINT = "/gpu_worker/runsync"
DEFAULT_PAYLOAD = {"matrix_size": 256}


async def send_request(
    session: aiohttp.ClientSession,
    url: str,
    payload: dict,
) -> dict:
    """Send a single request and return timing data."""
    start = time.perf_counter()
    try:
        async with session.post(url, json=payload) as resp:
            body = await resp.json()
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "status": resp.status,
                "duration_ms": duration_ms,
                "success": resp.status == 200,
                "body": body,
            }
    except Exception as e:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "status": 0,
            "duration_ms": duration_ms,
            "success": False,
            "error": str(e),
        }


async def run_burst(
    session: aiohttp.ClientSession,
    url: str,
    payload: dict,
    count: int,
    concurrency: int,
) -> list[dict]:
    """Send a burst of concurrent requests with a concurrency limit."""
    semaphore = asyncio.Semaphore(concurrency)
    results = []

    async def limited_request() -> dict:
        async with semaphore:
            return await send_request(session, url, payload)

    tasks = [limited_request() for _ in range(count)]
    results = await asyncio.gather(*tasks)
    return list(results)


def compute_stats(results: list[dict]) -> dict:
    """Compute latency percentiles and error rate from results."""
    durations = [r["duration_ms"] for r in results]
    successes = sum(1 for r in results if r["success"])
    errors = len(results) - successes

    if not durations:
        return {"count": 0, "errors": 0, "error_rate": 0}

    durations_sorted = sorted(durations)
    p50_idx = int(len(durations_sorted) * 0.50)
    p95_idx = int(len(durations_sorted) * 0.95)
    p99_idx = int(len(durations_sorted) * 0.99)

    return {
        "count": len(results),
        "successes": successes,
        "errors": errors,
        "error_rate": round(errors / len(results) * 100, 2),
        "min_ms": round(min(durations), 2),
        "max_ms": round(max(durations), 2),
        "mean_ms": round(statistics.mean(durations), 2),
        "p50_ms": round(durations_sorted[p50_idx], 2),
        "p95_ms": round(durations_sorted[min(p95_idx, len(durations_sorted) - 1)], 2),
        "p99_ms": round(durations_sorted[min(p99_idx, len(durations_sorted) - 1)], 2),
    }


def print_stats(label: str, stats: dict) -> None:
    """Print formatted statistics for a phase."""
    print(f"\n--- {label} ---")
    print(
        f"  Requests:   {stats['count']} ({stats['successes']} ok, {stats['errors']} errors)"
    )
    print(f"  Error rate: {stats['error_rate']}%")
    if stats["count"] > 0 and stats.get("min_ms") is not None:
        print(
            f"  Latency:    min={stats['min_ms']}ms  mean={stats['mean_ms']}ms  max={stats['max_ms']}ms"
        )
        print(
            f"  Percentiles: p50={stats['p50_ms']}ms  p95={stats['p95_ms']}ms  p99={stats['p99_ms']}ms"
        )


async def run_load_test(args: argparse.Namespace) -> None:
    """Execute the four-phase load test."""
    url = f"{args.url}{args.endpoint}"
    payload = DEFAULT_PAYLOAD

    print(f"Target: {url}")
    print(f"Concurrency: {args.concurrency}  |  Requests per burst: {args.requests}")
    print(f"Pause between bursts: {args.pause}s")

    timeout = aiohttp.ClientTimeout(total=args.timeout)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Phase 1: Warm-up
        print("\n[Phase 1] Warm-up: 1 request")
        warmup = await run_burst(session, url, payload, count=1, concurrency=1)
        print_stats("Warm-up", compute_stats(warmup))

        # Phase 2: First burst
        print(f"\n[Phase 2] Burst: {args.requests} concurrent requests")
        burst1_start = time.perf_counter()
        burst1 = await run_burst(
            session, url, payload, count=args.requests, concurrency=args.concurrency
        )
        burst1_wall = round((time.perf_counter() - burst1_start) * 1000, 2)
        stats1 = compute_stats(burst1)
        print_stats(f"First Burst (wall time: {burst1_wall}ms)", stats1)

        # Phase 3: Pause
        print(f"\n[Phase 3] Pause: waiting {args.pause}s for idle timeout / scale-down")
        await asyncio.sleep(args.pause)

        # Phase 4: Second burst (cold vs warm comparison)
        print(f"\n[Phase 4] Second burst: {args.requests} concurrent requests")
        burst2_start = time.perf_counter()
        burst2 = await run_burst(
            session, url, payload, count=args.requests, concurrency=args.concurrency
        )
        burst2_wall = round((time.perf_counter() - burst2_start) * 1000, 2)
        stats2 = compute_stats(burst2)
        print_stats(f"Second Burst (wall time: {burst2_wall}ms)", stats2)

        # Summary
        print("\n=== Summary ===")
        if stats1.get("mean_ms") and stats2.get("mean_ms"):
            diff = round(stats2["mean_ms"] - stats1["mean_ms"], 2)
            direction = "slower" if diff > 0 else "faster"
            print(f"  Second burst was {abs(diff)}ms {direction} on average")
            print(
                f"  First burst p95: {stats1['p95_ms']}ms  |  Second burst p95: {stats2['p95_ms']}ms"
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load test for Flash autoscaling examples"
    )
    parser.add_argument(
        "--url", default=DEFAULT_URL, help=f"Base URL (default: {DEFAULT_URL})"
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT,
        help=f"Endpoint path (default: {DEFAULT_ENDPOINT})",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Max concurrent requests (default: 10)",
    )
    parser.add_argument(
        "--requests", type=int, default=20, help="Requests per burst (default: 20)"
    )
    parser.add_argument(
        "--pause",
        type=int,
        default=10,
        help="Pause between bursts in seconds (default: 10)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Request timeout in seconds (default: 60)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(run_load_test(parse_args()))
