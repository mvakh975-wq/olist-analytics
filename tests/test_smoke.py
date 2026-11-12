import dbt.version
import duckdb


def test_toolchain_imports():
    assert duckdb.sql("select 1").fetchone() == (1,)
    assert dbt.version.__version__
