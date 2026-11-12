DBT = uv run dbt --no-use-colors
DBT_ARGS = --project-dir dbt --profiles-dir dbt

.PHONY: data build export site-data datalens site test lint

data:
	uv run python -m scripts.download

build:
	$(DBT) build $(DBT_ARGS)

export:
	uv run python -m scripts.export_marts export

site-data:
	uv run python -m scripts.export_marts site-data

datalens:
	uv run python -m scripts.export_marts datalens

site: site-data
	cd site && npm install && npm run dev

test:
	uv run pytest

lint:
	uv run ruff check . && uv run ruff format --check . && uv run sqlfluff lint dbt/models dbt/tests
