"""Export dbt marts to parquet (committed) and build the small aggregates the dashboard reads.

Usage: python -m scripts.export_marts export|site-data
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

EXPORT_TABLES = (
    "fct_orders",
    "fct_order_items",
    "dim_customers",
    "dim_sellers",
    "mart_monthly_kpis",
    "mart_cohort_retention",
    "mart_rfm",
    "mart_delivery_performance",
)

# Aggregates for the dashboard, built from the committed parquet marts ({m} = marts directory).
# Measures are stored as sums and counts so pages can re-aggregate them after filtering.
SITE_TABLES = {
    "monthly_kpis": "select * from '{m}/mart_monthly_kpis.parquet'",
    "gmv_by_month_category_state": """
        select purchase_month as month, category, customer_state, is_analysis_period,
               sum(price + freight_value) as gmv,
               count(distinct order_id) as orders
        from '{m}/fct_order_items.parquet'
        where is_valid_order
        group by all""",
    "cohort_retention": "select * from '{m}/mart_cohort_retention.parquet'",
    "orders_per_customer": """
        select n_orders, count(*) as customers
        from '{m}/dim_customers.parquet' group by all""",
    "rfm_segments": """
        select segment,
               count(*) as customers,
               sum(monetary) as revenue,
               median(recency_days) as median_recency_days
        from '{m}/mart_rfm.parquet' group by all""",
    "delivery_by_bucket_state": """
        select delay_bucket, delay_bucket_order, customer_state,
               count(*) as orders,
               count(review_score) as reviewed,
               sum(review_score) as score_sum,
               count(*) filter (where is_low_score) as low_score_orders
        from '{m}/mart_delivery_performance.parquet'
        where is_analysis_period
        group by all""",
    "delivery_by_month": """
        select purchase_month as month,
               count(*) as orders,
               count(*) filter (where is_late) as late_orders
        from '{m}/mart_delivery_performance.parquet'
        where is_analysis_period
        group by all""",
    "delivery_by_state": """
        select customer_state,
               count(*) as orders,
               count(*) filter (where is_late) as late_orders,
               sum(delivery_days) as delivery_days_sum
        from '{m}/mart_delivery_performance.parquet'
        where is_analysis_period
        group by all""",
    "sellers_delivery": """
        select left(seller_id, 8) as seller, seller_state, n_orders, late_rate, avg_review_score
        from '{m}/dim_sellers.parquet'
        where n_orders >= 50""",
    "stats_delay_effect": "select * from '{m}/stats_delay_effect.parquet'",
    "stats_delay_by_state": "select * from '{m}/stats_delay_by_state.parquet'",
}

DB = Path("olist.duckdb")
MARTS_DIR = Path("data/marts")
SITE_DATA_DIR = Path("site/src/data")


def export(db: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    with duckdb.connect(str(db), read_only=True) as con:
        for table in EXPORT_TABLES:
            path = out_dir / f"{table}.parquet"
            con.execute(
                f"copy (select * from {table} order by all) to '{path}' "
                "(format parquet, compression zstd)"
            )
            paths.append(path)
    return paths


def _browser_types(con: duckdb.DuckDBPyConnection, sql: str) -> str:
    """Wrap a query so BIGINT/HUGEINT become INTEGER and DECIMAL becomes DOUBLE.

    DuckDB-WASM hands BIGINT to JavaScript as BigInt and DECIMAL as an object,
    which charts cannot plot; every value here fits in those types.
    """
    columns = []
    for name, column_type, *_ in con.sql(f"describe {sql}").fetchall():
        if column_type.startswith(("BIGINT", "HUGEINT")):
            columns.append(f'"{name}"::integer as "{name}"')
        elif column_type.startswith("DECIMAL"):
            columns.append(f'"{name}"::double as "{name}"')
        else:
            columns.append(f'"{name}"')
    return f"select {', '.join(columns)} from ({sql})"


def build_site_data(marts_dir: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    for name, sql in SITE_TABLES.items():
        path = out_dir / f"{name}.parquet"
        query = _browser_types(con, sql.format(m=marts_dir))
        con.execute(f"copy ({query} order by all) to '{path}' (format parquet, compression zstd)")


def main(argv: list[str]) -> int:
    if argv == ["export"]:
        for path in export(DB, MARTS_DIR):
            print(path)
    elif argv == ["site-data"]:
        build_site_data(MARTS_DIR, SITE_DATA_DIR)
        print(SITE_DATA_DIR)
    else:
        print("usage: python -m scripts.export_marts export|site-data", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
