from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from trading_app.data.schemas import NewsItem, PriceBar, Quote
from trading_app.data.storage.parquet_store import ParquetDataStore

pytestmark = pytest.mark.unit


def _bar(symbol: str, ts: datetime, close: float) -> PriceBar:
    return PriceBar(
        symbol=symbol,
        timestamp=ts,
        open=close - 0.5,
        high=close + 0.5,
        low=close - 1.0,
        close=close,
        volume=100.0,
        provider="test",
    )


def _quote(symbol: str, ts: datetime, bid: float, ask: float) -> Quote:
    return Quote(symbol=symbol, timestamp=ts, bid=bid, ask=ask, provider="q")


def test_save_and_load_prices_round_trip(tmp_path) -> None:
    store = ParquetDataStore(str(tmp_path))
    ts1 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    ts2 = datetime(2024, 1, 2, tzinfo=timezone.utc)
    bars = [_bar("AAPL", ts1, 150.0), _bar("AAPL", ts2, 151.0)]

    store.save_prices(bars)

    loaded = store.load_prices("AAPL")

    assert loaded == bars


def test_save_prices_deduplicates_and_orders(tmp_path) -> None:
    store = ParquetDataStore(str(tmp_path))
    ts1 = datetime(2024, 1, 2, tzinfo=timezone.utc)
    ts2 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    bar_latest = _bar("MSFT", ts1, 300.0)
    bar_earlier = _bar("MSFT", ts2, 295.0)

    store.save_prices([bar_latest, bar_earlier])
    # duplicate of bar_earlier should be ignored
    store.save_prices([_bar("MSFT", ts2, 295.0)])

    loaded = store.load_prices("MSFT")

    assert loaded == [bar_earlier, bar_latest]


def test_save_quotes_deduplicates_by_symbol_and_timestamp(tmp_path) -> None:
    store = ParquetDataStore(str(tmp_path))
    ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
    quotes = [
        _quote("AAPL", ts, 100.0, 101.0),
        _quote("AAPL", ts, 100.0, 101.0),  # duplicate
    ]

    store.save_quotes(quotes)
    store.save_quotes([_quote("AAPL", ts, 100.0, 101.0)])  # duplicate again

    df = pd.read_parquet(store._quotes_path(), engine="pyarrow")

    assert len(df) == 1
    assert df.iloc[0].symbol == "AAPL"
    assert pd.to_datetime(df.iloc[0].timestamp, utc=True) == ts


def test_save_news_groups_by_symbol_and_deduplicates(tmp_path) -> None:
    store = ParquetDataStore(str(tmp_path))
    ts1 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    ts2 = datetime(2024, 1, 2, tzinfo=timezone.utc)
    news_items = [
        NewsItem(
            id="1",
            symbol="AAPL",
            published_at=ts1,
            title="AAPL 1",
            summary="s1",
            source="wire",
            sentiment=None,
            tickers=["AAPL"],
        ),
        NewsItem(
            id="2",
            symbol=None,
            published_at=ts2,
            title="General",
            summary="s2",
            source="wire",
            sentiment=None,
            tickers=None,
        ),
    ]

    store.save_news(news_items)
    # duplicate id should be ignored
    store.save_news([news_items[0]])

    aapl_news = store.load_news("AAPL")
    general_news = store.load_news(None)

    assert [item.id for item in aapl_news] == ["1"]
    assert [item.id for item in general_news] == ["2"]
