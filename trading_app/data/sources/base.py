"""Abstract interfaces for pulling market and news data."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, Protocol, Sequence

from trading_app.data.schemas import NewsItem, PriceBar, Quote


class MarketDataSource(Protocol):
    """Contract for any market data provider (historical or live)."""

    name: str

    def fetch_history(
        self, symbols: Sequence[str], start: datetime | None = None, end: datetime | None = None
    ) -> Iterable[PriceBar]:
        """Yield historical bars for the requested symbols."""
        ...

    def stream_live(self, symbols: Sequence[str]) -> Iterable[PriceBar]:
        """Stream live bars or ticks."""
        ...

    def fetch_quotes(self, symbols: Sequence[str]) -> Iterable[Quote]:
        """Get latest top-of-book quotes."""
        ...


class NewsDataSource(Protocol):
    """Contract for any textual news or article provider."""

    name: str

    def fetch_news(
        self, symbols: Sequence[str] | None = None, start: datetime | None = None, end: datetime | None = None
    ) -> Iterable[NewsItem]:
        """Yield news items for symbols in a time window."""
        ...

    def stream_news(self, symbols: Sequence[str] | None = None) -> Iterable[NewsItem]:
        """Stream news items in near-real-time."""
        ...
