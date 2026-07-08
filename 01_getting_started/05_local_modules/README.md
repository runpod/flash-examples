# Local (non-pip) modules

Factor a Flash endpoint across local Python files that are **not** pip-installable —
a sibling module and a package that live next to the endpoint. This is the
capability added by **SLS-360**.

```
05_local_modules/
├── cpu_worker.py        # the @Endpoint — imports the local modules below
├── text_utils.py        # local sibling module
└── greetings/           # local package
    ├── __init__.py      # re-exports render() from .messages (transitive import)
    └── messages.py      # greeting templates
```

`cpu_worker.py` imports `text_utils` and `greetings` **inside the function body**.
That is required on the live path (`flash dev` / `.run()`), where only the
function source plus its local-module closure are shipped to the worker — so
imports must resolve at call time. The same code works unchanged for
`flash deploy`, where the whole project tree is bundled.

## Run it

```bash
# Live dev server (see the live-path note below re: worker image)
flash dev
# then: curl -s localhost:8888/cpu_worker/runsync -d '{"input": {"name": "Ada", "lang": "es"}}'

# Or deploy to Runpod
flash deploy
```

Expected result shape:

```json
{"status": "success", "greeting": "HOLA, ADA!", "timestamp": "..."}
```

`greeting` is produced by the local modules: `greetings.render()` builds
`"Hola, Ada"`, then `text_utils.shout()` upper-cases and adds `!`.

## Verifying SLS-360

Three tiers, in increasing cost. Tier 1 needs no infra; Tier 2 uses a real
Runpod endpoint; Tier 3 exercises the live inline-shipping path.

### Tier 1 — build path (local, no infra)

The build resolves each endpoint's local-import closure, force-includes those
files even when the ignore filter would drop them, and fails loudly if an
endpoint's local import can't be resolved.

```bash
flash build

# (a) sibling + package (init AND submodule) are all bundled:
tar tzf .flash/artifact.tar.gz | grep -E 'text_utils|greetings|cpu_worker'
#   ./cpu_worker.py
#   ./greetings/__init__.py
#   ./greetings/messages.py
#   ./text_utils.py
```

Force-include of an **ignore-dropped** module (this is the specific SLS-360 fix —
a module the ignore rules would silently drop is still bundled because an
endpoint imports it):

```bash
# a helper whose name matches the built-in test_*.py ignore rule
printf 'SAMPLE_NAMES = ["Ada", "Alan", "Grace"]\n' > test_samples.py
# make the endpoint import it (add `import test_samples` inside greet())
flash build
tar tzf .flash/artifact.tar.gz | grep test_samples.py   # -> ./test_samples.py  (rescued)
rm test_samples.py   # revert the endpoint edit too
```

Loud failure on an unresolved endpoint import (clean error, exit 1, no traceback):

```bash
# temporarily add `from . import missing_sibling` to cpu_worker.py, then:
flash build ; echo "exit=$?"
#   ✗ .../cpu_worker.py: relative import (level=1, module='missing_sibling')
#     could not be resolved to a local file under ...
#   exit=1
```

### Tier 2 — deploy path (real endpoint) — verified

The deploy path works with **any** worker image: the local modules are physically
bundled into the artifact and unpacked onto the worker filesystem, so the
endpoint imports them at runtime. This validates SLS-360's build/deploy half
end-to-end on real infra today.

```bash
flash deploy
curl -X POST https://api.runpod.ai/v2/<endpoint-id>/runsync \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {"name": "Ada", "lang": "es"}}'
# -> {"output": {"greeting": "HOLA, ADA!", "status": "success", ...}, "status": "COMPLETED"}
flash undeploy <name> --force   # tear down when done
```

Verified on a real CPU endpoint: the worker imported the local sibling
(`text_utils`) and package (`greetings`) and returned `"HOLA, ADA!"`.

> **Payload shape:** the generated queue handler calls the endpoint as
> `greet(**job_input)`, so the function takes typed params (`name`, `lang`) and
> the request nests them under `input`. A single `def greet(input_data: dict)`
> would instead require `{"input": {"input_data": {...}}}`.
>
> **Worker turnover:** a warm worker keeps serving the previous build for a short
> while after `flash deploy`. If a call returns stale behavior, retry until a
> fresh worker (new `workerId`) picks up the new build.

### Tier 3 — live path (`flash dev` / `.run()`)

This is the genuinely new capability: local modules are shipped **inline** with
the function and materialized on the worker's `sys.path` before the function
runs. It requires the worker runtime that materializes `FunctionRequest.modules`
(flash-worker PR runpod-workers/flash#100).

- **Against stock Runpod workers** (current published image): the inline modules
  are ignored by the worker, so `import text_utils` fails on the worker. This is
  expected until #100 is released.
- **To test now:** build the flash-worker image locally with #100
  (`make build` in the worker repo) and exercise it via the worker's
  `make smoketest` with a request carrying `modules`, or via
  `flash deploy --preview` (docker-compose) pointed at the local image.
- **After #100 ships:** `flash dev` + a POST to `/cpu_worker/runsync` works
  directly, and the greeting is computed by the shipped local modules on the
  worker.

## Why in-function imports

On the live path only the function's own source is extracted and shipped. Module
top-level imports/constants are not sent (that is the older AE-2308 behavior).
Keeping `import text_utils` / `from greetings import render` inside `greet()`
ensures the resolver discovers them and the worker can import them at call time —
and it stays correct for `flash deploy` too.
