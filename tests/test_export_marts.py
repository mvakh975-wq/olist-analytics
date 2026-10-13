import duckdb

from scripts.export_marts import EXPORT_TABLES, build_site_db, export
from tests.conftest import query


def test_export_and_site_db_roundtrip(built_db, tmp_path):
    out = tmp_path / "marts"
    paths = export(built_db, out)
    assert sorted(p.stem for p in paths) == sorted(EXPORT_TABLES)
    site_db = tmp_path / "site.duckdb"
    build_site_db(out, site_db)
    with duckdb.connect(str(site_db), read_only=True) as con:
        for table in EXPORT_TABLES:
            ((exported,),) = con.sql(f"select count(*) from {table}").fetchall()
            ((source,),) = query(built_db, f"select count(*) from {table}")
            assert exported == source, table


def test_site_db_includes_extra_parquet_and_rebuilds(built_db, tmp_path):
    out = tmp_path / "marts"
    export(built_db, out)
    duckdb.sql(f"copy (select 1 as x) to '{out / 'stats_example.parquet'}' (format parquet)")
    db = tmp_path / "site.duckdb"
    build_site_db(out, db)
    build_site_db(out, db)  # a second run must not fail on existing tables
    with duckdb.connect(str(db), read_only=True) as con:
        assert con.sql("select x from stats_example").fetchall() == [(1,)]
