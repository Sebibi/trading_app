"""Broker/exchange interface stub."""
from __future__ import annotations

from typing import Iterable, Protocol

from trading_app.execution.orders import Fill, Order
from trading_app.portfolio.models import PortfolioState


class Broker(Protocol):
    """Abstracts live or simulated execution."""

    name: str

    def submit_orders(self, orders: Iterable[Order], state: PortfolioState) -> Iterable[Fill]:
        """Send orders and return resulting fills."""
        ...

    def cancel_all(self, symbols: Iterable[str]) -> None:
        """Cancel open orders for the given symbols."""
        ...
