"""Python (pandas/matplotlib) and R analysis workers — real, no mocks."""

from __future__ import annotations

import pytest

from app.analysis import r_worker

_DATA = [
    {"label": "A", "value": 10},
    {"label": "B", "value": 20},
    {"label": "C", "value": 30},
]


def test_python_summary_stats():
    pytest.importorskip("pandas")
    from app.analysis.python_worker import summary_stats

    s = summary_stats(_DATA, "value")
    assert s["count"] == 3
    assert s["mean"] == 20.0
    assert s["sum"] == 60.0
    assert s["max"] == 30.0


def test_python_bar_chart_returns_png():
    pytest.importorskip("matplotlib")
    pytest.importorskip("pandas")
    from app.analysis.python_worker import bar_chart_png

    png = bar_chart_png(_DATA, "label", "value", title="Test")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic number
    assert len(png) > 1000


def test_r_worker_when_available():
    if not r_worker.r_available():
        pytest.skip("Rscript not installed")
    out = r_worker.run_summary(_DATA, "value")
    assert out["n"] == 3
    assert out["mean"] == 20
    assert out["sum"] == 60
