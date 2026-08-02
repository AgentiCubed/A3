"""Hermetic tests for the product-realization canon validator.

The validator (scripts/check_product_canon.py) gates the workstream registry
of the Agentic3 product-realization canon (DR-0006, issue #106). These tests
pin down its acceptance and rejection behavior with in-memory registries —
plus the committed registry itself — so the canon contract is proven without
network access.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "check_product_canon.py"
_spec = importlib.util.spec_from_file_location("check_product_canon", _SCRIPT)
check_product_canon = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_product_canon)

_BASELINE_COMMIT = "7061cd6d130d7863bf66bc12173c7896373da5b5"


def _registry() -> dict:
    """A minimal valid registry: two workstreams, one dependency edge."""
    return {
        "schema_version": "1.0",
        "canon_version": "0.1.0-test",
        "baseline": {
            "repository": "AgentiCubed/A3",
            "ref": "main",
            "commit": _BASELINE_COMMIT,
            "issue": 106,
            "governing_inputs": ["docs/agentic3/ARCHITECTURE-v2.md"],
        },
        "allowed_states": ["proposed", "active"],
        "workstreams": [
            {
                "id": "GOV-01",
                "title": "Canon and enforcement",
                "owner_role": "program steward",
                "state": "active",
                "dependencies": [],
                "owned_paths": ["docs/agentic3/PRODUCT-REALIZATION-PROGRAM.md"],
                "contract_surfaces": ["canon precedence"],
                "acceptance_evidence": ["issue:106"],
                "collision_policy": "Reconcile on main before changing canon semantics.",
            },
            {
                "id": "RT-01",
                "title": "Event-ledger vertical slice",
                "owner_role": "runtime lead",
                "state": "proposed",
                "dependencies": ["GOV-01"],
                "owned_paths": ["backend/app/agentic3/**"],
                "contract_surfaces": ["RuntimeEventV1"],
                "acceptance_evidence": ["upgrade and downgrade"],
                "collision_policy": "The versioned event contract lands first.",
            },
        ],
    }


def test_valid_registry_has_no_errors():
    assert check_product_canon.validate_registry(_registry()) == []


def test_committed_registry_is_valid_and_pinned_to_baseline():
    """The canonical registry passes, pins the gate 2 baseline, and has no dangling canon files."""
    data = json.loads(check_product_canon.DEFAULT_REGISTRY.read_text())
    assert check_product_canon.validate_registry(data) == []
    assert data["baseline"]["commit"] == _BASELINE_COMMIT
    for governing_input in data["baseline"]["governing_inputs"]:
        assert (_REPO_ROOT / governing_input).is_file(), governing_input
    # GOV-01 owns only exact files (the canon's own artifacts); each must exist.
    gov = next(w for w in data["workstreams"] if w["id"] == "GOV-01")
    for owned_path in gov["owned_paths"]:
        assert (_REPO_ROOT / owned_path).is_file(), owned_path


def test_duplicate_workstream_ids_rejected():
    registry = _registry()
    registry["workstreams"][1]["id"] = "GOV-01"
    registry["workstreams"][1]["dependencies"] = []
    errors = check_product_canon.validate_registry(registry)
    assert "workstream IDs must be unique" in errors


def test_unknown_dependency_rejected():
    registry = _registry()
    registry["workstreams"][1]["dependencies"] = ["ART-99"]
    errors = check_product_canon.validate_registry(registry)
    assert "RT-01 has unknown dependency ART-99" in errors


def test_self_dependency_rejected():
    registry = _registry()
    registry["workstreams"][0]["dependencies"] = ["GOV-01"]
    errors = check_product_canon.validate_registry(registry)
    assert "GOV-01 depends on itself" in errors


def test_dependency_cycle_rejected():
    registry = _registry()
    registry["workstreams"][0]["dependencies"] = ["RT-01"]
    errors = check_product_canon.validate_registry(registry)
    assert any("dependency cycle" in error for error in errors)


def test_duplicate_exact_path_ownership_rejected():
    registry = _registry()
    registry["workstreams"][1]["owned_paths"] = ["docs/agentic3/PRODUCT-REALIZATION-PROGRAM.md"]
    errors = check_product_canon.validate_registry(registry)
    assert (
        "owned path 'docs/agentic3/PRODUCT-REALIZATION-PROGRAM.md' "
        "is claimed by GOV-01 and RT-01" in errors
    )


def test_state_outside_allowed_vocabulary_rejected():
    registry = _registry()
    registry["workstreams"][1]["state"] = "shipping"
    errors = check_product_canon.validate_registry(registry)
    assert "RT-01.state is not allowed: shipping" in errors


def test_missing_baseline_inputs_rejected():
    registry = _registry()
    registry["baseline"]["governing_inputs"] = []
    errors = check_product_canon.validate_registry(registry)
    assert "baseline.governing_inputs is required" in errors

    registry = _registry()
    del registry["baseline"]["commit"]
    errors = check_product_canon.validate_registry(registry)
    assert "baseline.commit is required" in errors

    registry = _registry()
    registry["baseline"]["commit"] = "HEAD"
    errors = check_product_canon.validate_registry(registry)
    assert "baseline.commit must be a 40-character lowercase SHA" in errors


def test_missing_workstream_fields_rejected():
    registry = _registry()
    del registry["workstreams"][1]["collision_policy"]
    del registry["workstreams"][1]["owner_role"]
    errors = check_product_canon.validate_registry(registry)
    assert "workstreams[1] missing fields: collision_policy, owner_role" in errors


def test_cli_exit_codes(tmp_path, monkeypatch, capsys):
    valid = tmp_path / "valid.json"
    valid.write_text(json.dumps(_registry()))
    monkeypatch.setattr("sys.argv", ["check_product_canon.py", str(valid)])
    assert check_product_canon.main() == 0
    assert "product canon valid" in capsys.readouterr().out

    broken = _registry()
    broken["workstreams"] = []
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps(broken))
    monkeypatch.setattr("sys.argv", ["check_product_canon.py", str(invalid)])
    assert check_product_canon.main() == 1
    assert "PRODUCT CANON INVALID" in capsys.readouterr().out

    garbled = tmp_path / "garbled.json"
    garbled.write_text("{not json")
    monkeypatch.setattr("sys.argv", ["check_product_canon.py", str(garbled)])
    assert check_product_canon.main() == 1
    assert "PRODUCT CANON INVALID" in capsys.readouterr().out
