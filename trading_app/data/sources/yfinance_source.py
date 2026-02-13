"""yfinance-based market data source implementation."""

from __future__ import annotations

from datetime import datetime
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

    def fetch_quotes(self, symbols: Sequence[str]) -> Iterable[Quote]:
        for symbol in symbols:
            ticker = yf.Ticker(symbol)
            try:
                info = ticker.fast_info
                bid = info.get("bid")
                ask = info.get("ask")
                last_price = info.get("last_price")
            except Exception:
                continue

            # If bid/ask missing, fall back to last price on both sides
            bid_val = float(bid) if bid is not None else float(last_price)
            ask_val = float(ask) if ask is not None else float(last_price)
            ts = datetime.utcnow()
            yield Quote(
                symbol=symbol,
                timestamp=ts,
                bid=bid_val,
                ask=ask_val,
                provider=self.name,
            )
