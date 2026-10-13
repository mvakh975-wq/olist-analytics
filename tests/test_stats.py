import numpy as np

from notebooks._common import bootstrap_diff_ci


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
