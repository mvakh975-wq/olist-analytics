import json

import duckdb

from scripts.export_marts import (
    DATALENS_CSV,
    EXPORT_TABLES,
    SITE_TABLES,
    build_datalens,
    build_site_data,
    export,
)
from tests.conftest import query


def test_export_writes_delay_statistics(built_db, tmp_path):
    out = tmp_path / "marts"
    export(built_db, out)
    effect = duckdb.sql(
        f"select comparison, n_late from '{out / 'stats_delay_effect.parquet'}'"
    ).fetchall()
    assert [c for c, _ in effect] == ["late vs on time", "15+ days late vs on time"]
    ((late,),) = query(
        built_db,
        "select count(*) from mart_delivery_performance where is_analysis_period and is_late and review_score is not null",
    )
    assert effect[0][1] == late


def test_export_matches_marts(built_db, tmp_path):
    out = tmp_path / "marts"
    paths = export(built_db, out)
    assert sorted(p.stem for p in paths) == sorted(
        [*EXPORT_TABLES, "stats_delay_effect", "stats_delay_by_state"]
    )
    for path in paths:
        if path.stem.startswith("stats_"):
            continue
        ((exported,),) = duckdb.sql(f"select count(*) from '{path}'").fetchall()
        ((source,),) = query(built_db, f"select count(*) from {path.stem}")
        assert exported == source, path.stem


def site_data(built_db, tmp_path):
    marts = tmp_path / "marts"
    export(built_db, marts)
    out = tmp_path / "site"
    # the fixture is small, so every seller counts
    build_site_data(marts, out, min_seller_orders=1)
    return out


def test_site_data_files(built_db, tmp_path):
    out = site_data(built_db, tmp_path)
    assert sorted(p.stem for p in out.glob("*.json") if p.stem != "overview") == sorted(SITE_TABLES)
    assert not list(out.glob("*.parquet")), "pages read JSON; no parquet should be shipped"


def test_site_data_has_no_customer_or_order_ids(built_db, tmp_path):
    out = site_data(built_db, tmp_path)
    for path in out.glob("*.json"):
        rows = json.loads(path.read_text())
        keys = set(rows[0]) if isinstance(rows, list) and rows else set()
        assert not keys & {"customer_unique_id", "customer_id", "order_id"}, path.name


def test_site_data_rebuild_is_idempotent(built_db, tmp_path):
    out = site_data(built_db, tmp_path)
    build_site_data(tmp_path / "marts", out, min_seller_orders=1)
    assert sorted(p.stem for p in out.glob("*.json") if p.stem != "overview") == sorted(SITE_TABLES)


def test_site_data_uses_browser_friendly_number_types(built_db, tmp_path):
    # pages use the values as they come: plain numbers, booleans, ISO dates, null for "no value"
    out = site_data(built_db, tmp_path)
    for name in SITE_TABLES:
        rows = json.loads((out / f"{name}.json").read_text())
        assert isinstance(rows, list), name
        for row in rows:
            for key, value in row.items():
                assert value is None or isinstance(value, int | float | bool | str), (name, key)
    cohorts = json.loads((out / "cohort_retention.json").read_text())
    assert cohorts and isinstance(cohorts[0]["retention"], float)
    assert isinstance(cohorts[0]["is_analysis_period"], bool)
    assert len(cohorts[0]["cohort_month"]) == 10  # YYYY-MM-DD


def columns(path):
    return list(json.loads(path.read_text())[0])


def test_seller_and_state_delivery_cover_the_analysis_period_only(built_db, tmp_path):
    out = site_data(built_db, tmp_path)
    assert columns(out / "sellers_delivery.json") == [
        "seller",
        "seller_state",
        "delivered_orders",
        "late_orders",
        "late_rate",
        "avg_days_late",
        "avg_review_score",
    ]
    assert "late_delay_days_sum" in columns(out / "delivery_by_state.json")
    ((site_late,),) = duckdb.sql(
        f"select sum(late_orders) from read_json('{out / 'delivery_by_state.json'}')"
    ).fetchall()
    ((mart_late,),) = query(
        built_db,
        "select count(*) from mart_delivery_performance where is_analysis_period and is_late",
    )
    assert site_late == mart_late


def test_overview_numbers_match_the_marts(built_db, tmp_path):
    out = site_data(built_db, tmp_path)
    o = json.loads((out / "overview.json").read_text())
    ((gmv_2018,),) = query(
        built_db,
        "select sum(gmv) from mart_monthly_kpis where month between '2018-01-01' and '2018-08-01'",
    )
    assert round(o["gmv_2018"], 2) == round(float(gmv_2018), 2)
    ((people, repeaters),) = query(
        built_db, "select count(*), count(*) filter (where n_orders > 1) from dim_customers"
    )
    assert o["customers"] == people
    assert o["repeat_share"] == repeaters / people
    ((late_rate,),) = query(
        built_db,
        "select avg(is_late::int) from mart_delivery_performance where is_analysis_period",
    )
    assert abs(o["late_rate"] - late_rate) < 1e-12
    expected = {
        "gmv_2017",
        "orders_2018",
        "orders_2017",
        "aov_2018",
        "aov_2017",
        "aov",
        "black_friday_gmv",
        "late_rate_2017",
        "late_rate_2018",
        "month1_retention",
        "low_score_on_time",
        "low_score_late_4_7",
        "late_sp",
        "late_rj",
        "late_ma",
        "late_nov_2017",
        "late_mar_2018",
        "high_value_customer_share",
        "high_value_revenue_share",
        "effect",
        "states_tested",
        "state_gap_min",
        "state_gap_max",
        "worst_sellers",
        "worst_sellers_late",
        "other_sellers_late",
        "worst_sellers_share_of_late",
    }
    assert expected <= o.keys()
    assert all(
        v is not None
        for k, v in o.items()
        if k not in {"late_sp", "late_rj", "late_ma", "state_gap_min", "state_gap_max"}
    )


def test_growth_page_files_are_small_csvs_that_reconcile(built_db, tmp_path):
    # the Growth page filters these in the browser without loading DuckDB
    out = site_data(built_db, tmp_path)
    gmv = duckdb.sql(f"select * from read_csv('{out / 'growth_gmv.csv'}')")
    assert gmv.columns == ["month", "category", "state", "gmv"]
    ((site_total,),) = duckdb.sql(
        f"select sum(gmv) from read_csv('{out / 'growth_gmv.csv'}')"
    ).fetchall()
    ((mart_total,),) = query(
        built_db, "select sum(gmv) from mart_monthly_kpis where is_analysis_period"
    )
    assert abs(site_total - float(mart_total)) < 0.01
    kpis = duckdb.sql(f"select * from read_csv('{out / 'growth_kpis.csv'}')")
    assert kpis.columns == ["month", "avg_order_value", "freight_share"]
    ((months,),) = query(
        built_db, "select count(*) from mart_monthly_kpis where is_analysis_period"
    )
    assert len(kpis.fetchall()) == months


def datalens(built_db, tmp_path):
    marts = tmp_path / "marts"
    export(built_db, marts)
    return {p.stem: p for p in build_datalens(marts, tmp_path / "datalens")}


def test_datalens_files_have_no_ids(built_db, tmp_path):
    files = datalens(built_db, tmp_path)
    assert sorted(files) == sorted(DATALENS_CSV)
    for path in files.values():
        header = path.read_text().splitlines()[0].lower()
        assert "_id" not in header and " id" not in header, path.name


def test_datalens_orders_match_monthly_kpis(built_db, tmp_path):
    orders = datalens(built_db, tmp_path)["orders"]
    ((n, gmv, late_rate),) = duckdb.sql(
        f"""select count(*), sum("GMV, BRL"), avg("Опоздал") from '{orders}'"""
    ).fetchall()
    ((kpi_orders, kpi_gmv),) = query(
        built_db,
        "select sum(orders), sum(gmv) from mart_monthly_kpis where is_analysis_period",
    )
    ((delivered_late_rate,),) = query(
        built_db,
        "select avg(is_late::int) from mart_delivery_performance where is_analysis_period",
    )
    assert n == kpi_orders
    assert round(gmv, 2) == round(float(kpi_gmv), 2)
    assert late_rate == delivered_late_rate


def test_datalens_labels_every_segment_and_delay_bucket(built_db, tmp_path):
    files = datalens(built_db, tmp_path)
    ((unlabelled_buckets,),) = duckdb.sql(
        f"""select count(*) from '{files["orders"]}'
            where "Доставлен" = 1 and "Срок доставки" is null"""
    ).fetchall()
    ((unlabelled_segments,),) = duckdb.sql(
        f"""select count(*) from '{files["rfm"]}' where "Сегмент" is null"""
    ).fetchall()
    assert unlabelled_buckets == 0
    assert unlabelled_segments == 0
