"""Hermetic tests for the dependency-audit gate's decision logic.

The gate itself (scripts/dependency_audit.py) shells out to pip-audit and
npm audit in CI; these tests pin down the pure parts — severity thresholds,
GHSA waiver matching, and the expiring-waiver policy — with canned reports,
so the gate's behavior is proven without network access.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "dependency_audit.py"
_spec = importlib.util.spec_from_file_location("dependency_audit", _SCRIPT)
dependency_audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dependency_audit)


def _npm_report() -> dict:
    return {
        "vulnerabilities": {
            "next": {
                "name": "next",
                "severity": "critical",
                "via": [
                    {
                        "title": "Authorization Bypass in Middleware",
                        "url": "https://github.com/advisories/GHSA-f82v-jwr5-mffw",
                        "severity": "critical",
                    },
                    {
                        "title": "DoS with Server Components",
                        "url": "https://github.com/advisories/GHSA-q4gf-8mx6-v5v3",
                        "severity": "high",
                    },
                ],
            },
            "vitest": {
                "name": "vitest",
                "severity": "critical",
                # Severity inherited through a dependency chain: via is a
                # plain string reference, the root advisory lives elsewhere.
                "via": ["vite"],
            },
            "postcss": {
                "name": "postcss",
                "severity": "moderate",
                "via": [
                    {
                        "title": "line return parsing error",
                        "url": "https://github.com/advisories/GHSA-7fh5-64p2-3v2j",
                        "severity": "moderate",
                    }
                ],
            },
        }
    }


def test_npm_fails_on_unwaived_critical_only():
    failures = dependency_audit.npm_failures(_npm_report(), waivers=set(), fail_level="critical")
    # The critical advisory fails; the high advisory and the moderate package
    # are below the threshold; the chain-only entry is skipped (reported at
    # its root).
    assert len(failures) == 1
    assert "GHSA-f82v-jwr5-mffw" in failures[0]


def test_npm_waiver_suppresses_exactly_its_advisory():
    failures = dependency_audit.npm_failures(
        _npm_report(), waivers={"GHSA-f82v-jwr5-mffw"}, fail_level="critical"
    )
    assert failures == []
    # The waiver does not blanket the package: at fail-level high the
    # unwaived high advisory on the same package still fails.
    failures = dependency_audit.npm_failures(
        _npm_report(), waivers={"GHSA-f82v-jwr5-mffw"}, fail_level="high"
    )
    assert len(failures) == 1
    assert "GHSA-q4gf-8mx6-v5v3" in failures[0]


def test_npm_fail_level_moderate_catches_moderate():
    failures = dependency_audit.npm_failures(_npm_report(), waivers=set(), fail_level="moderate")
    assert any("postcss" in f for f in failures)


def _write_waivers(tmp_path: Path, entries: list[dict]) -> Path:
    path = tmp_path / "waivers.json"
    path.write_text(json.dumps(entries))
    return path


def test_expired_waiver_is_not_applied_and_warns(tmp_path):
    path = _write_waivers(
        tmp_path,
        [
            {
                "id": "PYSEC-0000-1",
                "ecosystem": "python",
                "reason": "old",
                "expires": "2026-01-01",
            },
            {
                "id": "PYSEC-0000-2",
                "ecosystem": "python",
                "reason": "current",
                "expires": "2099-01-01",
            },
        ],
    )
    active, lines = dependency_audit.load_waivers(path, "python", today="2026-07-21")
    assert active == {"PYSEC-0000-2"}
    assert any("EXPIRED" in line and "PYSEC-0000-1" in line for line in lines)


def test_waivers_are_scoped_to_their_ecosystem(tmp_path):
    path = _write_waivers(
        tmp_path,
        [
            {
                "id": "GHSA-xxxx-yyyy-zzzz",
                "ecosystem": "npm",
                "reason": "r",
                "expires": "2099-01-01",
            }
        ],
    )
    active, _ = dependency_audit.load_waivers(path, "python", today="2026-07-21")
    assert active == set()
    active, _ = dependency_audit.load_waivers(path, "npm", today="2026-07-21")
    assert active == {"GHSA-xxxx-yyyy-zzzz"}


def test_missing_waiver_file_means_no_waivers(tmp_path):
    active, lines = dependency_audit.load_waivers(
        tmp_path / "absent.json", "python", today="2026-07-21"
    )
    assert active == set()
    assert lines == []


def test_repo_waiver_file_is_well_formed():
    """Every committed waiver carries an id, ecosystem, reason, and expiry."""
    entries = json.loads(dependency_audit.DEFAULT_WAIVERS.read_text())
    for entry in entries:
        assert entry["ecosystem"] in {"python", "npm"}
        assert entry["id"]
        assert entry["reason"]
        # ISO date, parseable and four-digit-year
        assert len(entry["expires"]) == 10 and entry["expires"][4] == "-"
