import duckdb

from scripts.export_marts import EXPORT_TABLES, SITE_TABLES, build_site_data, export
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
    assert sorted(p.stem for p in out.glob("*.parquet")) == sorted(SITE_TABLES)


def test_site_gmv_reconciles_with_marts(built_db, tmp_path):
    out = site_data(built_db, tmp_path)
    ((site_monthly,),) = duckdb.sql(
        f"select sum(gmv) from '{out / 'monthly_kpis.parquet'}'"
    ).fetchall()
    ((site_by_cat,),) = duckdb.sql(
        f"select sum(gmv) from '{out / 'gmv_by_month_category_state.parquet'}'"
    ).fetchall()
    ((mart,),) = query(built_db, "select sum(gmv) from mart_monthly_kpis")
    assert float(site_monthly) == float(mart)
    assert round(float(site_by_cat), 2) == round(float(mart), 2)


def test_site_data_has_no_customer_or_order_ids(built_db, tmp_path):
    out = site_data(built_db, tmp_path)
    for path in out.glob("*.parquet"):
        columns = {
            c for (c,) in duckdb.sql(f"select name from parquet_schema('{path}')").fetchall()
        }
        assert not columns & {"customer_unique_id", "customer_id", "order_id"}, path.name


def test_site_data_rebuild_is_idempotent(built_db, tmp_path):
    out = site_data(built_db, tmp_path)
    build_site_data(tmp_path / "marts", out, min_seller_orders=1)
    assert sorted(p.stem for p in out.glob("*.parquet")) == sorted(SITE_TABLES)


def test_site_data_uses_browser_friendly_number_types(built_db, tmp_path):
    # BIGINT arrives in the browser as BigInt and DECIMAL as an object; charts need plain numbers
    out = site_data(built_db, tmp_path)
    for path in out.glob("*.parquet"):
        types = {
            t
            for (t,) in duckdb.sql(
                f"select column_type from (describe select * from '{path}')"
            ).fetchall()
        }
        assert not {t for t in types if t.startswith(("BIGINT", "HUGEINT", "DECIMAL"))}, (
            path.name,
            types,
        )


def columns(path):
    return [
        c
        for (c,) in duckdb.sql(
            f"select column_name from (describe select * from '{path}')"
        ).fetchall()
    ]


def test_category_aggregate_has_only_additive_measures(built_db, tmp_path):
    # order counts per category double-count orders that span categories
    out = site_data(built_db, tmp_path)
    assert "orders" not in columns(out / "gmv_by_month_category_state.parquet")


def test_seller_and_state_delivery_cover_the_analysis_period_only(built_db, tmp_path):
    out = site_data(built_db, tmp_path)
    assert columns(out / "sellers_delivery.parquet") == [
        "seller",
        "seller_state",
        "delivered_orders",
        "late_orders",
        "late_rate",
        "avg_days_late",
        "avg_review_score",
    ]
    assert "late_delay_days_sum" in columns(out / "delivery_by_state.parquet")
    ((site_late,),) = duckdb.sql(
        f"select sum(late_orders) from '{out / 'delivery_by_state.parquet'}'"
    ).fetchall()
    ((mart_late,),) = query(
        built_db,
        "select count(*) from mart_delivery_performance where is_analysis_period and is_late",
    )
    assert site_late == mart_late


def test_overview_numbers_match_the_marts(built_db, tmp_path):
    import json

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
