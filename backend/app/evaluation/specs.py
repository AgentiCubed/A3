"""Canonical rubric validation, merging, and provenance hashes."""

from __future__ import annotations

import hashlib
import json

from pydantic import ValidationError

from app.schemas.project import AcceptanceCriterionIn


class RubricSpecError(ValueError):
    """A rubric cannot be executed safely or conflicts with governed criteria."""


def normalize_rubric_specs(raw_specs: object) -> list[dict]:
    """Validate rubric JSON and return one stable JSON-compatible representation."""
    if raw_specs is None:
        return []
    if not isinstance(raw_specs, list):
        raise RubricSpecError("rubric specifications must be a list")
    normalized: list[dict] = []
    for index, raw in enumerate(raw_specs):
        try:
            criterion = AcceptanceCriterionIn.model_validate(raw)
        except ValidationError as exc:
            error = exc.errors(include_url=False, include_input=False)[0]
            location = ".".join(str(part) for part in error["loc"])
            suffix = f".{location}" if location else ""
            raise RubricSpecError(
                f"invalid rubric specification at {index}{suffix}: {error['msg']}"
            ) from exc
        normalized.append(criterion.model_dump(mode="json", exclude_none=True))
    return normalized


def canonical_rubric_json(specs: list[dict]) -> str:
    return json.dumps(specs, sort_keys=True, separators=(",", ":"))


def rubric_sha256(specs: list[dict]) -> str:
    return hashlib.sha256(canonical_rubric_json(specs).encode()).hexdigest()


def merge_rubric_specs(persisted: object, requested: object) -> tuple[list[dict], list[str]]:
    """Merge an additive request overlay without allowing governed criteria replacement."""
    persisted_specs = normalize_rubric_specs(persisted)
    requested_specs = normalize_rubric_specs(requested)
    merged: list[dict] = []
    canonical_seen: set[str] = set()
    keyed: dict[str, str] = {}

    def _add(spec: dict) -> None:
        canonical = canonical_rubric_json([spec])
        if canonical in canonical_seen:
            return
        key = spec.get("key")
        if key and key in keyed and keyed[key] != canonical:
            raise RubricSpecError(f"rubric criterion key '{key}' conflicts with governed criteria")
        canonical_seen.add(canonical)
        if key:
            keyed[key] = canonical
        merged.append(spec)

    for spec in persisted_specs:
        _add(spec)
    for spec in requested_specs:
        _add(spec)

    sources: list[str] = []
    if persisted_specs:
        sources.append("persisted")
    if requested_specs:
        sources.append("request")
    return merged, sources
