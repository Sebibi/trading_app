"""Reference SMA crossover strategy."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque

from trading_app.data.schemas import PriceBar
from trading_app.execution.orders import Order, OrderSide, OrderType
from trading_app.portfolio.models import PortfolioState


@dataclass
class SmaCrossoverStrategy:
    """Long-only SMA crossover strategy for a single symbol."""

    symbol: str
    short_window: int = 20
    long_window: int = 50
    quantity: float = 1.0
    name: str = "sma_crossover"
    _closes: Deque[float] = field(default_factory=deque, init=False, repr=False)
    _prev_diff: float | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.short_window <= 0 or self.long_window <= 0:
            raise ValueError("SMA windows must be positive integers.")
        if self.short_window >= self.long_window:
            raise ValueError("short_window must be smaller than long_window.")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive.")

    def on_start(self, state: PortfolioState) -> list[Order]:
        self._closes = deque(maxlen=self.long_window)
        self._prev_diff = None
        return []

    def on_bar(self, bar: PriceBar, state: PortfolioState) -> list[Order]:
        if bar.symbol != self.symbol:
            return []

        self._closes.append(bar.close)
        if len(self._closes) < self.long_window:
            return []

        short_sma = sum(list(self._closes)[-self.short_window :]) / self.short_window
        long_sma = sum(self._closes) / self.long_window
        diff = short_sma - long_sma

        in_market = state.positions.get(self.symbol) is not None
        orders: list[Order] = []
        if self._prev_diff is None:
            if diff > 0 and not in_market:
                orders.append(
                    Order(
                        symbol=self.symbol,
                        quantity=self.quantity,
                        side=OrderSide.BUY,
                        type=OrderType.MARKET,
                    )
                )
        elif self._prev_diff <= 0 < diff and not in_market:
            orders.append(
                Order(
                    symbol=self.symbol,
                    quantity=self.quantity,
                    side=OrderSide.BUY,
                    type=OrderType.MARKET,
                )
            )
        elif self._prev_diff >= 0 > diff and in_market:
            held_quantity = state.positions[self.symbol].quantity
            orders.append(
                Order(
                    symbol=self.symbol,
                    quantity=held_quantity,
                    side=OrderSide.SELL,
                    type=OrderType.MARKET,
                )
            )

        self._prev_diff = diff
        return orders

    def on_finish(self, state: PortfolioState) -> None:
        return None
