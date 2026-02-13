"""Backtesting coordinator stub."""
from __future__ import annotations

from typing import Sequence

from trading_app.data.schemas import PriceBar
from trading_app.portfolio.models import PortfolioState
from trading_app.strategies.base import Strategy


class BacktestEngine:
    """Runs strategies against historical data and tracks portfolio state."""

    def __init__(self, strategy: Strategy) -> None:
        self.strategy = strategy

    def run(self, bars: Sequence[PriceBar], starting_cash: float = 100_000.0) -> PortfolioState:
        """Execute the strategy across provided bars."""
        raise NotImplementedError("Implement backtest loop")
