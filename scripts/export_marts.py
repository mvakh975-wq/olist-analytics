"""Export dbt marts to parquet (committed) and build the small aggregates the dashboard reads.

Usage: python -m scripts.export_marts export|site-data
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb

from scripts.stats import write_delay_stats

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
               sum(delivery_days) as delivery_days_sum,
               sum(delay_days) filter (where is_late) as late_delay_days_sum
        from '{m}/mart_delivery_performance.parquet'
        where is_analysis_period
        group by all""",
    # delivered orders in the analysis period, attributed to the main seller
    "sellers_delivery": """
        select left(d.main_seller_id, 8) as seller,
               any_value(s.seller_state) as seller_state,
               count(*) as delivered_orders,
               count(*) filter (where d.is_late) as late_orders,
               count(*) filter (where d.is_late) / count(*) as late_rate,
               avg(d.delay_days) filter (where d.is_late) as avg_days_late,
               avg(d.review_score) as avg_review_score
        from '{m}/mart_delivery_performance.parquet' as d
        left join '{m}/dim_sellers.parquet' as s on d.main_seller_id = s.seller_id
        where d.is_analysis_period
        group by d.main_seller_id
        having count(*) >= {min_seller_orders}""",
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
    # the dashboard's statistics come from the same marts, so they are rebuilt here too
    return paths + write_delay_stats(db, out_dir)


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


# every number on the overview page, computed once at build time so the page needs no database
OVERVIEW = """
with kpis as (select * from '{m}/mart_monthly_kpis.parquet'),
     deliveries as (select * from '{m}/mart_delivery_performance.parquet' where is_analysis_period),
     customers as (select * from '{m}/dim_customers.parquet'),
     cohorts as (select * from '{m}/mart_cohort_retention.parquet'),
     rfm as (select * from '{m}/mart_rfm.parquet'),
     by_state as (select * from '{m}/stats_delay_by_state.parquet'),
     sellers as (select *, ntile(10) over (order by late_rate desc, seller) as decile
                 from '{site}/sellers_delivery.parquet')
select
    (select sum(gmv) from kpis where month between '2018-01-01' and '2018-08-01') as gmv_2018,
    (select sum(gmv) from kpis where month between '2017-01-01' and '2017-08-01') as gmv_2017,
    (select sum(orders) from kpis where month between '2018-01-01' and '2018-08-01') as orders_2018,
    (select sum(orders) from kpis where month between '2017-01-01' and '2017-08-01') as orders_2017,
    (select sum(gmv) / sum(orders) from kpis where month between '2018-01-01' and '2018-08-01') as aov_2018,
    (select sum(gmv) / sum(orders) from kpis where month between '2017-01-01' and '2017-08-01') as aov_2017,
    (select sum(gmv) / sum(orders) from kpis where is_analysis_period) as aov,
    (select max(gmv) from kpis where month = '2017-11-01') as black_friday_gmv,
    (select avg(is_late::int) from deliveries) as late_rate,
    (select avg(is_late::int) from deliveries where purchase_month between '2017-01-01' and '2017-08-01') as late_rate_2017,
    (select avg(is_late::int) from deliveries where purchase_month between '2018-01-01' and '2018-08-01') as late_rate_2018,
    (select count(*) from customers) as customers,
    (select count(*) filter (where n_orders > 1) / count(*) from customers) as repeat_share,
    (select sum(active_customers) / sum(cohort_size) from cohorts
     where is_analysis_period and months_since_first = 1) as month1_retention,
    (select avg(is_low_score::int) from deliveries where delay_bucket_order = 1) as low_score_on_time,
    (select avg(is_low_score::int) from deliveries where delay_bucket_order = 3) as low_score_late_4_7,
    (select avg(is_late::int) from deliveries where customer_state = 'SP') as late_sp,
    (select avg(is_late::int) from deliveries where customer_state = 'RJ') as late_rj,
    (select avg(is_late::int) from deliveries where customer_state = 'MA') as late_ma,
    (select avg(is_late::int) from deliveries where purchase_month = '2017-11-01') as late_nov_2017,
    (select avg(is_late::int) from deliveries where purchase_month = '2018-03-01') as late_mar_2018,
    (select count(*) filter (where segment in ('Promising high-value', 'At risk high-value')) / count(*)
     from rfm) as high_value_customer_share,
    (select sum(monetary) filter (where segment in ('Promising high-value', 'At risk high-value'))
            / sum(monetary) from rfm) as high_value_revenue_share,
    (select count(*) from by_state) as states_tested,
    (select max(diff) from by_state) as state_gap_min,
    (select min(diff) from by_state) as state_gap_max,
    (select count(*) from sellers where decile = 1) as worst_sellers,
    (select sum(late_orders) / sum(delivered_orders) from sellers where decile = 1) as worst_sellers_late,
    (select sum(late_orders) / sum(delivered_orders) from sellers where decile > 1) as other_sellers_late,
    (select sum(late_orders) filter (where decile = 1) from sellers)
        / (select count(*) from deliveries where is_late) as worst_sellers_share_of_late
"""

# the Growth page filters these small files in the browser instead of loading DuckDB
GROWTH_CSV = {
    "growth_gmv": """
        select strftime(purchase_month, '%Y-%m') as month, category, customer_state as state,
               round(sum(price + freight_value), 2)::double as gmv
        from '{m}/fct_order_items.parquet'
        where is_valid_order and is_analysis_period
        group by all""",
    "growth_kpis": """
        select strftime(month, '%Y-%m') as month,
               round(avg_order_value, 4)::double as avg_order_value,
               round(freight_share, 6)::double as freight_share
        from '{m}/mart_monthly_kpis.parquet'
        where is_analysis_period""",
}

EFFECT = """
select mean_on_time, mean_late, diff, ci_low, ci_high
from '{m}/stats_delay_effect.parquet' where comparison = 'late vs on time'
"""


def _plain(value):
    """JSON-friendly Python number (DuckDB returns Decimal for sums of decimals)."""
    if value is None or isinstance(value, int | float | str):
        return value
    return float(value)


def build_overview(marts_dir: Path, site_dir: Path) -> dict:
    con = duckdb.connect()
    rel = con.sql(OVERVIEW.format(m=marts_dir, site=site_dir))
    overview = {k: _plain(v) for k, v in zip(rel.columns, rel.fetchone(), strict=True)}
    effect = con.sql(EFFECT.format(m=marts_dir))
    overview["effect"] = {
        k: _plain(v) for k, v in zip(effect.columns, effect.fetchone(), strict=True)
    }
    return overview


def build_site_data(marts_dir: Path, out_dir: Path, min_seller_orders: int = 50) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    for name, sql in SITE_TABLES.items():
        path = out_dir / f"{name}.parquet"
        query = _browser_types(con, sql.format(m=marts_dir, min_seller_orders=min_seller_orders))
        con.execute(f"copy ({query} order by all) to '{path}' (format parquet, compression zstd)")
    for name, sql in GROWTH_CSV.items():
        con.execute(
            f"copy ({sql.format(m=marts_dir)} order by all) to '{out_dir / name}.csv' (header)"
        )
    overview = build_overview(marts_dir, out_dir)
    (out_dir / "overview.json").write_text(json.dumps(overview, indent=2) + "\n")


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
