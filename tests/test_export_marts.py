import duckdb

from scripts.export_marts import EXPORT_TABLES, SITE_TABLES, build_site_data, export
from tests.conftest import query


def test_export_matches_marts(built_db, tmp_path):
    out = tmp_path / "marts"
    paths = export(built_db, out)
    assert sorted(p.stem for p in paths) == sorted(EXPORT_TABLES)
    for path in paths:
        ((exported,),) = duckdb.sql(f"select count(*) from '{path}'").fetchall()
        ((source,),) = query(built_db, f"select count(*) from {path.stem}")
        assert exported == source, path.stem


def site_data(built_db, tmp_path):
    marts = tmp_path / "marts"
    export(built_db, marts)
    # the notebooks add these two; the site expects them
    duckdb.sql(
        f"copy (select 'late vs on time' as comparison, -2.0 as diff) to '{marts / 'stats_delay_effect.parquet'}' (format parquet)"
    )
    duckdb.sql(
        f"copy (select 'SP' as customer_state, -1.8 as diff) to '{marts / 'stats_delay_by_state.parquet'}' (format parquet)"
    )
    out = tmp_path / "site"
    build_site_data(marts, out)
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
    build_site_data(tmp_path / "marts", out)
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
