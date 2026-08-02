#!/usr/bin/env python3
"""Build Boomerez into dist/.

Copies app trees from apps/ and the shared tokens into dist/, then writes a
build manifest. dist/ is disposable and gitignored — this script recreates it
from scratch on every run. Stdlib only.

Usage: python3 tools/build.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APPS = ROOT / "apps"
TOKENS = ROOT / "packages" / "tokens" / "tokens.css"
DIST = ROOT / "dist"

EXCLUDE = {".gitkeep", ".DS_Store"}


def main() -> int:
    shutil.rmtree(DIST, ignore_errors=True)
    DIST.mkdir()

    copied = []

    shutil.copy2(TOKENS, DIST / "tokens.css")
    copied.append("tokens.css")

    if APPS.is_dir():
        for src in sorted(APPS.rglob("*")):
            if not src.is_file() or src.name in EXCLUDE:
                continue
            rel = src.relative_to(APPS)
            dest = DIST / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            copied.append(str(rel))

    manifest = DIST / "build-manifest.json"
    manifest.write_text(
        json.dumps({"files": copied}, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Built {len(copied)} file(s) into {DIST.relative_to(ROOT)}/ "
          f"(+ build-manifest.json).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
