"""R analysis worker runner — availability, input validation, and the
subprocess boundary (CSV framing in, JSON out) with its error paths.

The real ``Rscript`` is never invoked: ``subprocess.run`` is stubbed so these
stay hermetic unit tests regardless of whether R is installed on the host.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from app.analysis import r_worker
from app.analysis.r_worker import RNotAvailable, RWorkerError, r_available, run_summary


def test_r_available_reflects_which(monkeypatch):
    monkeypatch.setattr(r_worker.shutil, "which", lambda _name: "/usr/bin/Rscript")
    assert r_available() is True
    monkeypatch.setattr(r_worker.shutil, "which", lambda _name: None)
    assert r_available() is False


def test_run_summary_raises_when_rscript_missing(monkeypatch):
    monkeypatch.setattr(r_worker, "r_available", lambda: False)
    with pytest.raises(RNotAvailable):
        run_summary([{"value": 1}], "value")


def test_run_summary_rejects_empty_records(monkeypatch):
    monkeypatch.setattr(r_worker, "r_available", lambda: True)
    with pytest.raises(RWorkerError, match="no records"):
        run_summary([], "value")


def test_run_summary_writes_csv_and_parses_json(monkeypatch):
    monkeypatch.setattr(r_worker, "r_available", lambda: True)
    captured: dict = {}

    def fake_run(cmd, capture_output, text, timeout):
        # The worker builds a fixed argv and writes the records to a temp CSV
        # that still exists while the subprocess "runs" — read it back to prove
        # the language-neutral framing (CSV path + value column).
        captured["cmd"] = cmd
        captured["timeout"] = timeout
        captured["csv"] = Path(cmd[2]).read_text()
        return subprocess.CompletedProcess(
            cmd, 0, stdout=json.dumps({"mean": 2.0, "sum": 6.0}), stderr=""
        )

    monkeypatch.setattr(r_worker.subprocess, "run", fake_run)
    out = run_summary([{"value": 1}, {"value": 2}, {"value": 3}], "value")

    assert out == {"mean": 2.0, "sum": 6.0}
    assert captured["cmd"][0] == "Rscript"
    assert captured["cmd"][3] == "value"
    assert captured["timeout"] == 60
    assert "value" in captured["csv"]  # header
    assert "1" in captured["csv"] and "3" in captured["csv"]  # rows


def test_run_summary_raises_on_nonzero_exit(monkeypatch):
    monkeypatch.setattr(r_worker, "r_available", lambda: True)

    def fake_run(cmd, capture_output, text, timeout):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="R exploded")

    monkeypatch.setattr(r_worker.subprocess, "run", fake_run)
    with pytest.raises(RWorkerError, match="R exploded"):
        run_summary([{"value": 1}], "value")


def test_run_summary_nonzero_exit_uses_default_message(monkeypatch):
    monkeypatch.setattr(r_worker, "r_available", lambda: True)

    def fake_run(cmd, capture_output, text, timeout):
        return subprocess.CompletedProcess(cmd, 2, stdout="", stderr="   ")

    monkeypatch.setattr(r_worker.subprocess, "run", fake_run)
    with pytest.raises(RWorkerError, match="R worker failed"):
        run_summary([{"value": 1}], "value")


def test_run_summary_raises_on_invalid_json(monkeypatch):
    monkeypatch.setattr(r_worker, "r_available", lambda: True)

    def fake_run(cmd, capture_output, text, timeout):
        return subprocess.CompletedProcess(cmd, 0, stdout="not-json", stderr="")

    monkeypatch.setattr(r_worker.subprocess, "run", fake_run)
    with pytest.raises(RWorkerError, match="invalid R output"):
        run_summary([{"value": 1}], "value")
