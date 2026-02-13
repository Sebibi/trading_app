"""Filesystem-backed Parquet implementation."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd

from trading_app.data.schemas import NewsItem, PriceBar, Quote
from trading_app.data.storage.base import DataStore


class ParquetDataStore(DataStore):
    """Persists market/news data as Parquet files under a root directory."""

    def __init__(self, root_path: str) -> None:
        self.root_path = Path(root_path)
        self.root_path.mkdir(parents=True, exist_ok=True)

    # ---------- Prices ----------
    def _prices_path(self, symbol: str) -> Path:
        return self.root_path / "prices" / f"{symbol}.parquet"

    def save_prices(self, bars: Iterable[PriceBar]) -> None:
        records = [asdict(bar) for bar in bars]
        if not records:
            return
        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        symbol = df.iloc[0]["symbol"]
        path = self._prices_path(symbol)
        path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if path.exists() else "w"
        df.to_parquet(path, engine="pyarrow", compression="snappy", index=False, append=mode == "a")

    def load_prices(self, symbol: str, limit: int | None = None) -> Sequence[PriceBar]:
        path = self._prices_path(symbol)
        if not path.exists():
            return []
        df = pd.read_parquet(path, engine="pyarrow")
        if limit:
            df = df.tail(limit)
        return [
            PriceBar(
                symbol=row.symbol,
                timestamp=pd.to_datetime(row.timestamp).to_pydatetime(),
                open=float(row.open),
                high=float(row.high),
                low=float(row.low),
                close=float(row.close),
                volume=float(row.volume) if pd.notna(row.volume) else None,
                provider=row.provider,
            )
            for row in df.itertuples()
        ]

    # ---------- Quotes ----------
    def _quotes_path(self) -> Path:
        return self.root_path / "quotes.parquet"

    def save_quotes(self, quotes: Iterable[Quote]) -> None:
        records = [asdict(q) for q in quotes]
        if not records:
            return
        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        path = self._quotes_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if path.exists() else "w"
        df.to_parquet(path, engine="pyarrow", compression="snappy", index=False, append=mode == "a")

    # ---------- News ----------
    def _news_path(self, symbol: str | None = None) -> Path:
        if symbol:
            return self.root_path / "news" / f"{symbol}.parquet"
        return self.root_path / "news" / "all.parquet"

    def save_news(self, items: Iterable[NewsItem]) -> None:
        records = [asdict(item) for item in items]
        if not records:
            return
        df = pd.DataFrame(records)
        df["published_at"] = pd.to_datetime(df["published_at"], utc=True)
        symbols = df["symbol"].fillna("all").unique()
        for sym in symbols:
            sym_df = df[df["symbol"].fillna("all") == sym]
            path = self._news_path(sym if sym != "all" else None)
            path.parent.mkdir(parents=True, exist_ok=True)
            mode = "a" if path.exists() else "w"
            sym_df.to_parquet(
                path, engine="pyarrow", compression="snappy", index=False, append=mode == "a"
            )

    def load_news(self, symbol: str | None = None, limit: int | None = None) -> Sequence[NewsItem]:
        path = self._news_path(symbol)
        fallback = self._news_path(None)
        if not path.exists():
            if fallback.exists():
                path = fallback
            else:
                return []
        df = pd.read_parquet(path, engine="pyarrow")
        if limit:
            df = df.tail(limit)
        return [
            NewsItem(
                id=str(row.id),
                symbol=row.symbol if pd.notna(row.symbol) else None,
                published_at=pd.to_datetime(row.published_at).to_pydatetime(),
                title=row.title,
                summary=row.summary,
                source=row.source,
                sentiment=row.sentiment if pd.notna(row.sentiment) else None,
                tickers=(
                    list(row.tickers)
                    if hasattr(row, "tickers") and row.tickers is not None
                    else None
                ),
            )
            for row in df.itertuples()
        ]
