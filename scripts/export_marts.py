"""Export dbt marts to parquet (committed) and build the DuckDB file the dashboard reads.

Usage: python -m scripts.export_marts export|site-db
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
DB = Path("olist.duckdb")
MARTS_DIR = Path("data/marts")
SITE_DB = Path("site/sources/olist/olist.duckdb")


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


def build_site_db(marts_dir: Path, db_path: Path) -> None:
    """One table per parquet file in marts_dir; the file is rebuilt from scratch."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.unlink(missing_ok=True)
    with duckdb.connect(str(db_path)) as con:
        for path in sorted(marts_dir.glob("*.parquet")):
            con.execute(f"create table {path.stem} as select * from read_parquet('{path}')")


def main(argv: list[str]) -> int:
    if argv == ["export"]:
        for path in export(DB, MARTS_DIR):
            print(path)
    elif argv == ["site-db"]:
        build_site_db(MARTS_DIR, SITE_DB)
        print(SITE_DB)
    else:
        print("usage: python -m scripts.export_marts export|site-db", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
