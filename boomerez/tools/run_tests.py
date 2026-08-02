#!/usr/bin/env python3
"""Boomerez test suite — run by CI and locally.

Checks repo structure, token integrity, the earl-lint rubric config, and
.gitignore coverage, then rubric-lints any app HTML present. Exits non-zero
on the first category of failure so CI fails on errors. Stdlib only.

Usage: python3 tools/run_tests.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FAILURES: list = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'ok' if ok else 'FAIL'}  {label}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        FAILURES.append(label)


def test_structure() -> None:
    print("Repo structure:")
    for rel in [
        "apps/mode-studio",
        "packages/tokens/tokens.css",
        "packages/earl-lint/earl_lint.py",
        "packages/earl-lint/rubric.json",
        "tools/build.py",
        "docs/DESIGN-STANDARD.md",
        "docs/DEVLOG.md",
        "README.md",
        "LICENSE",
        ".gitignore",
        ".github/workflows/ci.yml",
    ]:
        check(rel, (ROOT / rel).exists(), "missing")


def test_tokens() -> None:
    print("Design tokens:")
    css = (ROOT / "packages/tokens/tokens.css").read_text(encoding="utf-8")
    props = re.findall(r"--bz-[\w-]+\s*:", css)
    check("tokens.css defines :root block", ":root" in css)
    check("tokens.css defines --bz- custom properties", len(props) >= 10,
          f"only {len(props)} found")
    check("tokens.css braces balanced", css.count("{") == css.count("}"))


def test_rubric() -> None:
    print("earl-lint rubric:")
    rubric = json.loads((ROOT / "packages/earl-lint/rubric.json").read_text(encoding="utf-8"))
    check("rubric declares criterion CC-3", rubric.get("criterion") == "CC-3")
    rules = rubric.get("rules", [])
    check("rubric has rules", len(rules) > 0)
    check("rules have id/check/description",
          all({"id", "check", "description"} <= set(r) for r in rules))


def test_gitignore() -> None:
    print(".gitignore coverage:")
    lines = {
        ln.strip() for ln in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    }
    check("ignores /dist/", "/dist/" in lines or "dist/" in lines)
    check("ignores node_modules", "node_modules/" in lines or "node_modules" in lines)
    check("ignores .env", ".env" in lines)
    check("ignores audio files", "*.mp3" in lines and "*.wav" in lines)
    check("ignores video files", "*.mp4" in lines and "*.mov" in lines)


def test_devlog() -> None:
    print("Dev log:")
    devlog = (ROOT / "docs/DEVLOG.md").read_text(encoding="utf-8")
    check("DEVLOG has a dated entry (## YYYY-MM-DD)",
          bool(re.search(r"^## \d{4}-\d{2}-\d{2}", devlog, re.MULTILINE)))


def test_earl_lint_runs() -> None:
    print("earl-lint execution:")
    result = subprocess.run(
        [sys.executable, str(ROOT / "packages/earl-lint/earl_lint.py"), str(ROOT / "apps")],
        capture_output=True, text=True,
    )
    detail = (result.stdout + result.stderr).strip().replace("\n", " | ")
    check("earl-lint exits cleanly over apps/", result.returncode == 0, detail)


def main() -> int:
    for test in (test_structure, test_tokens, test_rubric, test_gitignore,
                 test_devlog, test_earl_lint_runs):
        test()
    if FAILURES:
        print(f"\n{len(FAILURES)} test failure(s).")
        return 1
    print("\nAll tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
