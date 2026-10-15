"""R analysis worker runner.

Shells out to the R script via Rscript through a language-neutral job interface
(CSV path + column in, JSON out), so the domain never imports or depends on R.
If Rscript is not installed, ``RNotAvailable`` is raised and callers fall back to
the Python worker.
"""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

_R_SCRIPT = Path(__file__).parent / "r" / "summary.R"


class RNotAvailable(RuntimeError):
    pass


class RWorkerError(RuntimeError):
    pass


def r_available() -> bool:
    return shutil.which("Rscript") is not None


def run_summary(records: list[dict[str, Any]], value_column: str) -> dict[str, float]:
    if not r_available():
        raise RNotAvailable("Rscript is not installed")
    if not records:
        raise RWorkerError("no records to analyze")

    with tempfile.TemporaryDirectory() as tmp:
        csv_path = Path(tmp) / "data.csv"
        fieldnames = list(records[0].keys())
        with csv_path.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

        # Fixed args, no shell; Rscript resolved via PATH after the which() check.
        cmd = ["Rscript", str(_R_SCRIPT), str(csv_path), value_column]  # noqa: S607
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)  # noqa: S603
    if proc.returncode != 0:
        raise RWorkerError(proc.stderr.strip() or "R worker failed")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RWorkerError(f"invalid R output: {proc.stdout!r}") from exc
