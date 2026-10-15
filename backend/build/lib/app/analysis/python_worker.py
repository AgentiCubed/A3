"""Python analysis worker (real — pandas + matplotlib).

Computes summary statistics over a tabular dataset and renders a bar-chart PNG.
Pure compute + bytes out; the caller persists the chart via the ArtifactStore.
Runs headless (Agg backend), so it works in CI/containers with no display.
"""

from __future__ import annotations

import io
from typing import Any


def summary_stats(records: list[dict[str, Any]], value_column: str) -> dict[str, float]:
    import pandas as pd

    df = pd.DataFrame(records)
    if value_column not in df.columns:
        raise ValueError(f"column not found: {value_column}")
    col = pd.to_numeric(df[value_column], errors="coerce").dropna()
    return {
        "count": float(col.count()),
        "mean": round(float(col.mean()), 4) if len(col) else 0.0,
        "std": round(float(col.std(ddof=1)), 4) if len(col) > 1 else 0.0,
        "min": float(col.min()) if len(col) else 0.0,
        "max": float(col.max()) if len(col) else 0.0,
        "sum": float(col.sum()),
    }


def bar_chart_png(
    records: list[dict[str, Any]], label_column: str, value_column: str, *, title: str = ""
) -> bytes:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd

    df = pd.DataFrame(records)
    labels = df[label_column].astype(str).tolist()
    values = pd.to_numeric(df[value_column], errors="coerce").fillna(0).tolist()

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(labels, values, color="#2f6fed")
    ax.set_title(title or f"{value_column} by {label_column}")
    ax.set_ylabel(value_column)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    return buf.getvalue()
