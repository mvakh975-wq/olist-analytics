from pathlib import Path

import duckdb

from scripts.download import RAW_FILES

FIX = Path(__file__).parent / "fixtures" / "raw"


def q(sql: str):
    return duckdb.sql(sql.replace("FIX", str(FIX))).fetchone()[0]


def test_all_files_present():
    assert sorted(p.name for p in FIX.glob("*.csv")) == sorted(RAW_FILES)


def test_fixture_covers_edge_cases():
    # a person with two orders under two different customer_id values
    assert (
        q("""select count(*) from (select c.customer_unique_id
               from 'FIX/olist_orders_dataset.csv' o join 'FIX/olist_customers_dataset.csv' c
               using (customer_id) group by 1 having count(*) > 1)""")
        >= 1
    )
    assert (
        q("""select count(*) from 'FIX/olist_orders_dataset.csv'
               where order_delivered_customer_date::timestamp
                     > order_estimated_delivery_date::timestamp""")
        >= 1
    )
    assert (
        q("select count(*) from 'FIX/olist_orders_dataset.csv' where order_status = 'canceled'")
        >= 1
    )
    assert (
        q("select count(*) from 'FIX/olist_orders_dataset.csv' where order_status = 'shipped'") >= 1
    )
    assert (
        q("""select count(*) from 'FIX/olist_orders_dataset.csv'
               where order_status = 'delivered' and order_delivered_customer_date is null""")
        >= 1
    )
    assert (
        q("""select count(*) from 'FIX/olist_orders_dataset.csv' o
               where not exists (select 1 from 'FIX/olist_order_reviews_dataset.csv' r
                                 where r.order_id = o.order_id)""")
        >= 1
    )
    assert (
        q("""select count(*) from (select order_id from 'FIX/olist_order_reviews_dataset.csv'
               group by 1 having min(review_score) <> max(review_score))""")
        >= 1
    )
    assert (
        q("""select count(*) from (select order_id from 'FIX/olist_order_items_dataset.csv'
               group by 1 having count(distinct seller_id) > 1)""")
        >= 1
    )
    assert (
        q("""select count(*) from 'FIX/olist_orders_dataset.csv' o
               where not exists (select 1 from 'FIX/olist_order_items_dataset.csv' i
                                 where i.order_id = o.order_id)""")
        >= 1
    )


def test_fixture_has_orders_outside_analysis_period():
    assert (
        q(
            "select count(*) from 'FIX/olist_orders_dataset.csv' where order_purchase_timestamp >= '2018-09-01'"
        )
        >= 1
    )


def test_referential_integrity():
    assert (
        q("""select count(*) from 'FIX/olist_order_items_dataset.csv' i
               where i.order_id not in (select order_id from 'FIX/olist_orders_dataset.csv')""")
        == 0
    )
    assert (
        q("""select count(*) from 'FIX/olist_orders_dataset.csv' o
               where o.customer_id not in
                     (select customer_id from 'FIX/olist_customers_dataset.csv')""")
        == 0
    )
    assert (
        q("""select count(*) from 'FIX/olist_order_items_dataset.csv' i
               where i.product_id not in (select product_id from 'FIX/olist_products_dataset.csv')
                  or i.seller_id not in (select seller_id from 'FIX/olist_sellers_dataset.csv')""")
        == 0
    )
