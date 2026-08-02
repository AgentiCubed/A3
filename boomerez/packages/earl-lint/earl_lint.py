#!/usr/bin/env python3
"""earl-lint: rubric linter for Boomerez HTML artifacts.

Implements design standard criterion CC-3 (docs/DESIGN-STANDARD.md): every
shipped HTML artifact must pass the rubric in rubric.json with zero errors.

Usage:
    python3 packages/earl-lint/earl_lint.py <file-or-dir> [...]

Exit codes: 0 = clean, 1 = rubric errors found, 2 = usage/config problem.
Stdlib only.
"""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

RUBRIC_PATH = Path(__file__).parent / "rubric.json"


class DocumentFacts(HTMLParser):
    """Collects the facts rubric rules assert against."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.has_doctype = False
        self.html_lang = None
        self.title_text = ""
        self._in_title = False
        self.has_viewport_meta = False
        self.imgs_missing_alt = 0

    def handle_decl(self, decl: str) -> None:
        if decl.lower().startswith("doctype html"):
            self.has_doctype = True

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attrs_d = dict(attrs)
        if tag == "html":
            self.html_lang = attrs_d.get("lang")
        elif tag == "title":
            self._in_title = True
        elif tag == "meta" and attrs_d.get("name", "").lower() == "viewport":
            self.has_viewport_meta = True
        elif tag == "img" and not (attrs_d.get("alt") or "").strip():
            self.imgs_missing_alt += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_text += data


CHECKS = {
    "doctype": lambda f, src: f.has_doctype,
    "html-lang": lambda f, src: bool((f.html_lang or "").strip()),
    "title-nonempty": lambda f, src: bool(f.title_text.strip()),
    "viewport-meta": lambda f, src: f.has_viewport_meta,
    "img-alt": lambda f, src: f.imgs_missing_alt == 0,
    "tokens-linked": lambda f, src: bool(re.search(r"tokens\.css|--bz-", src)),
}


def load_rubric() -> list:
    rubric = json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))
    for rule in rubric["rules"]:
        if rule["check"] not in CHECKS:
            sys.exit(f"earl-lint: rubric rule {rule['id']} references "
                     f"unknown check {rule['check']!r}")
    return rubric["rules"]


def lint_file(path: Path, rules: list) -> list:
    src = path.read_text(encoding="utf-8", errors="replace")
    facts = DocumentFacts()
    facts.feed(src)
    facts.close()
    return [rule for rule in rules if not CHECKS[rule["check"]](facts, src)]


def collect_html(args: list) -> list:
    files = []
    for arg in args:
        p = Path(arg)
        if p.is_dir():
            files.extend(sorted(p.rglob("*.html")))
        elif p.is_file():
            files.append(p)
        else:
            sys.exit(f"earl-lint: no such file or directory: {arg}")
    return files


def main(argv: list) -> int:
    if not argv:
        print(__doc__)
        return 2
    rules = load_rubric()
    files = collect_html(argv)
    if not files:
        print("earl-lint: no HTML files found; nothing to lint.")
        return 0
    errors = 0
    for path in files:
        for rule in lint_file(path, rules):
            errors += 1
            print(f"{path}: [{rule['id']}] {rule['description']}")
    if errors:
        print(f"earl-lint: {errors} rubric error(s) across {len(files)} file(s).")
        return 1
    print(f"earl-lint: {len(files)} file(s) clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
