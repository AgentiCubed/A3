"""Dependency-audit gate (next-steps Step 2, gap G3).

Runs the ecosystem's native auditor and fails the build on non-waived
findings, so a vulnerable pin is caught by the pipeline instead of a human:

    python scripts/dependency_audit.py backend    # pip-audit over the venv
    python scripts/dependency_audit.py frontend   # npm audit over the lockfile

Backend fails on ANY non-waived known vulnerability (pip-audit does not
report reliable severities). Frontend fails on non-waived advisories at or
above --fail-level (default: critical).

Waivers live in scripts/dependency-audit-waivers.json:

    [{"id": "GHSA-... | PYSEC-... | CVE-...", "ecosystem": "python|npm",
      "reason": "why this is acceptable", "expires": "YYYY-MM-DD"}]

A waiver PAST its expiry date is not applied — the finding resurfaces and
fails the gate, so waivers cannot rot silently. Stdlib only; no third-party
imports, so the gate itself adds no auditable surface.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WAIVERS = Path(__file__).resolve().parent / "dependency-audit-waivers.json"
_SEVERITY_ORDER = ["info", "low", "moderate", "high", "critical"]
_GHSA_RE = re.compile(r"GHSA-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}")


def load_waivers(path: Path, ecosystem: str, today: str) -> tuple[set[str], list[str]]:
    """Return (active waiver ids, report lines). Expired waivers are dropped loudly."""
    lines: list[str] = []
    if not path.exists():
        return set(), lines
    active: set[str] = set()
    for entry in json.loads(path.read_text()):
        if entry.get("ecosystem") != ecosystem:
            continue
        wid, expires = entry["id"], entry["expires"]
        if expires < today:
            lines.append(
                f"WARNING: waiver for {wid} EXPIRED {expires} "
                f"({entry.get('reason', 'no reason recorded')}) — finding will fail the gate"
            )
        else:
            active.add(wid)
            lines.append(
                f"waiver active until {expires}: {wid} — {entry.get('reason', '')}"
            )
    return active, lines


def audit_backend(waivers: set[str]) -> list[str]:
    """Run pip-audit over the current environment; return non-waived finding lines."""
    proc = subprocess.run(
        [sys.executable, "-m", "pip_audit", "--skip-editable", "-f", "json"],
        capture_output=True,
        text=True,
    )
    if proc.returncode not in (
        0,
        1,
    ):  # 1 = vulnerabilities found; anything else is a tool error
        raise RuntimeError(f"pip-audit failed to run:\n{proc.stderr}")
    report = json.loads(proc.stdout)
    failures = []
    for dep in report.get("dependencies", []):
        for vuln in dep.get("vulns", []):
            ids = {vuln["id"], *vuln.get("aliases", [])}
            if ids & waivers:
                continue
            fixes = ", ".join(vuln.get("fix_versions", [])) or "no fix released"
            failures.append(
                f"{dep['name']} {dep['version']}: {vuln['id']} (fix: {fixes})"
            )
    return failures


def npm_failures(report: dict, waivers: set[str], fail_level: str) -> list[str]:
    """Pure filter over an `npm audit --json` report (unit-tested hermetically).

    Judged per advisory, not per package rollup: an advisory fails the gate
    when its own severity is at/above the threshold and its GHSA id is not
    waived. Entries in ``via`` that are plain strings are dependency-chain
    references — the root advisory is reported (and waivable) on the package
    that names it, so chains are skipped here.
    """
    threshold = _SEVERITY_ORDER.index(fail_level)
    failures = []
    for name, vuln in report.get("vulnerabilities", {}).items():
        for adv in vuln.get("via", []):
            if not isinstance(adv, dict):
                continue
            if _SEVERITY_ORDER.index(adv.get("severity", "info")) < threshold:
                continue
            match = _GHSA_RE.search(adv.get("url", ""))
            ghsa = match.group(0) if match else None
            if ghsa is not None and ghsa in waivers:
                continue
            failures.append(
                f"{name} ({adv.get('severity')}): {adv.get('title', '?')} [{ghsa or 'no GHSA id'}]"
            )
    return failures


def audit_frontend(waivers: set[str], fail_level: str) -> list[str]:
    npm = shutil.which("npm")
    if npm is None:
        raise RuntimeError("npm not found on PATH")
    proc = subprocess.run(  # noqa: S603 - fixed args, resolved binary
        [npm, "audit", "--json", "--audit-level=info"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT / "frontend",
    )
    if not proc.stdout.strip():
        raise RuntimeError(f"npm audit produced no report:\n{proc.stderr}")
    return npm_failures(json.loads(proc.stdout), waivers, fail_level)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ecosystem", choices=["backend", "frontend"])
    parser.add_argument("--waivers", type=Path, default=DEFAULT_WAIVERS)
    parser.add_argument("--fail-level", choices=_SEVERITY_ORDER, default="critical")
    args = parser.parse_args()

    today = datetime.now(UTC).date().isoformat()
    eco = "python" if args.ecosystem == "backend" else "npm"
    waivers, waiver_lines = load_waivers(args.waivers, eco, today)
    for line in waiver_lines:
        print(line)

    if args.ecosystem == "backend":
        failures = audit_backend(waivers)
    else:
        failures = audit_frontend(waivers, args.fail_level)

    if failures:
        print(
            f"\nDEPENDENCY AUDIT FAILED ({args.ecosystem}): {len(failures)} finding(s)"
        )
        for f in failures:
            print(f"  - {f}")
        print(
            "\nFix the pin, or add a justified waiver WITH AN EXPIRY DATE to",
            args.waivers,
        )
        return 1
    print(f"dependency audit clean ({args.ecosystem})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
