"""Validate the Agentic3 product-realization workstream registry."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = REPO_ROOT / "docs" / "agentic3" / "WORKSTREAM-REGISTRY.json"
_REQUIRED_WORKSTREAM_FIELDS = {
    "id",
    "title",
    "owner_role",
    "state",
    "dependencies",
    "owned_paths",
    "contract_surfaces",
    "acceptance_evidence",
    "collision_policy",
}
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def validate_registry(data: dict[str, Any]) -> list[str]:
    """Return deterministic validation errors; an empty list means valid."""
    errors: list[str] = []
    baseline = data.get("baseline")
    if not isinstance(baseline, dict):
        errors.append("baseline must be an object")
    else:
        for field in ("repository", "ref", "commit", "issue", "governing_inputs"):
            if not baseline.get(field):
                errors.append(f"baseline.{field} is required")
        if baseline.get("commit") and not _SHA_RE.fullmatch(str(baseline["commit"])):
            errors.append("baseline.commit must be a 40-character lowercase SHA")
        if not isinstance(baseline.get("governing_inputs"), list):
            errors.append("baseline.governing_inputs must be a list")

    allowed_states = data.get("allowed_states")
    if not isinstance(allowed_states, list) or not allowed_states:
        errors.append("allowed_states must be a non-empty list")
        allowed: set[str] = set()
    else:
        allowed = set(allowed_states)
        if len(allowed) != len(allowed_states):
            errors.append("allowed_states contains duplicates")

    workstreams = data.get("workstreams")
    if not isinstance(workstreams, list) or not workstreams:
        return [*errors, "workstreams must be a non-empty list"]

    ids: list[str] = []
    paths: dict[str, str] = {}
    dependencies: dict[str, list[str]] = {}
    for index, workstream in enumerate(workstreams):
        label = f"workstreams[{index}]"
        if not isinstance(workstream, dict):
            errors.append(f"{label} must be an object")
            continue
        missing = sorted(_REQUIRED_WORKSTREAM_FIELDS - workstream.keys())
        if missing:
            errors.append(f"{label} missing fields: {', '.join(missing)}")
        workstream_id = workstream.get("id")
        if not isinstance(workstream_id, str) or not workstream_id:
            errors.append(f"{label}.id must be a non-empty string")
            continue
        ids.append(workstream_id)
        state = workstream.get("state")
        if state not in allowed:
            errors.append(f"{workstream_id}.state is not allowed: {state}")
        deps = workstream.get("dependencies")
        if not isinstance(deps, list):
            errors.append(f"{workstream_id}.dependencies must be a list")
            deps = []
        dependencies[workstream_id] = deps
        for field in ("owned_paths", "contract_surfaces", "acceptance_evidence"):
            value = workstream.get(field)
            if not isinstance(value, list) or not value:
                errors.append(f"{workstream_id}.{field} must be a non-empty list")
        for path in workstream.get("owned_paths", []):
            if path in paths:
                errors.append(
                    f"owned path {path!r} is claimed by {paths[path]} and {workstream_id}"
                )
            else:
                paths[path] = workstream_id

    known_ids = set(ids)
    if len(known_ids) != len(ids):
        errors.append("workstream IDs must be unique")
    for workstream_id, deps in dependencies.items():
        for dependency in deps:
            if dependency == workstream_id:
                errors.append(f"{workstream_id} depends on itself")
            elif dependency not in known_ids:
                errors.append(f"{workstream_id} has unknown dependency {dependency}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(workstream_id: str) -> None:
        if workstream_id in visiting:
            errors.append(f"dependency cycle includes {workstream_id}")
            return
        if workstream_id in visited:
            return
        visiting.add(workstream_id)
        for dependency in dependencies.get(workstream_id, []):
            if dependency in known_ids:
                visit(dependency)
        visiting.remove(workstream_id)
        visited.add(workstream_id)

    for workstream_id in ids:
        visit(workstream_id)
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", nargs="?", type=Path, default=DEFAULT_REGISTRY)
    args = parser.parse_args()
    try:
        data = json.loads(args.registry.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"PRODUCT CANON INVALID: {exc}")
        return 1
    errors = validate_registry(data)
    if errors:
        print(f"PRODUCT CANON INVALID: {len(errors)} error(s)")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"product canon valid: {len(data['workstreams'])} workstreams")
    return 0


if __name__ == "__main__":
    sys.exit(main())
