DBT = uv run dbt --no-use-colors
DBT_ARGS = --project-dir dbt --profiles-dir dbt

.PHONY: data build export site-db site test lint

data:            ## download raw CSVs from Kaggle into data/raw
	uv run python -m scripts.download

build:           ## build and test all dbt models on full data
	$(DBT) build $(DBT_ARGS)

export:          ## export marts to data/marts/*.parquet
	uv run python -m scripts.export_marts export

site-db:         ## build the DuckDB file Evidence reads, from committed parquet
	uv run python -m scripts.export_marts site-db

site: site-db    ## run the dashboard locally
	cd site && npm install && npm run sources && npm run dev

test:
	uv run pytest

lint:
	uv run ruff check . && uv run ruff format --check . && uv run sqlfluff lint dbt/models dbt/tests
