"""yfinance-based market data source implementation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Sequence

import pandas as pd
import yfinance as yf

from trading_app.data.schemas import PriceBar, Quote
from trading_app.data.sources.base import MarketDataSource


class YFinanceSource:
    """Pulls historical prices and simple quote snapshots using yfinance."""

    name = "yfinance"

    def fetch_history(
        self, symbols: Sequence[str], start: datetime | None = None, end: datetime | None = None
    ) -> Iterable[PriceBar]:
        if not symbols:
            return []

        data = yf.download(
            tickers=list(symbols),
            start=start,
            end=end,
            progress=False,
            group_by="ticker",
            auto_adjust=False,
            threads=True,
        )

        # yfinance returns MultiIndex when multiple tickers requested
        if isinstance(data.columns, pd.MultiIndex):
            for symbol in symbols:
                if symbol not in data.columns.levels[0]:
                    continue
                sym_df = data[symbol].dropna()
                for ts, row in sym_df.iterrows():
                    yield PriceBar(
                        symbol=symbol,
                        timestamp=ts.to_pydatetime(),
                        open=float(row["Open"]),
                        high=float(row["High"]),
                        low=float(row["Low"]),
                        close=float(row["Close"]),
                        volume=float(row["Volume"]) if not pd.isna(row["Volume"]) else None,
                        provider=self.name,
                    )
        else:
            sym = symbols[0]
            for ts, row in data.dropna().iterrows():
                yield PriceBar(
                    symbol=sym,
                    timestamp=ts.to_pydatetime(),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=float(row["Volume"]) if not pd.isna(row["Volume"]) else None,
                    provider=self.name,
                )

    def stream_live(self, symbols: Sequence[str]) -> Iterable[PriceBar]:
        raise NotImplementedError("Live streaming not supported via yfinance")

    @staticmethod
    def _coerce_float(value: object) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def fetch_quotes(self, symbols: Sequence[str]) -> Iterable[Quote]:
        for symbol in symbols:
            ticker = yf.Ticker(symbol)
            try:
                info = ticker.fast_info
                bid = self._coerce_float(info.get("bid"))
                ask = self._coerce_float(info.get("ask"))
                last_price = self._coerce_float(info.get("last_price"))
            except Exception:
                continue

            if bid is None and ask is None and last_price is None:
                continue

            # Fill missing sides with last trade when available.
            bid_val = bid if bid is not None else last_price
            ask_val = ask if ask is not None else last_price
            if bid_val is None:
                bid_val = ask_val
            if ask_val is None:
                ask_val = bid_val
            if bid_val is None or ask_val is None:
                continue

            ts = datetime.now(timezone.utc)
            yield Quote(
                symbol=symbol,
                timestamp=ts,
                bid=bid_val,
                ask=ask_val,
                provider=self.name,
            )
