#!/usr/bin/env python3
"""Consolidate example dependencies into root pyproject.toml.

Simple script that collects all dependencies from example directories
and adds them to the root pyproject.toml. No conflict resolution -
if pip/uv can't resolve versions, fix manually.

Usage:
    python scripts/sync_example_deps.py          # Consolidate
    python scripts/sync_example_deps.py --check  # Verify (CI mode)

Make commands:
    make consolidate-deps  # Run consolidation
    make check-deps        # Verify in sync
"""

import sys
from pathlib import Path

import tomli_w

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]

ROOT_DIR = Path(__file__).parent.parent
ROOT_PYPROJECT = ROOT_DIR / "pyproject.toml"
EXAMPLES_DIRS = [
    "01_getting_started",
    "02_ml_inference",
    "03_advanced_workers",
    "04_scaling_performance",
    "05_data_workflows",
    "06_real_world",
]


def collect_all_deps() -> set[str]:
    """Collect all dependencies from example pyproject.toml files."""
    all_deps = set()
    for examples_dir in EXAMPLES_DIRS:
        examples_path = ROOT_DIR / examples_dir
        if not examples_path.exists():
            continue
        for example_dir in examples_path.iterdir():
            if not example_dir.is_dir():
                continue
            pyproject_path = example_dir / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                    deps = data.get("project", {}).get("dependencies", [])
                    all_deps.update(deps)
    return all_deps


def main() -> None:
    """Consolidate dependencies or check if consolidation is needed."""
    check_mode = "--check" in sys.argv

    with open(ROOT_PYPROJECT, "rb") as f:
        root_data = tomllib.load(f)

    example_deps = collect_all_deps()
    current = set(root_data["project"].get("dependencies", []))

    if check_mode:
        missing = example_deps - current
        if missing:
            print("ERROR: Dependencies need consolidation:")
            for dep in sorted(missing):
                print(f"  Missing: {dep}")
            print("\nRun: make consolidate-deps")
            sys.exit(1)
        print("✓ All example dependencies are in root")
        return

    # Consolidate mode
    root_data["project"]["dependencies"] = sorted(current | example_deps)
    with open(ROOT_PYPROJECT, "wb") as f:
        tomli_w.dump(root_data, f)

    new_count = len(example_deps - current)
    print(f"✓ Consolidated {new_count} new dependencies")
    print("Run 'uv sync' to install")


if __name__ == "__main__":
    main()
