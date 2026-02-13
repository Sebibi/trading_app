from __future__ import annotations

from datetime import datetime, timezone

import pytest

from trading_app.cli.main import main
from trading_app.data.schemas import PriceBar
from trading_app.data.storage.parquet_store import ParquetDataStore

pytestmark = pytest.mark.unit


def test_backtest_dry_run_executes(tmp_path, capsys) -> None:
    exit_code = main(
        [
            "backtest-dry-run",
            "--symbol",
            "AAPL",
            "--store-path",
            str(tmp_path),
        ]
    )

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "Backtest dry-run" in out
    assert "engine_status=not_implemented" in out


def test_show_latest_prices_prints_latest_bar(tmp_path, capsys) -> None:
    store = ParquetDataStore(str(tmp_path))
    store.save_prices(
        [
            PriceBar(
                symbol="AAPL",
                timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
                volume=1000.0,
                provider="test",
            )
        ]
    )

    exit_code = main(
        [
            "show-latest-prices",
            "AAPL",
            "--store-path",
            str(tmp_path),
        ]
    )

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "AAPL:" in out
    assert "C=100.5000" in out
