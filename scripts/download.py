"""Download the Olist dataset from Kaggle into data/raw and verify it is complete."""

from __future__ import annotations

import sys
from pathlib import Path

DATASET = "olistbr/brazilian-ecommerce"
DATASET_URL = "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce"
DEFAULT_RAW_DIR = Path("data/raw")

RAW_FILES = (
    "olist_customers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
)


class RawDataError(Exception):
    pass


def missing_files(raw_dir: Path) -> list[str]:
    return [name for name in RAW_FILES if not (raw_dir / name).is_file()]


def _default_api():
    # importing the kaggle package may already try to authenticate
    from kaggle.api.kaggle_api_extended import KaggleApi

    return KaggleApi()


def download(raw_dir: Path, api=None) -> None:
    if not missing_files(raw_dir):
        return
    raw_dir.mkdir(parents=True, exist_ok=True)
    try:
        api = api or _default_api()
        api.authenticate()
    except (Exception, SystemExit) as exc:  # kaggle>=2 calls sys.exit() without a token
        raise RawDataError(
            "Kaggle credentials not found.\n"
            "Either run `uv run kaggle auth login`, or create a token at "
            "https://www.kaggle.com/settings/api and save it to ~/.kaggle/access_token,\n"
            "or download the archive manually from\n"
            f"  {DATASET_URL}\n"
            f"and unzip all CSV files into {raw_dir}"
        ) from exc
    api.dataset_download_files(DATASET, path=str(raw_dir), unzip=True)
    missing = missing_files(raw_dir)
    if missing:
        raise RawDataError(f"Download incomplete, missing: {', '.join(missing)}")


def main(argv: list[str] | None = None) -> int:
    raw_dir = Path(argv[0]) if argv else DEFAULT_RAW_DIR
    try:
        download(raw_dir)
    except RawDataError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Raw data ready in {raw_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
