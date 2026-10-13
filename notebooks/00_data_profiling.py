# %% [markdown]
# # 00 · Data profiling
# Missing values, duplicates, column types and date ranges for every raw table,
# before any modelling. Decisions taken from these numbers are recorded in
# `docs/data_quality.md`.

# %%
from pathlib import Path

import duckdb
import pandas as pd

pd.set_option("display.max_rows", 200)
RAW = Path("../data/raw")
con = duckdb.connect()
tables = {p.stem: p for p in sorted(RAW.glob("*.csv"))}


def sql(query: str) -> pd.DataFrame:
    return con.sql(query.replace("RAW", str(RAW))).df()


# %% [markdown]
# ## Columns: types, nulls, distinct values

# %%
def profile(name: str, path: Path) -> pd.DataFrame:
    rel = con.read_csv(str(path), header=True)
    df = rel.df()
    return pd.DataFrame(
        {
            "table": name,
            "column": df.columns,
            "dtype": [str(t) for t in rel.dtypes],
            "rows": len(df),
            "nulls": df.isna().sum().values,
            "null_pct": (df.isna().mean() * 100).round(2).values,
            "distinct": df.nunique().values,
        }
    )


summary = pd.concat([profile(n, p) for n, p in tables.items()], ignore_index=True)
summary

# %% [markdown]
# ## Full-row duplicates

# %%
pd.Series(
    {n: int(con.read_csv(str(p), header=True).df().duplicated().sum()) for n, p in tables.items()},
    name="duplicate_rows",
)

# %% [markdown]
# ## Keys and customer identity

# %%
checks = {
    "orders: duplicate order_id": "select count(*) - count(distinct order_id) from 'RAW/olist_orders_dataset.csv'",
    "reviews: duplicate review_id": "select count(*) - count(distinct review_id) from 'RAW/olist_order_reviews_dataset.csv'",
    "reviews: duplicate (review_id, order_id)": "select count(*) - count(distinct (review_id, order_id)) from 'RAW/olist_order_reviews_dataset.csv'",
    "orders with >1 review": "select count(*) from (select order_id from 'RAW/olist_order_reviews_dataset.csv' group by 1 having count(*) > 1)",
    "orders without a review": "select count(*) from 'RAW/olist_orders_dataset.csv' o where not exists (select 1 from 'RAW/olist_order_reviews_dataset.csv' r where r.order_id = o.order_id)",
    "customers: duplicate customer_id": "select count(*) - count(distinct customer_id) from 'RAW/olist_customers_dataset.csv'",
    "customer_id values": "select count(distinct customer_id) from 'RAW/olist_customers_dataset.csv'",
    "customer_unique_id values": "select count(distinct customer_unique_id) from 'RAW/olist_customers_dataset.csv'",
    "unique customers with >1 order": """select count(*) from (
          select c.customer_unique_id from 'RAW/olist_orders_dataset.csv' o
          join 'RAW/olist_customers_dataset.csv' c using (customer_id)
          group by 1 having count(*) > 1)""",
    "orders with items from >1 seller": "select count(*) from (select order_id from 'RAW/olist_order_items_dataset.csv' group by 1 having count(distinct seller_id) > 1)",
    "orders without items": "select count(*) from 'RAW/olist_orders_dataset.csv' o where not exists (select 1 from 'RAW/olist_order_items_dataset.csv' i where i.order_id = o.order_id)",
    "orders without payments": "select count(*) from 'RAW/olist_orders_dataset.csv' o where not exists (select 1 from 'RAW/olist_order_payments_dataset.csv' p where p.order_id = o.order_id)",
}
pd.Series({k: sql(q).iat[0, 0] for k, q in checks.items()}, name="value")

# %% [markdown]
# ## Orders per month (to choose the analysis period) and status mix

# %%
sql("""
select date_trunc('month', order_purchase_timestamp::timestamp)::date as month, count(*) as orders
from 'RAW/olist_orders_dataset.csv' group by 1 order by 1
""")

# %%
sql("select order_status, count(*) as orders from 'RAW/olist_orders_dataset.csv' group by 1 order by 2 desc")

# %% [markdown]
# ## Delivery dates

# %%
sql("""
select
  count(*) filter (where order_status = 'delivered') as delivered,
  count(*) filter (where order_status = 'delivered' and order_delivered_customer_date is null) as delivered_no_date,
  count(*) filter (where order_status <> 'delivered' and order_delivered_customer_date is not null) as not_delivered_with_date,
  count(*) filter (where order_delivered_customer_date::timestamp < order_purchase_timestamp::timestamp) as delivered_before_purchase,
  count(*) filter (where order_estimated_delivery_date is null) as no_estimate
from 'RAW/olist_orders_dataset.csv'
""")

# %% [markdown]
# ## Payments vs items + freight

# %%
sql("""
with i as (select order_id, sum(price + freight_value) as items from 'RAW/olist_order_items_dataset.csv' group by 1),
     p as (select order_id, sum(payment_value) as paid from 'RAW/olist_order_payments_dataset.csv' group by 1)
select count(*) as orders,
       count(*) filter (where abs(items - paid) > 1) as mismatch_gt_1brl,
       round(sum(abs(items - paid)) filter (where abs(items - paid) > 1), 2) as mismatch_brl_total
from i join p using (order_id)
""")

# %%
sql("select payment_type, count(*) as payments from 'RAW/olist_order_payments_dataset.csv' group by 1 order by 2 desc")

# %% [markdown]
# ## Product categories

# %%
sql("""
select count(*) filter (where product_category_name is null) as products_without_category
from 'RAW/olist_products_dataset.csv'
""")

# %%
sql("""
select distinct p.product_category_name
from 'RAW/olist_products_dataset.csv' p
left join 'RAW/product_category_name_translation.csv' t using (product_category_name)
where t.product_category_name_english is null
""")

# %% [markdown]
# ## Value ranges

# %%
sql("""
select min(price) as min_price, max(price) as max_price,
       min(freight_value) as min_freight, max(freight_value) as max_freight,
       count(*) filter (where price <= 0) as non_positive_price
from 'RAW/olist_order_items_dataset.csv'
""")

# %%
sql("select review_score, count(*) as reviews from 'RAW/olist_order_reviews_dataset.csv' group by 1 order by 1")
