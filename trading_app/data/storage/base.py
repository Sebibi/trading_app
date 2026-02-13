"""Storage contracts for persisting and retrieving data."""

from __future__ import annotations

from typing import Iterable, Protocol, Sequence

from trading_app.data.schemas import NewsItem, PriceBar, Quote


class DataStore(Protocol):
    """Abstract storage backend (filesystem, database, object store)."""

    def save_prices(self, bars: Iterable[PriceBar]) -> None: ...

    def load_prices(self, symbol: str, limit: int | None = None) -> Sequence[PriceBar]: ...

    def save_quotes(self, quotes: Iterable[Quote]) -> None: ...

    def save_news(self, items: Iterable[NewsItem]) -> None: ...

    def load_news(
        self, symbol: str | None = None, limit: int | None = None
    ) -> Sequence[NewsItem]: ...
