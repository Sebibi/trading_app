"""Coordinator for moving data from sources into storage."""

from __future__ import annotations

from typing import Iterable, Sequence

from trading_app.data.schemas import NewsItem, PriceBar
from trading_app.data.sources.base import MarketDataSource, NewsDataSource
from trading_app.data.storage.base import DataStore


class DataPipeline:
    """Orchestrates ingestion and normalization of market/news data."""

    def __init__(
        self,
        store: DataStore,
        market_sources: Sequence[MarketDataSource],
        news_sources: Sequence[NewsDataSource] | None = None,
    ) -> None:
        self.store = store
        self.market_sources = list(market_sources)
        self.news_sources = list(news_sources) if news_sources else []

    def ingest_history(self, symbols: Sequence[str]) -> None:
        """Fetch historical bars and persist them."""
        if not symbols:
            return

        for source in self.market_sources:
            bars = list(source.fetch_history(symbols))
            if bars:
                self.store.save_prices(bars)

    def ingest_news(self, symbols: Sequence[str] | None = None) -> None:
        """Fetch historical news and persist it."""
        if not self.news_sources:
            return

        for source in self.news_sources:
            items = list(source.fetch_news(symbols))
            if items:
                self.store.save_news(items)

    def stream_live(self, symbols: Sequence[str]) -> Iterable[PriceBar]:
        """Pass-through live stream from the selected source(s)."""
        if not symbols:
            return []

        for source in self.market_sources:
            yield from source.stream_live(symbols)

    def list_sources(self) -> list[str]:
        """Return registered data source names."""
        return [source.name for source in [*self.market_sources, *self.news_sources]]


class PipelineContext:
    """Placeholder for per-run context (e.g., start/end times, run id)."""

    def __init__(self, run_id: str | None = None) -> None:
        self.run_id = run_id
