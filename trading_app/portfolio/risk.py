"""Risk management policies and checks (placeholder)."""
from __future__ import annotations

from typing import Protocol

from trading_app.execution.orders import Order
from trading_app.portfolio.models import PortfolioState


class RiskModel(Protocol):
    """Validates orders against risk constraints."""

    name: str

    def validate(self, orders: list[Order], state: PortfolioState) -> list[Order]:
        """Return approved orders, potentially adjusted or filtered."""
        ...
