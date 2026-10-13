from tests.conftest import query


def test_month_zero_is_full_cohort(built_db):
    rows = query(
        built_db,
        "select count(*) from mart_cohort_retention where months_since_first = 0 and retention <> 1",
    )
    assert rows == [(0,)]


def test_cohort_sizes_sum_to_customers(built_db):
    ((a,),) = query(
        built_db, "select sum(cohort_size) from mart_cohort_retention where months_since_first = 0"
    )
    ((b,),) = query(built_db, "select count(*) from dim_customers")
    assert a == b


def test_repeat_customer_counted_once_per_cohort(built_db):
    # the fixture's repeat customer has two orders under two different customer_id values
    ((cohort_people,),) = query(
        built_db, "select sum(cohort_size) from mart_cohort_retention where months_since_first = 0"
    )
    ((customer_ids,),) = query(
        built_db, "select count(distinct customer_id) from fct_orders where is_valid_order"
    )
    assert cohort_people < customer_ids


def test_repeat_purchase_shows_up_as_retention(built_db):
    ((later_active,),) = query(
        built_db,
        """select coalesce(sum(active_customers), 0) from mart_cohort_retention
           where months_since_first > 0""",
    )
    ((repeaters_later_month,),) = query(
        built_db,
        """select count(*) from dim_customers
           where date_trunc('month', last_order_at) > first_order_month""",
    )
    assert later_active >= repeaters_later_month


def test_retention_bounds(built_db):
    assert query(
        built_db, "select count(*) from mart_cohort_retention where retention < 0 or retention > 1"
    ) == [(0,)]


def test_no_unobservable_months(built_db):
    rows = query(
        built_db,
        """select count(*) from mart_cohort_retention
           where cohort_month + to_months(months_since_first)
                 > (select max(purchase_month) from fct_orders)""",
    )
    assert rows == [(0,)]
