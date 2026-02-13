"""Filesystem-backed Parquet implementation stub."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

from trading_app.data.schemas import NewsItem, PriceBar, Quote
from trading_app.data.storage.base import DataStore


class ParquetDataStore(DataStore):
    """Persists market/news data as Parquet files under a root directory."""

    def __init__(self, root_path: str) -> None:
        self.root_path = Path(root_path)

    def save_prices(self, bars: Iterable[PriceBar]) -> None:
        raise NotImplementedError("Write bars to Parquet files")

    def load_prices(self, symbol: str, limit: int | None = None) -> Sequence[PriceBar]:
        raise NotImplementedError("Read bars from Parquet files")

    def save_quotes(self, quotes: Iterable[Quote]) -> None:
        raise NotImplementedError("Write quotes to Parquet files")

    def save_news(self, items: Iterable[NewsItem]) -> None:
        raise NotImplementedError("Write news items to Parquet files")

    def load_news(self, symbol: str | None = None, limit: int | None = None) -> Sequence[NewsItem]:
        raise NotImplementedError("Read news items from Parquet files")
