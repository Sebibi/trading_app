"""Reference buy-and-hold strategy for backtest validation."""

from __future__ import annotations

from dataclasses import dataclass, field

from trading_app.data.schemas import PriceBar
from trading_app.execution.orders import Order, OrderSide, OrderType
from trading_app.portfolio.models import PortfolioState


@dataclass
class BuyAndHoldStrategy:
    """Buy a fixed quantity of one symbol on the first seen bar, then hold."""

    symbol: str
    quantity: float
    name: str = "buy_and_hold"
    _has_bought: bool = field(default=False, init=False, repr=False)

    def on_start(self, state: PortfolioState) -> list[Order]:
        self._has_bought = False
        return []

    def on_bar(self, bar: PriceBar, state: PortfolioState) -> list[Order]:
        if self._has_bought:
            return []
        if bar.symbol != self.symbol:
            return []
        self._has_bought = True
        return [
            Order(
                symbol=self.symbol,
                quantity=self.quantity,
                side=OrderSide.BUY,
                type=OrderType.MARKET,
            )
        ]

    def on_finish(self, state: PortfolioState) -> None:
        return None
