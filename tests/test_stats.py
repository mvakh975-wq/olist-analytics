import numpy as np
import pandas as pd

from scripts.stats import bootstrap_diff_ci, delay_by_state, delay_effect


def test_bootstrap_ci_contains_true_difference():
    rng = np.random.default_rng(0)
    a = rng.normal(4.0, 1.0, 2000)
    b = rng.normal(3.0, 1.0, 2000)
    diff, lo, hi = bootstrap_diff_ci(a, b)
    assert lo < -1.0 < hi
    assert abs(diff + 1.0) < 0.1
    assert hi - lo < 0.2


def test_bootstrap_is_deterministic():
    a, b = np.arange(50.0), np.arange(50.0) + 1
    assert bootstrap_diff_ci(a, b) == bootstrap_diff_ci(a, b)


def deliveries(n_on_time=400, n_late=100, late_score=2, state="SP"):
    return pd.DataFrame(
        {
            "customer_state": state,
            "is_late": [False] * n_on_time + [True] * n_late,
            "delay_days": [-3] * n_on_time + [20] * n_late,
            "review_score": [5] * n_on_time + [late_score] * n_late,
        }
    )


def test_delay_effect_rows_and_signs():
    effect = delay_effect(deliveries())
    assert list(effect.comparison) == ["late vs on time", "15+ days late vs on time"]
    row = effect.iloc[0]
    assert row.n_on_time == 400 and row.n_late == 100
    assert row["diff"] == -3.0
    assert row.ci_low <= -3.0 <= row.ci_high
    assert row.mannwhitney_p < 0.001
    # late orders score lower, so the rank-biserial correlation is negative
    assert row.rank_biserial == -1.0


def test_delay_by_state_skips_states_with_too_few_late_orders():
    df = pd.concat([deliveries(state="SP"), deliveries(n_late=10, state="AC")])
    by_state = delay_by_state(df)
    assert list(by_state.customer_state) == ["SP"]
    assert by_state.iloc[0]["diff"] == -3.0


def test_delay_effect_does_not_depend_on_row_order():
    rng = np.random.default_rng(1)
    df = pd.DataFrame(
        {
            "customer_state": "SP",
            "is_late": rng.random(600) < 0.2,
            "delay_days": rng.integers(-10, 30, 600),
            "review_score": rng.integers(1, 6, 600),
        }
    )
    df["is_late"] = df.delay_days > 0
    shuffled = df.sample(frac=1, random_state=7)
    pd.testing.assert_frame_equal(delay_effect(df), delay_effect(shuffled))
