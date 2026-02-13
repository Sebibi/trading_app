"""Shared data models for market and news data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Sequence


@dataclass
class PriceBar:
    """OHLCV bar for a single instrument."""

    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
    provider: str | None = None


@dataclass
class Quote:
    """Top-of-book quote snapshot."""

    symbol: str
    timestamp: datetime
    bid: float
    ask: float
    bid_size: float | None = None
    ask_size: float | None = None
    provider: str | None = None


@dataclass
class NewsItem:
    """Structured representation of a news headline or article summary."""

    id: str
    symbol: str | None
    published_at: datetime
    title: str
    summary: str
    source: str
    sentiment: Literal["positive", "neutral", "negative"] | None = None
    tickers: Sequence[str] | None = None
