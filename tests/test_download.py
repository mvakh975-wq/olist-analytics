from pathlib import Path

import pytest

from scripts.download import COMPLETE_MARKER, RAW_FILES, RawDataError, download, missing_files


def touch_all(d: Path, names) -> None:
    d.mkdir(parents=True, exist_ok=True)
    for n in names:
        (d / n).write_text("x\n")


def test_raw_files_list_is_complete():
    assert len(RAW_FILES) == 9
    assert "olist_orders_dataset.csv" in RAW_FILES
    assert "product_category_name_translation.csv" in RAW_FILES


def test_incomplete_raw_dir_detected(tmp_path):
    touch_all(tmp_path, RAW_FILES[:-1])
    assert missing_files(tmp_path) == [RAW_FILES[-1]]


def test_complete_dir_skips_download(tmp_path):
    touch_all(tmp_path, RAW_FILES)
    (tmp_path / COMPLETE_MARKER).write_text("ok\n")

    class Boom:
        def authenticate(self):
            raise AssertionError("must not hit the API")

    download(tmp_path, api=Boom())


class FakeApi:
    def __init__(self, files):
        self.files = files

    def authenticate(self):
        pass

    def dataset_download_files(self, dataset, path, unzip):
        assert dataset == "olistbr/brazilian-ecommerce" and unzip
        touch_all(Path(path), self.files)


def test_download_writes_files(tmp_path):
    download(tmp_path, api=FakeApi(RAW_FILES))
    assert missing_files(tmp_path) == []


def test_partial_download_is_an_error(tmp_path):
    with pytest.raises(RawDataError, match="olist_sellers_dataset.csv"):
        download(tmp_path, api=FakeApi([f for f in RAW_FILES if "sellers" not in f]))


def test_missing_credentials_message(tmp_path):
    class NoCreds:
        def authenticate(self):
            raise OSError("Could not find kaggle.json")

    with pytest.raises(RawDataError) as exc:
        download(tmp_path, api=NoCreds())
    msg = str(exc.value)
    assert "kaggle.com/datasets/olistbr/brazilian-ecommerce" in msg
    assert str(tmp_path) in msg


def test_client_exit_on_missing_credentials_becomes_raw_data_error(tmp_path):
    # kaggle>=2 prints its own help and calls sys.exit() when no token is configured
    class ExitingClient:
        def authenticate(self):
            raise SystemExit(1)

    with pytest.raises(RawDataError, match="kaggle auth login"):
        download(tmp_path, api=ExitingClient())


def test_files_from_an_interrupted_download_are_not_trusted(tmp_path):
    # all names present (e.g. unzip was interrupted) but the download never completed
    touch_all(tmp_path, RAW_FILES)
    (tmp_path / "olist_orders_dataset.csv").write_text("")
    calls = []

    class Api(FakeApi):
        def dataset_download_files(self, dataset, path, unzip):
            calls.append(path)
            super().dataset_download_files(dataset, path, unzip)

    download(tmp_path, api=Api(RAW_FILES))
    assert calls, "an incomplete directory must trigger a fresh download"
    assert missing_files(tmp_path) == []


def test_download_failure_becomes_raw_data_error(tmp_path):
    class Offline(FakeApi):
        def dataset_download_files(self, dataset, path, unzip):
            raise ConnectionError("network is unreachable")

    with pytest.raises(RawDataError, match="network is unreachable"):
        download(tmp_path, api=Offline(RAW_FILES))
    assert missing_files(tmp_path) == list(RAW_FILES)
