"""Shared helpers for the analysis notebooks."""

from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import numpy as np

DB = Path(__file__).resolve().parents[1] / "olist.duckdb"
MARTS = Path(__file__).resolve().parents[1] / "data" / "marts"

ACCENT = "#2a78d6"  # main series
SIGNAL = "#e34948"  # negative values only (late deliveries, low scores)
MUTED = "#8a8984"  # context

plt.rcParams.update(
    {
        "figure.figsize": (9, 4),
        "figure.dpi": 110,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "#e6e5e1",
        "axes.axisbelow": True,
        "axes.titlelocation": "left",
        "axes.titlesize": 12,
    }
)


def con() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB), read_only=True)


def bootstrap_diff_ci(a, b, n: int = 5000, seed: int = 42, alpha: float = 0.05):
    """Difference of means (b - a) with a percentile bootstrap confidence interval."""
    rng = np.random.default_rng(seed)
    a, b = np.asarray(a, float), np.asarray(b, float)
    diffs = np.empty(n)
    for k in range(n):
        diffs[k] = rng.choice(b, b.size).mean() - rng.choice(a, a.size).mean()
    lo, hi = np.quantile(diffs, [alpha / 2, 1 - alpha / 2])
    return float(b.mean() - a.mean()), float(lo), float(hi)
