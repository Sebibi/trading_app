from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest

from trading_app.cli.main import main
from trading_app.data.schemas import PriceBar
from trading_app.data.storage.parquet_store import ParquetDataStore


@pytest.mark.unit
def test_ingest_history_uses_source_and_writes_parquet(tmp_path, monkeypatch) -> None:
    def fake_fetch_history(self, symbols, start=None, end=None):
        assert symbols == ["AAPL"]
        assert start == datetime(2024, 1, 1)
        assert end == datetime(2024, 1, 3)
        return [
            PriceBar(
                symbol="AAPL",
                timestamp=datetime(2024, 1, 2, tzinfo=timezone.utc),
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
                volume=1000.0,
                provider="yfinance",
            )
        ]

    monkeypatch.setattr(
        "trading_app.cli.main.YFinanceSource.fetch_history",
        fake_fetch_history,
    )

    exit_code = main(
        [
            "ingest-history",
            "AAPL",
            "--store-path",
            str(tmp_path),
            "--start",
            "2024-01-01",
            "--end",
            "2024-01-03",
        ]
    )

    loaded = ParquetDataStore(str(tmp_path)).load_prices("AAPL")
    assert exit_code == 0
    assert len(loaded) == 1
    assert loaded[0].close == 100.5


@pytest.mark.integration
@pytest.mark.network
def test_ingest_history_real_network_fetch(tmp_path) -> None:
    if os.getenv("RUN_NETWORK_TESTS") != "1":
        pytest.skip("Set RUN_NETWORK_TESTS=1 to enable network tests.")

    exit_code = main(
        [
            "ingest-history",
            "MSFT",
            "--store-path",
            str(tmp_path),
            "--start",
            "2024-01-01",
            "--end",
            "2024-02-01",
        ]
    )

    loaded = ParquetDataStore(str(tmp_path)).load_prices("MSFT")
    assert exit_code == 0
    assert loaded
