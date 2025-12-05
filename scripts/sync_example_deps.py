#!/usr/bin/env python3
"""
Sync example dependencies to root pyproject.toml.

Scans all example directories for pyproject.toml files, extracts dependencies,
and updates the root pyproject.toml with all required packages.

Filters out transitive dependencies already provided by tetra-rp:
- fastapi
- pydantic
- uvicorn
"""

import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import tomllib
from packaging import version

try:
    import tomli_w
except ImportError:
    tomli_w = None

ROOT_DIR = Path(__file__).parent.parent
ROOT_PYPROJECT = ROOT_DIR / "pyproject.toml"

EXAMPLES_DIRS = [
    "01_getting_started",
    "02_advanced",
    "03_production",
    "04_integrations",
    "05_scaling",
    "06_real_world",
]

TRANSITIVE_DEPS = {
    "fastapi",
    "pydantic",
    "uvicorn",
}

ESSENTIAL_ROOT_DEPS = {
    "tetra-rp",
    "tetra_rp",
}

# Fallback version number for specs without parseable versions
FALLBACK_VERSION = 999


def parse_pyproject(path: Path) -> dict[str, Any]:
    """Parse a pyproject.toml file."""
    with open(path, "rb") as f:
        return tomllib.load(f)


def extract_dependencies(pyproject_data: dict[str, Any]) -> list[str]:
    """Extract dependencies from pyproject.toml data."""
    return pyproject_data.get("project", {}).get("dependencies", [])


def normalize_dep_name(dep: str) -> str:
    """Extract package name from dependency string (e.g., 'numpy>=2.0.2' -> 'numpy')."""
    for op in [">=", "<=", "==", "!=", ">", "<", "~="]:
        if op in dep:
            return dep.split(op)[0].strip()
    return dep.strip()


def fully_normalize_name(name: str) -> str:
    """Normalize package name for consistent comparison.

    Converts to lowercase and replaces underscores with hyphens to match
    PyPI package naming conventions.
    """
    return normalize_dep_name(name).lower().replace("_", "-")


def collect_example_deps() -> dict[str, set[str]]:
    """Scan all example directories and collect dependencies."""
    deps_by_package: dict[str, set[str]] = defaultdict(set)

    for examples_dir in EXAMPLES_DIRS:
        examples_path = ROOT_DIR / examples_dir
        if not examples_path.exists():
            continue

        for example_dir in examples_path.iterdir():
            if not example_dir.is_dir():
                continue

            pyproject_path = example_dir / "pyproject.toml"
            if not pyproject_path.exists():
                continue

            try:
                pyproject_data = parse_pyproject(pyproject_path)
                deps = extract_dependencies(pyproject_data)

                for dep in deps:
                    normalized_name = fully_normalize_name(dep)

                    if normalized_name not in TRANSITIVE_DEPS:
                        deps_by_package[normalized_name].add(dep)

            except Exception as e:
                print(f"Warning: Failed to parse {pyproject_path}: {e}", file=sys.stderr)

    return deps_by_package


def detect_version_conflicts(deps_by_package: dict[str, set[str]]) -> list[tuple[str, set[str]]]:
    """Detect packages with multiple version specifications."""
    conflicts = []
    for package, dep_specs in deps_by_package.items():
        if len(dep_specs) > 1:
            conflicts.append((package, dep_specs))
    return conflicts


def select_most_permissive(dep_specs: set[str]) -> str:
    """Select the most permissive version constraint from a set of specs.

    For conflicts like ('package>=1.0', 'package>=2.0'), prefers the lower
    minimum version. Falls back to the spec with lowest operator count if
    min versions are equal (e.g., 'package>=1.0' over 'package>=1.0,<2.0').
    """

    def extract_min_version(spec: str) -> tuple[int, Any]:
        """Extract operator count and version from spec for sorting."""
        # Prioritize by: fewest constraints (more permissive), then lower min version
        constraint_count = sum(1 for op in [">=", "<=", "==", "!=", ">", "<", "~="] if op in spec)
        # Extract version number for proper semantic version comparison
        match = re.search(r"(\d+(?:\.\d+)*)", spec)
        if match:
            try:
                min_version = version.parse(match.group(1))
            except version.InvalidVersion:
                min_version = version.parse("999.0.0")  # Fallback for unparseable versions
        else:
            min_version = version.parse("999.0.0")  # Fallback for specs without version numbers
        return (constraint_count, min_version)

    return min(dep_specs, key=extract_min_version)


def merge_dependencies(deps_by_package: dict[str, set[str]], root_deps: list[str]) -> list[str]:
    """
    Merge dependencies, preferring the most permissive version constraint.
    Preserves essential root dependencies not found in examples.
    """
    merged = []
    added_names = set()
    example_dep_names = {
        fully_normalize_name(dep) for specs in deps_by_package.values() for dep in specs
    }

    for dep in root_deps:
        dep_name = fully_normalize_name(dep)
        if dep_name not in added_names and (
            dep_name in ESSENTIAL_ROOT_DEPS
            or (dep_name not in example_dep_names and dep_name not in TRANSITIVE_DEPS)
        ):
            merged.append(dep)
            added_names.add(dep_name)

    for package, dep_specs in sorted(deps_by_package.items()):
        if package not in added_names:
            if len(dep_specs) == 1:
                merged.append(next(iter(dep_specs)))
            else:
                merged.append(select_most_permissive(dep_specs))
            added_names.add(package)

    return sorted(merged, key=lambda d: fully_normalize_name(d))


def read_root_pyproject() -> tuple[dict[str, Any], str]:
    """Read root pyproject.toml and return parsed data and original content."""
    with open(ROOT_PYPROJECT) as f:
        original = f.read()

    with open(ROOT_PYPROJECT, "rb") as f:
        data = tomllib.load(f)

    return data, original


def update_root_pyproject(merged_deps: list[str], dry_run: bool = False) -> bool:
    """Update root pyproject.toml with merged dependencies.

    Uses tomli_w library if available to properly write TOML format.
    Falls back to line-by-line string manipulation as a fallback.
    """
    root_data, original_content = read_root_pyproject()
    current_deps = root_data.get("project", {}).get("dependencies", [])

    if sorted(current_deps) == sorted(merged_deps):
        print("Root dependencies are already up to date.")
        return False

    if dry_run:
        print("\n=== Dry Run Mode ===")
        print("\nCurrent root dependencies:")
        for dep in sorted(current_deps):
            print(f"  - {dep}")
        print("\nProposed merged dependencies:")
        for dep in merged_deps:
            print(f"  - {dep}")
        return False

    if tomli_w:
        # Use tomli_w to write proper TOML format
        root_data["project"]["dependencies"] = merged_deps
        with open(ROOT_PYPROJECT, "wb") as f:
            tomli_w.dump(root_data, f)
    else:
        # Fallback to string manipulation for environments without tomli_w
        deps_section = '[\n    "' + '",\n    "'.join(merged_deps) + '",\n]'

        lines = original_content.split("\n")
        new_lines = []
        in_dependencies = False
        bracket_depth = 0

        for line in lines:
            if line.strip().startswith("dependencies = ["):
                in_dependencies = True
                new_lines.append(f"dependencies = {deps_section}")
                if line.strip().endswith("]"):
                    in_dependencies = False
                else:
                    bracket_depth = 1
                continue

            if in_dependencies:
                # Count unquoted brackets to handle extras like package[extra].
                # Known failure cases include:
                #   - Multiline strings in dependencies (triple quotes)
                #   - Nested arrays or tables within dependencies
                #   - Comments inside the dependencies array
                #   - Inline tables or complex value types
                if '"""' in line or "'''" in line or (line.count("{") > 0) or (line.count("}") > 0):
                    print(
                        "ERROR: Detected complex TOML structure in dependencies array. "
                        "Please ensure 'tomli_w' is installed for safe operation.",
                        file=sys.stderr,
                    )
                    return False

                in_quotes = False
                for i, char in enumerate(line):
                    if char == '"' and (i == 0 or line[i - 1] != "\\"):
                        in_quotes = not in_quotes
                    elif not in_quotes:
                        if char == "[":
                            bracket_depth += 1
                        elif char == "]":
                            bracket_depth -= 1

                if bracket_depth == 0:
                    in_dependencies = False
                continue

            new_lines.append(line)

        with open(ROOT_PYPROJECT, "w") as f:
            f.write("\n".join(new_lines))

    print(f"Updated {ROOT_PYPROJECT}")
    return True


def main() -> int:
    """Main entry point."""
    dry_run = "--dry-run" in sys.argv or "--check" in sys.argv
    check_mode = "--check" in sys.argv

    print(f"Scanning example directories: {', '.join(EXAMPLES_DIRS)}")

    deps_by_package = collect_example_deps()

    if not deps_by_package:
        print("No example dependencies found.")
        return 0

    print(f"\nFound {len(deps_by_package)} unique packages across examples")

    conflicts = detect_version_conflicts(deps_by_package)
    if conflicts:
        print("\nVersion conflicts detected:")
        for package, dep_specs in conflicts:
            print(f"  {package}:")
            for spec in sorted(dep_specs):
                print(f"    - {spec}")
        print("\nUsing most permissive constraint for conflicts")

    root_data, _ = read_root_pyproject()
    current_root_deps = root_data.get("project", {}).get("dependencies", [])

    merged_deps = merge_dependencies(deps_by_package, current_root_deps)

    changed = update_root_pyproject(merged_deps, dry_run=dry_run or check_mode)

    if check_mode and changed:
        print("\nERROR: Root pyproject.toml is out of sync with example dependencies.")
        print("Run 'make sync-example-deps' to update.")
        return 1

    if not dry_run and changed:
        print("\nNext steps:")
        print("  1. Review the changes to pyproject.toml")
        print("  2. Run 'uv sync --all-groups' to install new dependencies")
        print("  3. Run 'make requirements.txt' to regenerate the lockfile")

    return 0


if __name__ == "__main__":
    sys.exit(main())
