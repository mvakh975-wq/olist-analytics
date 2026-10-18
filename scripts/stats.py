"""Statistics behind the delivery-vs-review findings, shared by notebook 04 and the export."""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

# a state enters the confounding check only with enough reviewed and late deliveries
MIN_STATE_ORDERS = 300
MIN_STATE_LATE = 30

REVIEWED_DELIVERIES = """
    select customer_state, main_category, is_late, delay_days, review_score
    from mart_delivery_performance
    where is_analysis_period and review_score is not null
"""


def bootstrap_diff_ci(a, b, n: int = 5000, seed: int = 42, alpha: float = 0.05):
    """Difference of means (b - a) with a percentile bootstrap confidence interval."""
    rng = np.random.default_rng(seed)
    a, b = np.asarray(a, float), np.asarray(b, float)
    diffs = np.empty(n)
    for k in range(n):
        diffs[k] = rng.choice(b, b.size).mean() - rng.choice(a, a.size).mean()
    lo, hi = np.quantile(diffs, [alpha / 2, 1 - alpha / 2])
    return float(b.mean() - a.mean()), float(lo), float(hi)


def _compare(name: str, on_time: np.ndarray, late: np.ndarray) -> dict:
    diff, lo, hi = bootstrap_diff_ci(on_time, late)
    u, p = mannwhitneyu(on_time, late, alternative="two-sided")
    return {
        "comparison": name,
        "n_on_time": len(on_time),
        "n_late": len(late),
        "mean_on_time": on_time.mean(),
        "mean_late": late.mean(),
        "diff": diff,
        "ci_low": lo,
        "ci_high": hi,
        "mannwhitney_p": p,
        # U counts on-time > late pairs, so the sign is negative when late orders score lower
        "rank_biserial": 1 - 2 * u / (len(on_time) * len(late)),
    }


def _scores(df: pd.DataFrame, mask) -> np.ndarray:
    # sorted, so the bootstrap does not depend on the order rows arrive from the database
    return np.sort(df.loc[mask, "review_score"].to_numpy(float))


def delay_effect(df: pd.DataFrame) -> pd.DataFrame:
    """Late vs on-time review scores: mean difference, 95% CI, Mann–Whitney U, rank-biserial."""
    on_time = _scores(df, ~df.is_late)
    late = _scores(df, df.is_late)
    very_late = _scores(df, df.delay_days >= 15)
    return pd.DataFrame(
        [
            _compare("late vs on time", on_time, late),
            _compare("15+ days late vs on time", on_time, very_late),
        ]
    )


def delay_by_state(df: pd.DataFrame) -> pd.DataFrame:
    """The late vs on-time gap inside each state with enough data (confounding check)."""
    rows = []
    for state, g in df.groupby("customer_state"):
        if len(g) < MIN_STATE_ORDERS or g.is_late.sum() < MIN_STATE_LATE:
            continue
        rows.append(
            {
                "customer_state": state,
                "n": len(g),
                "late_share": g.is_late.mean(),
                "mean_on_time": g.loc[~g.is_late, "review_score"].mean(),
                "mean_late": g.loc[g.is_late, "review_score"].mean(),
            }
        )
    columns = ["customer_state", "n", "late_share", "mean_on_time", "mean_late"]
    out = pd.DataFrame(rows, columns=columns)
    return out.assign(diff=out.mean_late - out.mean_on_time)


def write_delay_stats(db: Path, out_dir: Path) -> list[Path]:
    with duckdb.connect(str(db), read_only=True) as con:
        df = con.sql(REVIEWED_DELIVERIES).df()
    paths = [out_dir / "stats_delay_effect.parquet", out_dir / "stats_delay_by_state.parquet"]
    delay_effect(df).to_parquet(paths[0], index=False)
    delay_by_state(df).to_parquet(paths[1], index=False)
    return paths
