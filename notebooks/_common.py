"""Shared helpers for the analysis notebooks."""

import sys
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "olist.duckdb"
MARTS = ROOT / "data" / "marts"

# lets notebooks import the shared statistics from scripts/
sys.path.insert(0, str(ROOT))

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
