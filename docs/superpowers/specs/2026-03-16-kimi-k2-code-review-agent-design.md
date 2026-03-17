# Kimi-K2 Code Review Agent -- Design Spec

## Overview

A two-worker Flash example that deploys Kimi-K2-Instruct via vLLM on 8xH100 GPUs and exposes a PR diff code review service through CPU-based LB endpoints. Demonstrates self-hosted large model inference combined with CPU orchestration for a realistic developer tool.

**Location:** `02_ml_inference/02_code_review_agent/`

## Architecture

```
┌─────────────────────────────────────────────────┐
│  User                                           │
│  curl /review/json or /review/markdown          │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│  CPU Worker (LB) -- cpu_worker.py               │
│  Endpoint: 02_02_kimi_k2_review                 │
│  cpu="cpu3c-1-2", workers=(1, 3)                │
│                                                 │
│  Routes:                                        │
│    POST /review/json      → structured JSON     │
│    POST /review/markdown  → formatted markdown  │
│    GET  /review/health    → aggregate status     │
│                                                 │
│  Responsibilities:                              │
│    - Validate diff input                        │
│    - Parse diff for file names and line numbers  │
│    - Construct review prompt                    │
│    - Poll GPU health before dispatching         │
│    - Parse LLM output into structured format    │
│    - Format markdown report                     │
│                                                 │
│  Note: LB route handlers run in-process. QB     │
│  imports (gpu_worker) go inside route handlers   │
│  per existing cross-worker patterns. prompts.py  │
│  imported at module level (string constants).   │
└──────────────┬──────────────────────────────────┘
               │ await generate(prompt)
               │ (imported from gpu_worker.py)
               ▼
┌─────────────────────────────────────────────────┐
│  GPU Worker (QB) -- gpu_worker.py               │
│  Endpoint: 02_02_kimi_k2_gpu                    │
│  gpu=GpuType.NVIDIA_H100_80GB_HBM3, gpu_count=8│
│  workers=(0, 1), idle_timeout=600               │
│                                                 │
│  QB Functions (each decorated separately):      │
│    generate(prompt) → raw LLM text              │
│    health()         → loading/ready/error       │
│                                                 │
│  Internals:                                     │
│    - Pre-quantized W4A16 model (~500GB)         │
│    - RedHatAI/Kimi-K2-Instruct-quantized.w4a16  │
│    - vLLM engine, tensor_parallel_size=8        │
│    - max_model_len=8192 (VRAM-constrained)      │
│    - Eager model loading at startup             │
└─────────────────────────────────────────────────┘
```

## GPU Worker -- gpu_worker.py

### Resource Configuration

Both QB functions share the same endpoint name and resource config, each with its own `@Endpoint` decorator (same pattern as the TTS example):

```python
@Endpoint(
    name="02_02_kimi_k2_gpu",
    gpu=GpuType.NVIDIA_H100_80GB_HBM3,
    gpu_count=8,
    workers=(0, 1),
    idle_timeout=600,
    dependencies=["vllm", "torch"],
)
async def generate(input_data: dict) -> dict:
    ...

@Endpoint(
    name="02_02_kimi_k2_gpu",
    gpu=GpuType.NVIDIA_H100_80GB_HBM3,
    gpu_count=8,
    dependencies=["vllm"],
)
async def health(input_data: dict) -> dict:
    ...
```

- 8xH100 80GB = 640GB VRAM total
- Pre-quantized W4A16 model: ~500GB for weights, leaving ~140GB for KV cache and vLLM overhead
- `max_model_len=8192` -- realistic limit given VRAM budget. Input (system prompt + diff) + output must fit within this window.
- `workers=(0, 1)` -- single instance, scales to zero when idle
- `idle_timeout=600` -- 10 minutes to avoid frequent cold starts

### Endpoints

**`generate`** -- Takes chat messages (system + user), returns raw text.

Input:
```json
{
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "max_tokens": 4096,
  "temperature": 0.1,
  "top_p": 0.95
}
```

Output:
```json
{
  "status": "success",
  "text": "...",
  "usage": {"prompt_tokens": 1234, "completion_tokens": 567}
}
```

**`health`** -- Returns model status.

Output:
```json
{
  "status": "ready",
  "model": "RedHatAI/Kimi-K2-Instruct-quantized.w4a16",
  "quantization": "W4A16",
  "gpu_count": 8
}
```

Or during loading:
```json
{
  "status": "loading",
  "model": "RedHatAI/Kimi-K2-Instruct-quantized.w4a16"
}
```

### Model Initialization

vLLM engine initialized eagerly inside the first function call, then cached in a module-level dict. This works because the entire module runs on the worker process -- module-level state persists between invocations on the same pod.

```python
_state = {}

@Endpoint(
    name="02_02_kimi_k2_gpu",
    gpu=GpuType.NVIDIA_H100_80GB_HBM3,
    gpu_count=8,
    workers=(0, 1),
    idle_timeout=600,
    dependencies=["vllm", "torch"],
)
async def generate(input_data: dict) -> dict:
    from vllm import LLM, SamplingParams

    if "engine" not in _state:
        _state["engine"] = LLM(
            model="RedHatAI/Kimi-K2-Instruct-quantized.w4a16",
            tensor_parallel_size=8,
            gpu_memory_utilization=0.95,
            max_model_len=8192,
            distributed_executor_backend="ray",
        )
    engine = _state["engine"]
    # ... generate
```

Note: No `quantization` parameter needed -- the model is pre-quantized. vLLM detects the format from the model config.

## CPU Worker -- cpu_worker.py

### Resource Configuration

```python
from prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

api = Endpoint(
    name="02_02_kimi_k2_review",
    cpu="cpu3c-1-2",
    workers=(1, 3),
)

@api.post("/review/json")
async def review_json(data: dict) -> dict:
    from gpu_worker import generate, health as gpu_health
    # ... route handler body
```

Cross-worker imports (`generate`, `health`) go inside route handler bodies, matching the established pattern from `03_mixed_workers/pipeline.py`. The `prompts.py` import stays at module level since it's just string constants with no side effects.

### Routes

#### `POST /review/json`

**Input:**
```json
{
  "diff": "unified diff string"
}
```

**Output:**
```json
{
  "summary": "Brief overall assessment of the changes",
  "comments": [
    {
      "file": "src/auth.py",
      "line": 42,
      "severity": "critical",
      "category": "security",
      "issue": "SQL query constructed with string concatenation using user input",
      "suggestion": "Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))"
    }
  ],
  "stats": {
    "critical": 1,
    "warning": 0,
    "suggestion": 2,
    "nitpick": 1
  }
}
```

#### `POST /review/markdown`

Same input. Output is a markdown string:

```markdown
# Code Review

## Summary
Brief overall assessment.

## Critical Issues
### src/auth.py:42 -- SQL Injection
SQL query constructed with string concatenation...
**Suggestion:** Use parameterized queries...

## Warnings
(none)

## Suggestions
...

## Positive Notes
...
```

#### `GET /review/health`

Polls its own status and the GPU worker's `health` endpoint with a 5-second timeout. Returns aggregate:

```json
{
  "orchestrator": "ready",
  "gpu_worker": "ready",
  "status": "ready"
}
```

If GPU worker is loading: `"status": "loading"`. If GPU worker is unreachable or times out (5s): `"status": "degraded"`. Note: if the GPU worker has scaled to zero, the health call will time out and report "degraded" rather than triggering a cold start.

### Processing Pipeline

1. **Validate** -- Reject empty diffs, diffs > 20KB (~5-6K tokens, leaves room for system prompt ~500 tokens + 2-4K output tokens within `max_model_len=8192`), return 400
2. **Parse** -- Extract file names and changed line numbers from unified diff format. Strip binary file hunks.
3. **Build prompt** -- Insert parsed diff into prompt template from `prompts.py`. System prompt instructs JSON output schema.
4. **Health check** -- Call GPU worker `health` (5s timeout). If not `ready`, return 503 with retry guidance.
5. **Generate** -- Call GPU worker `generate` with constructed messages.
6. **Parse response** -- Extract JSON from LLM output. If invalid JSON, retry once with stricter prompt. If still invalid, return 502 with `raw_response`.
7. **Format** -- For `/review/json`, return parsed JSON. For `/review/markdown`, transform JSON into markdown report.

## Prompt Design -- prompts.py

Separate file with string constants. Imported by `cpu_worker.py` at module level (plain constants with no side effects).

**System prompt** instructs Kimi-K2 to:
- Act as a senior code reviewer
- Analyze the unified diff provided
- Output a JSON object matching the review schema (file, line, severity, category, issue, suggestion)
- Use four severity levels: critical (bugs, security), warning (logic issues, error handling), suggestion (improvements, readability), nitpick (style, naming)
- Use five categories: security, bug, performance, style, logic
- Include a summary field with 1-2 sentence assessment
- Include positive notes when code is well-written

**User prompt template** wraps the diff:
```
Review the following unified diff:

```diff
{diff}
```

Respond with ONLY a JSON object matching the specified schema.
```

## Error Handling

| Scenario | Response | Details |
|----------|----------|---------|
| Empty diff | 400 | `"error": "Diff is empty"` |
| Diff > 20KB | 400 | `"error": "Diff too large (max 20KB). Split into smaller reviews."` |
| GPU worker loading | 503 | `"error": "Model loading", "retry_after": 60` |
| GPU worker unreachable | 503 | `"error": "GPU worker unavailable"` |
| vLLM OOM | 502 | `"error": "Generation failed: OOM", "input_tokens": N` |
| LLM invalid JSON | 502 (after 1 retry) | `"error": "Failed to parse review", "raw_response": "..."` |
| vLLM model load failure | health returns error | `"status": "error", "detail": "..."` |

No silent failures. Every error includes enough context to diagnose.

## File Structure

```
02_ml_inference/02_code_review_agent/
├── gpu_worker.py          # vLLM Kimi-K2 inference (QB endpoint, two @Endpoint functions)
├── cpu_worker.py          # Code review orchestrator (LB routes)
├── prompts.py             # System/user prompt templates (plain string constants)
├── sample_diffs/          # Curated test diffs
│   ├── security_bug.diff  # SQL injection, unescaped input
│   └── style_issues.diff  # Naming, long functions, magic numbers
└── README.md              # Setup, requirements, usage, curl examples
```

## Testing

No pytest infrastructure -- consistent with all other flash-examples.

**Manual testing via `__main__` blocks:**
- `gpu_worker.py` -- simple prompt generation test (requires GPU)
- `cpu_worker.py` -- loads sample diff, calls full pipeline, prints both output formats

**README includes curl commands for all three routes.**

**Sample diffs are curated:**
- `security_bug.diff` -- should produce at least one "critical" finding (SQL injection or XSS)
- `style_issues.diff` -- should produce "suggestion" and "nitpick" findings (naming, magic numbers, long functions)

## GPU Requirements and Alternatives

**Primary target:** 8xH100 80GB with pre-quantized W4A16 model

| Config | Model | VRAM Needed | Context Limit | Notes |
|--------|-------|-------------|---------------|-------|
| 8xH100 80GB (W4A16) | `RedHatAI/Kimi-K2-Instruct-quantized.w4a16` | ~500GB weights + KV cache | 8192 tokens | Primary target. Tight but workable. |
| 8xH200 141GB (FP8) | `moonshotai/Kimi-K2-Instruct` | ~1TB at FP8 | ~16K tokens | More headroom. Use `quantization="fp8"`. |
| 8xH200 141GB (FP16) | `moonshotai/Kimi-K2-Instruct` | ~2TB | N/A | Does not fit. Would need a cluster. |

**Cold start:** Model download is ~500GB (W4A16) and takes 30-60 minutes on first run. Subsequent starts load from disk cache in several minutes. The health check pattern lets clients poll readiness.

**Disk requirements:** ~600GB free disk space for model weights and vLLM cache.

## Dependencies

**GPU worker:** `vllm`, `torch` (declared in `@Endpoint(dependencies=[...])`)

**CPU worker:** None beyond `runpod_flash` (stdlib only for diff parsing)

**prompts.py:** No dependencies (plain string constants)
