from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Sequence

import pytest

from trading_app.data.pipeline import DataPipeline
from trading_app.data.schemas import NewsItem, PriceBar, Quote
from trading_app.data.storage.base import DataStore

pytestmark = pytest.mark.unit


class FakeMarketSource:
    def __init__(self, name: str, bars: Sequence[PriceBar]) -> None:
        self.name = name
        self._bars = list(bars)
        self.requested_symbols: list[str] | None = None

    def fetch_history(
        self, symbols: Sequence[str], start: datetime | None = None, end: datetime | None = None
    ) -> Iterable[PriceBar]:
        self.requested_symbols = list(symbols)
        return list(self._bars)

    def stream_live(self, symbols: Sequence[str]) -> Iterable[PriceBar]:
        self.requested_symbols = list(symbols)
        yield from self._bars

    def fetch_quotes(self, symbols: Sequence[str]) -> Iterable[Quote]:
        return []


class FakeNewsSource:
    def __init__(self, name: str, news: Sequence[NewsItem]) -> None:
        self.name = name
        self._news = list(news)
        self.requested_symbols: list[str] | None = None

    def fetch_news(
        self,
        symbols: Sequence[str] | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> Iterable[NewsItem]:
        self.requested_symbols = list(symbols) if symbols else None
        return list(self._news)

    def stream_news(self, symbols: Sequence[str] | None = None) -> Iterable[NewsItem]:
        return []


class FakeStore(DataStore):
    def __init__(self) -> None:
        self.prices: list[PriceBar] = []
        self.quotes: list[Quote] = []
        self.news: list[NewsItem] = []

    def save_prices(self, bars: Iterable[PriceBar]) -> None:
        self.prices.extend(list(bars))

    def load_prices(self, symbol: str, limit: int | None = None) -> Sequence[PriceBar]:
        return []

    def save_quotes(self, quotes: Iterable[Quote]) -> None:
        self.quotes.extend(list(quotes))

    def save_news(self, items: Iterable[NewsItem]) -> None:
        self.news.extend(list(items))

    def load_news(
        self, symbol: str | None = None, limit: int | None = None
    ) -> Sequence[NewsItem]:
        return []


def _price_bar(symbol: str, ts: datetime) -> PriceBar:
    return PriceBar(
        symbol=symbol,
        timestamp=ts,
        open=1.0,
        high=2.0,
        low=0.5,
        close=1.5,
        volume=10.0,
        provider="test",
    )


def test_ingest_history_collects_from_all_sources() -> None:
    store = FakeStore()
    ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
    bars_a = [_price_bar("AAPL", ts)]
    bars_b = [_price_bar("AAPL", ts.replace(hour=1))]

    source_a = FakeMarketSource("s1", bars_a)
    source_b = FakeMarketSource("s2", bars_b)
    pipeline = DataPipeline(store=store, market_sources=[source_a, source_b])

    pipeline.ingest_history(["AAPL"])

    assert store.prices == bars_a + bars_b
    assert source_a.requested_symbols == ["AAPL"]
    assert source_b.requested_symbols == ["AAPL"]


def test_ingest_history_ignores_empty_symbol_list() -> None:
    store = FakeStore()
    source = FakeMarketSource("s1", [])
    pipeline = DataPipeline(store=store, market_sources=[source])

    pipeline.ingest_history([])

    assert store.prices == []


def test_ingest_news_collects_from_sources() -> None:
    store = FakeStore()
    ts = datetime(2024, 2, 1, tzinfo=timezone.utc)
    news_items = [
        NewsItem(
            id="1",
            symbol="MSFT",
            published_at=ts,
            title="News",
            summary="Summary",
            source="wire",
            sentiment=None,
            tickers=["MSFT"],
        )
    ]

    news_source = FakeNewsSource("news", news_items)
    pipeline = DataPipeline(store=store, market_sources=[], news_sources=[news_source])

    pipeline.ingest_news(["MSFT"])

    assert store.news == news_items
    assert news_source.requested_symbols == ["MSFT"]


def test_stream_live_yields_from_all_sources_in_order() -> None:
    store = FakeStore()
    ts = datetime(2024, 3, 1, tzinfo=timezone.utc)
    bars_a = [_price_bar("AAPL", ts)]
    bars_b = [_price_bar("AAPL", ts.replace(minute=30))]

    source_a = FakeMarketSource("s1", bars_a)
    source_b = FakeMarketSource("s2", bars_b)
    pipeline = DataPipeline(store=store, market_sources=[source_a, source_b])

    streamed = list(pipeline.stream_live(["AAPL"]))

    assert streamed == bars_a + bars_b
