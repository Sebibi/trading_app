from __future__ import annotations

from datetime import timezone

import pytest

from trading_app.data.sources.yfinance_source import YFinanceSource

pytestmark = pytest.mark.unit


class _FakeTicker:
    def __init__(self, fast_info: dict[str, object]) -> None:
        self.fast_info = fast_info


def test_fetch_quotes_skips_symbols_with_no_price_data(monkeypatch) -> None:
    def fake_ticker(_symbol: str) -> _FakeTicker:
        return _FakeTicker({"bid": None, "ask": None, "last_price": None})

    monkeypatch.setattr("trading_app.data.sources.yfinance_source.yf.Ticker", fake_ticker)
    source = YFinanceSource()

    quotes = list(source.fetch_quotes(["AAPL"]))

    assert quotes == []


def test_fetch_quotes_falls_back_and_returns_utc_timestamp(monkeypatch) -> None:
    def fake_ticker(_symbol: str) -> _FakeTicker:
        return _FakeTicker({"bid": None, "ask": 101.5, "last_price": 101.0})

    monkeypatch.setattr("trading_app.data.sources.yfinance_source.yf.Ticker", fake_ticker)
    source = YFinanceSource()

    quotes = list(source.fetch_quotes(["AAPL"]))

    assert len(quotes) == 1
    quote = quotes[0]
    assert quote.bid == 101.0
    assert quote.ask == 101.5
    assert quote.timestamp.tzinfo == timezone.utc
