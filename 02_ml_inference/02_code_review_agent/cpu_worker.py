# code review orchestrator: validates diffs, dispatches to Kimi-K2 GPU worker,
# returns structured JSON or formatted markdown reports.
# run with: flash run
# test directly: python cpu_worker.py
import json
import re

from prompts import RETRY_PROMPT, SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from runpod_flash import Endpoint

MAX_DIFF_BYTES = 20 * 1024  # 20KB ~ 5-6K tokens, fits in 8192 context with output room
HEALTH_TIMEOUT_SECONDS = 5

api = Endpoint(
    name="02_02_kimi_k2_review",
    cpu="cpu3c-1-2",
    workers=(1, 3),
)


def _validate_diff(diff: str) -> str | None:
    """Return an error message if the diff is invalid, None if valid."""
    if not diff or not diff.strip():
        return "Diff is empty"
    if len(diff.encode("utf-8")) > MAX_DIFF_BYTES:
        return f"Diff too large (max {MAX_DIFF_BYTES // 1024}KB). Split into smaller reviews."
    return None


def _strip_binary_hunks(diff: str) -> str:
    """Remove binary file diffs, keeping only text changes."""
    lines = diff.splitlines(keepends=True)
    result = []
    skip = False
    for line in lines:
        if line.startswith("Binary files ") or line.startswith("GIT binary patch"):
            skip = True
            continue
        if skip and line.startswith("diff --git "):
            skip = False
        if not skip:
            result.append(line)
    return "".join(result)


def _parse_llm_json(text: str) -> dict | None:
    """Extract JSON from LLM output, handling markdown fences and preamble."""
    # try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # strip markdown fences
    fenced = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    # find first { to last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    return None


def _compute_stats(comments: list[dict]) -> dict:
    """Compute severity counts from comment list."""
    stats = {"critical": 0, "warning": 0, "suggestion": 0, "nitpick": 0}
    for comment in comments:
        severity = comment.get("severity", "")
        if severity in stats:
            stats[severity] += 1
    return stats


def _format_markdown(review: dict) -> str:
    """Convert structured review JSON to a markdown report."""
    lines = ["# Code Review", ""]

    summary = review.get("summary", "No summary provided.")
    lines.extend(["## Summary", summary, ""])

    comments = review.get("comments", [])
    by_severity = {"critical": [], "warning": [], "suggestion": [], "nitpick": []}
    for c in comments:
        severity = c.get("severity", "suggestion")
        by_severity.setdefault(severity, []).append(c)

    section_names = {
        "critical": "Critical Issues",
        "warning": "Warnings",
        "suggestion": "Suggestions",
        "nitpick": "Nitpicks",
    }

    for severity, title in section_names.items():
        items = by_severity.get(severity, [])
        lines.append(f"## {title}")
        if not items:
            lines.extend(["(none)", ""])
            continue
        for c in items:
            file = c.get("file", "unknown")
            line_num = c.get("line", "?")
            category = c.get("category", "")
            issue = c.get("issue", "")
            suggestion = c.get("suggestion", "")
            lines.append(f"### {file}:{line_num} -- {category}")
            lines.append(issue)
            if suggestion:
                lines.append(f"**Suggestion:** {suggestion}")
            lines.append("")

    positive = review.get("positive_notes", [])
    lines.append("## Positive Notes")
    if positive:
        for note in positive:
            lines.append(f"- {note}")
    else:
        lines.append("(none)")
    lines.append("")

    return "\n".join(lines)


async def _call_generate(messages: list[dict], max_tokens: int = 4096) -> dict:
    """Call the GPU worker's generate function."""
    from gpu_worker import generate

    return await generate(
        {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.1,
            "top_p": 0.95,
        }
    )


async def _check_gpu_health() -> dict:
    """Call the GPU worker's health function with timeout handling."""
    import asyncio

    from gpu_worker import health as gpu_health

    try:
        result = await asyncio.wait_for(
            gpu_health({}),
            timeout=HEALTH_TIMEOUT_SECONDS,
        )
        return result
    except asyncio.TimeoutError:
        return {"status": "degraded", "detail": "GPU worker health check timed out"}
    except Exception as e:
        return {"status": "degraded", "detail": str(e)}


async def _run_review(diff: str) -> dict:
    """Core review logic shared by JSON and markdown routes."""
    # validate
    error = _validate_diff(diff)
    if error:
        return {"error_code": 400, "error": error}

    # strip binary hunks
    cleaned_diff = _strip_binary_hunks(diff)
    if not cleaned_diff.strip():
        return {"error_code": 400, "error": "Diff contains only binary files"}

    # health check
    gpu_status = await _check_gpu_health()
    if gpu_status.get("status") not in ("ready",):
        status = gpu_status.get("status", "unknown")
        if status == "loading":
            return {"error_code": 503, "error": "Model loading", "retry_after": 60}
        return {
            "error_code": 503,
            "error": f"GPU worker unavailable (status: {status})",
        }

    # generate review
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT_TEMPLATE.format(diff=cleaned_diff)},
    ]

    result = await _call_generate(messages)
    if result.get("status") != "success":
        return {"error_code": 502, "error": result.get("error", "Generation failed")}

    # parse LLM output
    review = _parse_llm_json(result["text"])

    if review is None:
        # retry once with stricter prompt
        messages.append({"role": "assistant", "content": result["text"]})
        messages.append({"role": "user", "content": RETRY_PROMPT})
        retry_result = await _call_generate(messages, max_tokens=4096)
        if retry_result.get("status") == "success":
            review = _parse_llm_json(retry_result["text"])

    if review is None:
        return {
            "error_code": 502,
            "error": "Failed to parse review",
            "raw_response": result["text"][:2000],
        }

    # normalize and add stats
    comments = review.get("comments", [])
    review["stats"] = _compute_stats(comments)
    return review


@api.post("/review/json")
async def review_json(diff: str) -> dict:
    """
    Review a unified diff and return structured JSON feedback.

    Args:
        diff: Unified diff string (max 20KB)

    Returns:
        Structured review with summary, comments, and stats
    """
    return await _run_review(diff)


@api.post("/review/markdown")
async def review_markdown(diff: str) -> dict:
    """
    Review a unified diff and return a formatted markdown report.

    Args:
        diff: Unified diff string (max 20KB)

    Returns:
        markdown: Formatted review report
    """
    result = await _run_review(diff)

    # error responses include "error_code" field; pass through as-is
    if "error_code" in result:
        return result

    return {"markdown": _format_markdown(result)}


@api.get("/review/health")
async def review_health() -> dict:
    """Aggregate health check: orchestrator + GPU worker status."""
    gpu_status = await _check_gpu_health()
    gpu = gpu_status.get("status", "unknown")

    if gpu == "ready":
        overall = "ready"
    elif gpu == "loading":
        overall = "loading"
    else:
        overall = "degraded"

    return {
        "orchestrator": "ready",
        "gpu_worker": gpu,
        "status": overall,
    }


if __name__ == "__main__":
    import asyncio
    from pathlib import Path

    async def test():
        print("=== Testing diff validation ===")
        result = await review_json("")
        print(f"Empty diff: {result}\n")

        print("=== Testing review pipeline ===")
        diff_path = Path(__file__).parent / "sample_diffs" / "security_bug.diff"
        if diff_path.exists():
            diff_text = diff_path.read_text()
            print(f"Loaded diff: {len(diff_text)} bytes")

            print("\n--- JSON review ---")
            result = await review_json(diff_text)
            print(json.dumps(result, indent=2))

            print("\n--- Markdown review ---")
            result = await review_markdown(diff_text)
            if "markdown" in result:
                print(result["markdown"])
            else:
                print(result)
        else:
            print(f"Sample diff not found at {diff_path}")

        print("\n=== Testing health ===")
        result = await review_health()
        print(f"Health: {result}")

    asyncio.run(test())
