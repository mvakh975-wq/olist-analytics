import os
import subprocess
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "raw"


def raw(name: str) -> str:
    """A raw fixture CSV as a DuckDB table expression, every column as text."""
    return f"read_csv('{FIXTURES}/{name}.csv', header = true, all_varchar = true)"


@pytest.fixture(scope="session")
def built_db(tmp_path_factory) -> Path:
    db = tmp_path_factory.mktemp("dbt") / "ci.duckdb"
    result = subprocess.run(
        [
            "dbt",
            "build",
            "--project-dir",
            "dbt",
            "--profiles-dir",
            "dbt",
            "--vars",
            f"{{raw_dir: '{FIXTURES}'}}",
        ],
        cwd=ROOT,
        env={**os.environ, "OLIST_DB": str(db)},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout[-4000:]
    return db


def query(db: Path, sql: str) -> list[tuple]:
    with duckdb.connect(str(db), read_only=True) as con:
        return con.sql(sql).fetchall()
