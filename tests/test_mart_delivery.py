from tests.conftest import query


def test_only_measurable_deliveries(built_db):
    assert query(
        built_db, "select count(*) from mart_delivery_performance where delay_days is null"
    ) == [(0,)]
    ((a,),) = query(built_db, "select count(*) from mart_delivery_performance")
    ((b,),) = query(built_db, "select count(*) from fct_orders where delay_days is not null")
    assert a == b


def test_buckets_match_delay(built_db):
    bounds = {
        "On time or early": (None, 0),
        "1–3 days late": (1, 3),
        "4–7 days late": (4, 7),
        "8–14 days late": (8, 14),
        "15+ days late": (15, None),
    }
    rows = query(
        built_db,
        "select delay_bucket, min(delay_days), max(delay_days) from mart_delivery_performance group by 1",
    )
    assert rows, "fixture must contain delivered orders"
    for bucket, lo, hi in rows:
        want_lo, want_hi = bounds[bucket]
        assert want_lo is None or lo >= want_lo, bucket
        assert want_hi is None or hi <= want_hi, bucket


def test_bucket_order_is_consistent(built_db):
    rows = query(
        built_db,
        "select count(distinct delay_bucket_order) - count(distinct delay_bucket) from mart_delivery_performance",
    )
    assert rows == [(0,)]


def test_low_score_flag(built_db):
    rows = query(
        built_db,
        """select count(*) from mart_delivery_performance
           where (review_score is null) <> (is_low_score is null)
              or is_low_score <> (review_score <= 2)""",
    )
    assert rows == [(0,)]
