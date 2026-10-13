from tests.conftest import query, raw


def test_monthly_gmv_reconciles_with_raw(built_db):
    ((mart,),) = query(built_db, "select sum(gmv) from mart_monthly_kpis")
    ((expected,),) = query(
        built_db,
        f"""select sum(i.price::decimal(12,2) + i.freight_value::decimal(12,2))
            from {raw("olist_order_items_dataset")} i
            join {raw("olist_orders_dataset")} o using (order_id)
            where o.order_status not in ('canceled', 'unavailable')""",
    )
    assert mart == expected


def test_monthly_orders_reconcile_with_raw(built_db):
    ((mart,),) = query(built_db, "select sum(orders) from mart_monthly_kpis")
    ((expected,),) = query(
        built_db,
        f"""select count(distinct o.order_id)
            from {raw("olist_orders_dataset")} o
            join {raw("olist_order_items_dataset")} i using (order_id)
            where o.order_status not in ('canceled', 'unavailable')""",
    )
    assert mart == expected


def test_one_row_per_month(built_db):
    assert query(built_db, "select count(*) - count(distinct month) from mart_monthly_kpis") == [
        (0,)
    ]


def test_edge_months_flagged(built_db):
    rows = query(
        built_db,
        """select count(*) from mart_monthly_kpis
           where is_analysis_period <> (month between '2017-01-01' and '2018-08-01')""",
    )
    assert rows == [(0,)]


def test_new_customers_never_exceed_customers(built_db):
    assert query(
        built_db, "select count(*) from mart_monthly_kpis where new_customers > customers"
    ) == [(0,)]
    ((new_total,),) = query(built_db, "select sum(new_customers) from mart_monthly_kpis")
    ((people,),) = query(built_db, "select count(*) from dim_customers")
    assert new_total == people
