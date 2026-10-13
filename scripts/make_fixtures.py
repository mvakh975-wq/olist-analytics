"""Cut a small, referentially consistent sample of real Olist rows for CI tests.

Usage: python -m scripts.make_fixtures data/raw tests/fixtures/raw
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

from scripts.download import RAW_FILES

TABLES = {
    "orders": "olist_orders_dataset",
    "customers": "olist_customers_dataset",
    "items": "olist_order_items_dataset",
    "payments": "olist_order_payments_dataset",
    "reviews": "olist_order_reviews_dataset",
    "products": "olist_products_dataset",
    "sellers": "olist_sellers_dataset",
    "geo": "olist_geolocation_dataset",
    "translation": "product_category_name_translation",
}

# each query returns order_ids that must be in the sample so edge cases are covered
MUST_HAVE = {
    "repeat_customer": """
        select o.order_id from orders o join customers c using (customer_id)
        where c.customer_unique_id = (
            select c2.customer_unique_id from orders o2 join customers c2 using (customer_id)
            where o2.order_status = 'delivered'
            group by 1 having count(*) = 2 order by 1 limit 1)""",
    "late": """select order_id from orders
               where order_delivered_customer_date::timestamp
                     > order_estimated_delivery_date::timestamp + interval 10 day
               order by order_id limit 2""",
    "canceled": "select order_id from orders where order_status = 'canceled' order by 1 limit 1",
    "shipped": "select order_id from orders where order_status = 'shipped' order by 1 limit 1",
    "delivered_no_date": """select order_id from orders where order_status = 'delivered'
                            and order_delivered_customer_date is null order by 1 limit 1""",
    "conflicting_reviews": """select order_id from reviews group by 1
                              having min(review_score) <> max(review_score) order by 1 limit 1""",
    "no_review": """select order_id from orders o where order_status = 'delivered'
                    and not exists (select 1 from reviews r where r.order_id = o.order_id)
                    order by 1 limit 1""",
    "two_sellers": """select order_id from items group by 1 having count(distinct seller_id) > 1
                      order by 1 limit 1""",
    "after_period": """select order_id from orders
                       where order_purchase_timestamp::timestamp >= '2018-09-01'
                       order by 1 limit 1""",
    "no_items": """select order_id from orders o where order_status = 'unavailable'
                   and not exists (select 1 from items i where i.order_id = o.order_id)
                   order by 1 limit 1""",
}


def build_fixtures(raw_dir: Path, out_dir: Path, n_orders: int = 80, seed: int = 42) -> None:
    con = duckdb.connect()
    for view, stem in TABLES.items():
        con.execute(
            f"create view {view} as select * from read_csv('{raw_dir / stem}.csv', "
            "header = true, all_varchar = true)"
        )
    con.execute("create table pick (order_id varchar)")
    for sql in MUST_HAVE.values():
        con.execute(f"insert into pick {sql}")
    con.execute(f"select setseed({seed / 100})")
    con.execute(
        "insert into pick select order_id from orders where order_status = 'delivered' "
        f"and order_id not in (select order_id from pick) order by random() limit {n_orders}"
    )
    picked = "(select order_id from pick)"
    selects = {
        "orders": f"select * from orders where order_id in {picked}",
        "items": f"select * from items where order_id in {picked}",
        "payments": f"select * from payments where order_id in {picked}",
        "reviews": f"select * from reviews where order_id in {picked}",
        "customers": f"""select * from customers where customer_id in
                         (select customer_id from orders where order_id in {picked})""",
        "products": f"""select * from products where product_id in
                        (select product_id from items where order_id in {picked})""",
        "sellers": f"""select * from sellers where seller_id in
                       (select seller_id from items where order_id in {picked})""",
        "geo": "select * from (select * from geo order by all limit 5)",
        "translation": "select * from translation",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    for view, sql in selects.items():
        con.execute(f"copy ({sql} order by all) to '{out_dir / TABLES[view]}.csv' (header)")
    assert sorted(p.name for p in out_dir.glob("*.csv")) == sorted(RAW_FILES)


if __name__ == "__main__":
    build_fixtures(Path(sys.argv[1]), Path(sys.argv[2]))
