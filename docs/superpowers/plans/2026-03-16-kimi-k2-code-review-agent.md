# Kimi-K2 Code Review Agent Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a two-worker Flash example that self-hosts Kimi-K2-Instruct via vLLM on 8xH100 GPUs and exposes PR diff code review through CPU LB endpoints returning JSON and markdown.

**Architecture:** GPU worker (QB) hosts vLLM with a pre-quantized W4A16 Kimi-K2 model, exposing `generate` and `health` functions. CPU worker (LB) validates diffs, constructs prompts, dispatches to GPU, and formats responses as structured JSON or markdown reports. Cross-worker orchestration follows the `03_mixed_workers/pipeline.py` pattern.

**Tech Stack:** `runpod_flash` (Endpoint, GpuType), `vllm` (LLM engine), stdlib `re`/`json` (diff parsing, response parsing)

**Spec:** `docs/superpowers/specs/2026-03-16-kimi-k2-code-review-agent-design.md`

**Commit workflow:** Do NOT commit after each task. Accumulate all files and commit once after `make format && make lint-fix && make quality-check` passes in the final task. Use `git commit --no-verify` since quality checks already passed. Do NOT add `Co-Authored-By` lines to any commits.

---

## Chunk 1: Prompt Templates and Sample Diffs

### Task 1: Create prompts.py

**Files:**
- Create: `02_ml_inference/02_code_review_agent/prompts.py`

- [ ] **Step 1: Create the prompts file with system and user prompt constants**

```python
# prompt templates for the Kimi-K2 code review agent.
# imported by cpu_worker.py at module level (plain string constants, no side effects).

SYSTEM_PROMPT = """\
You are a senior code reviewer. Analyze the unified diff provided and return a JSON object with your review.

Output schema (respond with ONLY this JSON, no markdown fences, no explanation):
{
  "summary": "1-2 sentence overall assessment",
  "comments": [
    {
      "file": "path/to/file.py",
      "line": 42,
      "severity": "critical|warning|suggestion|nitpick",
      "category": "security|bug|performance|style|logic",
      "issue": "What is wrong",
      "suggestion": "How to fix it"
    }
  ],
  "positive_notes": ["Good things about the code"]
}

Severity levels:
- critical: bugs, security vulnerabilities, data loss risks
- warning: logic issues, missing error handling, race conditions
- suggestion: readability improvements, better abstractions, missing docs
- nitpick: style, naming conventions, formatting

Categories: security, bug, performance, style, logic

Rules:
- Reference exact file paths and line numbers from the diff
- Line numbers refer to the NEW file (lines starting with +)
- Include positive_notes when code is well-written
- If the diff is clean with no issues, say so in the summary and return empty comments
- Be specific and actionable in suggestions
"""

USER_PROMPT_TEMPLATE = """\
Review the following unified diff:

```diff
{diff}
```

Respond with ONLY a JSON object matching the schema above. No markdown fences around the JSON.\
"""

RETRY_PROMPT = """\
Your previous response was not valid JSON. Respond with ONLY a raw JSON object matching the schema. \
No markdown fences, no explanation, no text before or after the JSON.\
"""
```

- [ ] **Step 2: Verify the file is syntactically valid**

Run: `cd /Users/deanquinanola/Github/python/flash-project/flash-examples/main && python -c "from importlib.util import spec_from_file_location, module_from_spec; s = spec_from_file_location('prompts', '02_ml_inference/02_code_review_agent/prompts.py'); m = module_from_spec(s); s.loader.exec_module(m); print('SYSTEM_PROMPT length:', len(m.SYSTEM_PROMPT)); print('USER_PROMPT_TEMPLATE length:', len(m.USER_PROMPT_TEMPLATE)); print('RETRY_PROMPT length:', len(m.RETRY_PROMPT))"`
Expected: Three length lines printed, no errors.

### Task 2: Create sample diffs

**Files:**
- Create: `02_ml_inference/02_code_review_agent/sample_diffs/security_bug.diff`
- Create: `02_ml_inference/02_code_review_agent/sample_diffs/style_issues.diff`

- [ ] **Step 1: Create security_bug.diff**

This diff should contain a SQL injection vulnerability and unescaped user input. Write a realistic unified diff that adds a database query function with string concatenation:

```diff
--- a/src/auth.py
+++ b/src/auth.py
@@ -1,5 +1,6 @@
 import sqlite3
 from flask import request, jsonify
+from markupsafe import escape


 def get_db():
@@ -10,6 +11,22 @@ def get_db():
     return db


+def get_user(user_id):
+    """Look up a user by ID."""
+    db = get_db()
+    query = "SELECT * FROM users WHERE id = '" + user_id + "'"
+    result = db.execute(query).fetchone()
+    if result is None:
+        return {"error": "User not found"}, 404
+    return dict(result)
+
+
+def render_comment(comment_text):
+    """Render a user comment for display."""
+    return f"<div class='comment'>{comment_text}</div>"
+
+
 def login(username, password):
     """Authenticate a user."""
     db = get_db()
```

- [ ] **Step 2: Create style_issues.diff**

This diff should contain naming inconsistencies, magic numbers, and a long function:

```diff
--- a/src/processor.py
+++ b/src/processor.py
@@ -1,4 +1,5 @@
 import time
+import json


 def process_data(data):
@@ -8,3 +9,45 @@ def process_data(data):
         raise ValueError("data cannot be empty")
     return [item.strip() for item in data]

+
+def handleUserRequest(requestData, retryCount=3):
+    """Process a user request with retries."""
+    MaxItems = 100
+    result_list = []
+    error_list = []
+    for i in range(len(requestData)):
+        item = requestData[i]
+        if item.get("type") == 1:
+            processed = item.get("value", "").upper()
+            if len(processed) > 256:
+                processed = processed[:256]
+            result_list.append({"output": processed, "code": 1})
+        elif item.get("type") == 2:
+            processed = item.get("value", "").lower()
+            if len(processed) > 256:
+                processed = processed[:256]
+            result_list.append({"output": processed, "code": 2})
+        elif item.get("type") == 3:
+            processed = item.get("value", "").title()
+            if len(processed) > 256:
+                processed = processed[:256]
+            result_list.append({"output": processed, "code": 3})
+        else:
+            error_list.append({"index": i, "error": "unknown type"})
+        if len(result_list) >= MaxItems:
+            break
+    time.sleep(0.5)
+    final = {
+        "results": result_list,
+        "errors": error_list,
+        "total": len(result_list),
+        "error_count": len(error_list),
+        "ts": time.time(),
+    }
+    if len(error_list) > 0:
+        final["status"] = "partial"
+    else:
+        final["status"] = "ok"
+    return final
```

---

## Chunk 2: GPU Worker

### Task 3: Create gpu_worker.py

**Files:**
- Create: `02_ml_inference/02_code_review_agent/gpu_worker.py`

**Reference patterns:**
- `02_ml_inference/01_text_to_speech/gpu_worker.py` -- multi-function QB endpoint on same name, `if __name__` block, in-function imports
- Module-level `_state = {}` persists between invocations because the full module runs on the worker pod

- [ ] **Step 1: Write the complete gpu_worker.py**

```python
# Kimi-K2-Instruct inference via vLLM on 8xH100 GPUs.
# serves as the LLM backend for the code review agent.
# run with: flash run
# test directly: python gpu_worker.py
from runpod_flash import Endpoint, GpuType

MODEL_ID = "RedHatAI/Kimi-K2-Instruct-quantized.w4a16"
MAX_MODEL_LEN = 8192
TENSOR_PARALLEL_SIZE = 8
GPU_MEMORY_UTILIZATION = 0.95

# module-level state persists between invocations on the same worker pod.
# the entire module runs on the worker process, not just the function body.
_state = {}


def _get_engine():
    """Return the cached vLLM engine, initializing on first call."""
    if "engine" not in _state:
        from vllm import LLM

        _state["engine"] = LLM(
            model=MODEL_ID,
            tensor_parallel_size=TENSOR_PARALLEL_SIZE,
            gpu_memory_utilization=GPU_MEMORY_UTILIZATION,
            max_model_len=MAX_MODEL_LEN,
            distributed_executor_backend="ray",
        )
        _state["status"] = "ready"
    return _state["engine"]


@Endpoint(
    name="02_02_kimi_k2_gpu",
    gpu=GpuType.NVIDIA_H100_80GB_HBM3,
    gpu_count=8,
    workers=(0, 1),
    idle_timeout=600,
    dependencies=["vllm", "torch"],
)
async def generate(input_data: dict) -> dict:
    """
    Generate text using Kimi-K2-Instruct via vLLM.

    Input:
        messages: list[dict] - Chat messages with role and content
        max_tokens: int - Maximum tokens to generate (default: 4096)
        temperature: float - Sampling temperature (default: 0.1)
        top_p: float - Top-p sampling (default: 0.95)

    Returns:
        status: str - "success" or "error"
        text: str - Generated text
        usage: dict - Token usage stats
    """
    from vllm import SamplingParams

    messages = input_data.get("messages", [])
    if not messages:
        return {"status": "error", "error": "messages list is required and cannot be empty"}

    max_tokens = input_data.get("max_tokens", 4096)
    temperature = input_data.get("temperature", 0.1)
    top_p = input_data.get("top_p", 0.95)

    try:
        engine = _get_engine()
        tokenizer = engine.get_tokenizer()

        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

        sampling_params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )

        outputs = engine.generate([prompt], sampling_params)
        output = outputs[0]
        generated_text = output.outputs[0].text

        return {
            "status": "success",
            "text": generated_text,
            "usage": {
                "prompt_tokens": len(output.prompt_token_ids),
                "completion_tokens": len(output.outputs[0].token_ids),
            },
        }

    except Exception as e:
        error_msg = str(e)
        if "out of memory" in error_msg.lower() or "oom" in error_msg.lower():
            return {
                "status": "error",
                "error": f"Generation failed: OOM. Reduce diff size or max_tokens.",
                "detail": error_msg,
            }
        return {"status": "error", "error": error_msg}


@Endpoint(
    name="02_02_kimi_k2_gpu",
    gpu=GpuType.NVIDIA_H100_80GB_HBM3,
    gpu_count=8,
    dependencies=["vllm"],
)
async def health(input_data: dict) -> dict:
    """
    Check model loading status.

    Returns:
        status: str - "ready", "loading", or "error"
        model: str - Model identifier
        quantization: str - Quantization method
        gpu_count: int - Number of GPUs
    """
    try:
        _get_engine()
        return {
            "status": "ready",
            "model": MODEL_ID,
            "quantization": "W4A16",
            "gpu_count": TENSOR_PARALLEL_SIZE,
        }
    except Exception as e:
        if "engine" not in _state:
            return {
                "status": "loading",
                "model": MODEL_ID,
            }
        return {
            "status": "error",
            "model": MODEL_ID,
            "detail": str(e),
        }


if __name__ == "__main__":
    import asyncio

    print("Testing health check...")
    result = asyncio.run(health({}))
    print(f"Health: {result}\n")

    print("Testing generation...")
    test_payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2 + 2? Answer in one word."},
        ],
        "max_tokens": 32,
        "temperature": 0.0,
    }
    result = asyncio.run(generate(test_payload))
    if result["status"] == "success":
        print(f"Generated: {result['text']}")
        print(f"Usage: {result['usage']}")
    else:
        print(f"Error: {result}")
```

- [ ] **Step 2: Verify the file is syntactically valid**

Run: `cd /Users/deanquinanola/Github/python/flash-project/flash-examples/main && python -c "import ast; ast.parse(open('02_ml_inference/02_code_review_agent/gpu_worker.py').read()); print('OK')"`
Expected: `OK`

Note: Full functional testing requires 8xH100 GPUs. Syntax validation is the best we can do locally.

---

## Chunk 3: CPU Worker

### Task 4: Create cpu_worker.py

**Files:**
- Create: `02_ml_inference/02_code_review_agent/cpu_worker.py`

**Reference patterns:**
- `03_advanced_workers/05_load_balancer/cpu_lb.py` -- LB routes with `api = Endpoint(...)` + `@api.post(...)` + `@api.get(...)` + `if __name__` block
- `01_getting_started/03_mixed_workers/pipeline.py` -- cross-worker import inside route handler body: `from gpu_worker import generate`

- [ ] **Step 1: Write the complete cpu_worker.py**

```python
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
        return {"error_code": 503, "error": f"GPU worker unavailable (status: {status})"}

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

    # pass through errors
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
```

- [ ] **Step 2: Verify the file is syntactically valid**

Run: `cd /Users/deanquinanola/Github/python/flash-project/flash-examples/main && python -c "import ast; ast.parse(open('02_ml_inference/02_code_review_agent/cpu_worker.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Verify helper functions work in isolation**

Create a temporary test script and run it:

```bash
cd /Users/deanquinanola/Github/python/flash-project/flash-examples/main
cat > /tmp/test_cpu_helpers.py << 'PYEOF'
import sys
sys.path.insert(0, "02_ml_inference/02_code_review_agent")
from cpu_worker import _validate_diff, _strip_binary_hunks, _parse_llm_json, _compute_stats, _format_markdown

# test validation
assert _validate_diff("") == "Diff is empty"
assert _validate_diff("x" * 30000) is not None
assert _validate_diff("--- a/f\n+++ b/f\n@@ -1 +1 @@\n-old\n+new") is None

# test JSON parsing
assert _parse_llm_json('{"a": 1}') == {"a": 1}
assert _parse_llm_json('Here is the review:\n```json\n{"a": 1}\n```') == {"a": 1}
assert _parse_llm_json('Some text {"a": 1} more text') == {"a": 1}
assert _parse_llm_json("not json at all") is None

# test stats
assert _compute_stats([{"severity": "critical"}, {"severity": "warning"}, {"severity": "critical"}]) == {"critical": 2, "warning": 1, "suggestion": 0, "nitpick": 0}

# test markdown formatting
review = {"summary": "Test", "comments": [{"file": "a.py", "line": 1, "severity": "critical", "category": "bug", "issue": "Bad", "suggestion": "Fix"}], "positive_notes": ["Good job"]}
md = _format_markdown(review)
assert "# Code Review" in md
assert "Critical Issues" in md
assert "a.py:1" in md
assert "Good job" in md

print("All helper tests passed")
PYEOF
python /tmp/test_cpu_helpers.py
```
Expected: `All helper tests passed`

---

## Chunk 4: README and Final Integration

### Task 5: Create README.md

**Files:**
- Create: `02_ml_inference/02_code_review_agent/README.md`

**Reference:** `02_ml_inference/01_text_to_speech/README.md` for structure and tone.

- [ ] **Step 1: Write the README**

```markdown
# Code Review Agent with Kimi-K2

PR diff code reviewer powered by [Kimi-K2-Instruct](https://huggingface.co/moonshotai/Kimi-K2-Instruct) running on Runpod serverless GPUs via vLLM.

## Overview

This example demonstrates a two-worker architecture for self-hosted LLM inference:

- **GPU worker** (queue-based): Hosts Kimi-K2-Instruct via vLLM on 8xH100 GPUs with W4A16 quantization
- **CPU worker** (load-balanced): Validates diffs, constructs prompts, and formats review output as JSON or markdown

## What You'll Learn

- Self-hosting a 1T parameter MoE model with vLLM and quantization
- Cross-worker orchestration: CPU LB routes dispatching to GPU QB endpoints
- Health check patterns for large models with long cold starts
- Multiple output formats from the same pipeline (JSON + markdown)
- Multi-GPU provisioning with `gpu_count=8`

## Quick Start

### Prerequisites

- Python 3.10+
- Runpod API key ([get one here](https://docs.runpod.io/get-started/api-keys))

### GPU Requirements

| Config | Model | VRAM | Context Limit |
|--------|-------|------|---------------|
| **8xH100 80GB** (primary) | `RedHatAI/Kimi-K2-Instruct-quantized.w4a16` | ~500GB + KV cache | 8192 tokens |
| 8xH200 141GB | `moonshotai/Kimi-K2-Instruct` with FP8 | ~1TB | ~16K tokens |

Disk: ~600GB free for model weights and vLLM cache.

### Setup

```bash
cd 02_ml_inference/02_code_review_agent
uv sync
uv run flash login
```

### Run

```bash
uv run flash run
```

First run downloads the model (~500GB) and takes 30-60 minutes. Subsequent starts load from disk cache in several minutes. Server starts at http://localhost:8888

### Check Model Status

The GPU worker takes minutes to load. Poll the health endpoint before sending reviews:

```bash
curl http://localhost:8888/review/health
```

Response when loading:
```json
{"orchestrator": "ready", "gpu_worker": "loading", "status": "loading"}
```

Response when ready:
```json
{"orchestrator": "ready", "gpu_worker": "ready", "status": "ready"}
```

### Submit a Review (JSON)

```bash
curl -X POST http://localhost:8888/review/json \
  -H "Content-Type: application/json" \
  -d "{\"diff\": \"$(cat sample_diffs/security_bug.diff)\"}"
```

Response:
```json
{
  "summary": "Changes introduce SQL injection and XSS vulnerabilities.",
  "comments": [
    {
      "file": "src/auth.py",
      "line": 15,
      "severity": "critical",
      "category": "security",
      "issue": "SQL query built with string concatenation using user input",
      "suggestion": "Use parameterized queries: db.execute('SELECT * FROM users WHERE id = ?', (user_id,))"
    }
  ],
  "stats": {"critical": 2, "warning": 0, "suggestion": 0, "nitpick": 0}
}
```

### Submit a Review (Markdown)

```bash
curl -X POST http://localhost:8888/review/markdown \
  -H "Content-Type: application/json" \
  -d "{\"diff\": \"$(cat sample_diffs/style_issues.diff)\"}"
```

Returns a formatted markdown report.

## Architecture

```
User → POST /review/json
         ↓
CPU Worker (LB)          GPU Worker (QB)
  validate diff            vLLM engine
  build prompt    →await→  Kimi-K2-Instruct
  parse response  ←return← generated text
  format output
         ↓
User ← JSON or Markdown
```

## Limitations

- **Max diff size: 20KB** (~5-6K tokens). Larger diffs exceed the 8192 token context window. Split large PRs into per-file reviews.
- **Cold start: several minutes** after the worker scales to zero. Use `idle_timeout=600` (10 min) to reduce cold starts during active development.
- **First download: 30-60 minutes** for the ~500GB model weights.
- **No streaming**: vLLM generates the full response before returning.

## Cost Estimates

- Workers scale to 0 when idle (no charges)
- Pay only for GPU time during inference
- 8xH100 is a premium configuration -- consider reviewing in batches

## Swapping GPU Tiers

To use 8xH200 with FP8 quantization (more headroom, higher context), edit `gpu_worker.py`:

```python
# change GpuType and add quantization
@Endpoint(
    name="02_02_kimi_k2_gpu",
    gpu=GpuType.NVIDIA_H200,
    gpu_count=8,
    ...
)

# in _get_engine(), change model and add quantization param
_state["engine"] = LLM(
    model="moonshotai/Kimi-K2-Instruct",
    quantization="fp8",
    max_model_len=16384,
    ...
)
```

## References

- [Kimi-K2-Instruct Model Card](https://huggingface.co/moonshotai/Kimi-K2-Instruct)
- [RedHatAI W4A16 Quantization](https://huggingface.co/RedHatAI/Kimi-K2-Instruct-quantized.w4a16)
- [Running Kimi-K2 on Runpod](https://www.runpod.io/blog/guide-to-moonshotais-kimi-k2-on-runpod)
- [vLLM Kimi-K2 Recipe](https://docs.vllm.ai/projects/recipes/en/latest/moonshotai/Kimi-K2.html)
- [Flash Documentation](https://docs.runpod.io)
```

### Task 6: Update section README

**Files:**
- Modify: `02_ml_inference/README.md`

- [ ] **Step 1: Check if section README exists**

Run: `cat 02_ml_inference/README.md 2>/dev/null || echo "NO FILE"`

If it exists, add the new example entry. If not, create it following the pattern from other section READMEs.

- [ ] **Step 2: Add the code review agent entry**

Add an entry for `02_code_review_agent` to the section README, following the existing format (table row or list item matching whatever pattern is already there).

### Task 7: Update root README

**Files:**
- Modify: `README.md` (root)

- [ ] **Step 1: Add the new example to the examples table**

Find the `| **ML Inference** |` row in the root README table and add:

```
| | [02_code_review_agent](./02_ml_inference/02_code_review_agent/) | PR code review with self-hosted Kimi-K2 |
```

### Task 8: Run quality checks and commit

- [ ] **Step 1: Run format and lint**

Run: `cd /Users/deanquinanola/Github/python/flash-project/flash-examples/main && make format && make lint-fix`

Fix any issues that arise.

- [ ] **Step 2: Run full quality check**

Run: `make quality-check`
Expected: All checks pass.

- [ ] **Step 3: Commit all files**

Quality checks passed. Commit everything with `--no-verify` (no co-author lines):

```bash
git add 02_ml_inference/02_code_review_agent/ 02_ml_inference/README.md README.md
git commit --no-verify -m "feat(02_code_review_agent): add Kimi-K2 code review agent example

Two-worker Flash example: self-hosted Kimi-K2-Instruct via vLLM on
8xH100 (W4A16 quantization) with CPU orchestration for PR diff
code review. Outputs structured JSON and markdown reports."
```

### Task 9: Final verification

- [ ] **Step 1: Verify all files exist**

Run: `ls -la 02_ml_inference/02_code_review_agent/`
Expected: `gpu_worker.py`, `cpu_worker.py`, `prompts.py`, `README.md`, `sample_diffs/`

- [ ] **Step 2: Verify all Python files parse cleanly**

Run: `python -c "import ast; [ast.parse(open(f).read()) for f in ['02_ml_inference/02_code_review_agent/gpu_worker.py', '02_ml_inference/02_code_review_agent/cpu_worker.py', '02_ml_inference/02_code_review_agent/prompts.py']]; print('All files parse OK')"`
Expected: `All files parse OK`

- [ ] **Step 3: Verify helper function unit tests still pass**

Run: `python /tmp/test_cpu_helpers.py` (created in Task 4 Step 3)
Expected: `All helper tests passed`
