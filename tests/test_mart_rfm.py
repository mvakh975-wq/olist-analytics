from tests.conftest import query

SEGMENTS = {
    "Champions",
    "Loyal",
    "Promising high-value",
    "Recent",
    "At risk high-value",
    "Hibernating",
}


def test_every_customer_has_one_segment(built_db):
    ((a,),) = query(built_db, "select count(*) from mart_rfm")
    ((b,),) = query(built_db, "select count(*) from dim_customers")
    assert a == b
    assert {s for (s,) in query(built_db, "select distinct segment from mart_rfm")} <= SEGMENTS
    assert query(built_db, "select count(*) from mart_rfm where segment is null") == [(0,)]


def test_repeat_buyers_are_loyal_or_champions(built_db):
    rows = query(
        built_db,
        "select count(*) from mart_rfm where frequency >= 2 and segment not in ('Champions', 'Loyal')",
    )
    assert rows == [(0,)]
    ((n,),) = query(built_db, "select count(*) from mart_rfm where frequency >= 2")
    assert n >= 1


def test_scores_in_range(built_db):
    assert query(
        built_db,
        """select count(*) from mart_rfm where r_score not between 1 and 5
           or m_score not between 1 and 5 or f_score not between 1 and 3""",
    ) == [(0,)]


def test_recency_score_rewards_recent_customers(built_db):
    # the most recent customer gets the top recency score, the least recent the bottom one
    rows = query(
        built_db,
        """select
             (select r_score from mart_rfm order by recency_days asc, customer_unique_id limit 1),
             (select r_score from mart_rfm order by recency_days desc, customer_unique_id limit 1)""",
    )
    assert rows == [(5, 1)]
