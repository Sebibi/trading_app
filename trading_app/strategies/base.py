"""Strategy interface for both backtests and live trading."""

from __future__ import annotations

from typing import Protocol, Sequence

from trading_app.data.schemas import PriceBar
from trading_app.execution.orders import Order
from trading_app.portfolio.models import PortfolioState


class Strategy(Protocol):
    """Processes market data and emits orders."""

    name: str

    def on_start(self, state: PortfolioState) -> Sequence[Order]:
        """Called once before the run begins."""
        ...

    def on_bar(self, bar: PriceBar, state: PortfolioState) -> Sequence[Order]:
        """Handle a new price bar and decide on orders."""
        ...

    def on_finish(self, state: PortfolioState) -> None:
        """Called after the run ends to release resources/report."""
        ...
