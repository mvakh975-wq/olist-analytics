from tests.conftest import query


def test_customers_unique_and_consistent(built_db):
    assert query(
        built_db, "select count(*) - count(distinct customer_unique_id) from dim_customers"
    ) == [(0,)]
    ((orders,),) = query(built_db, "select count(*) from fct_orders where is_valid_order")
    ((summed,),) = query(built_db, "select sum(n_orders) from dim_customers")
    assert orders == summed


def test_repeat_customer_has_two_orders(built_db):
    ((repeaters,),) = query(built_db, "select count(*) from dim_customers where n_orders > 1")
    assert repeaters >= 1


def test_order_items_gmv_matches_orders(built_db):
    ((a,),) = query(built_db, "select sum(price + freight_value) from fct_order_items")
    ((b,),) = query(built_db, "select sum(gmv) from fct_orders")
    assert a == b


def test_analysis_period_flag(built_db):
    rows = query(
        built_db,
        """select count(*) from fct_orders
           where is_analysis_period <> (purchase_month between '2017-01-01' and '2018-08-01')""",
    )
    assert rows == [(0,)]


def test_seller_late_rate_bounds(built_db):
    assert query(
        built_db, "select count(*) from dim_sellers where late_rate < 0 or late_rate > 1"
    ) == [(0,)]
    ((n,),) = query(built_db, "select count(*) from dim_sellers where n_orders > 0")
    assert n >= 1
