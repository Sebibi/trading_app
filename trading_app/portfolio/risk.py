"""Risk management policies and checks."""

from __future__ import annotations

from dataclasses import replace
from dataclasses import dataclass
from typing import Protocol
from typing import Sequence

from trading_app.execution.orders import Order, OrderSide
from trading_app.portfolio.models import PortfolioState


class RiskModel(Protocol):
    """Validates orders against risk constraints."""

    name: str

    def validate(self, orders: list[Order], state: PortfolioState) -> list[Order]:
        """Return approved orders, potentially adjusted or filtered."""
        ...


@dataclass(frozen=True)
class NoOpRiskModel:
    """Pass-through risk model for deterministic baseline behavior."""

    name: str = "noop_risk"

    def validate(self, orders: list[Order], state: PortfolioState) -> list[Order]:
        del state
        return list(orders)


@dataclass(frozen=True)
class NoDuplicateBuyRiskModel:
    """Blocks duplicate buy intents for symbols already held or requested."""

    name: str = "no_duplicate_buy"

    def validate(self, orders: list[Order], state: PortfolioState) -> list[Order]:
        approved: list[Order] = []
        seen_buy_symbols = set(state.positions.keys())
        for order in orders:
            if order.side is OrderSide.BUY and order.symbol in seen_buy_symbols:
                continue
            approved.append(order)
            if order.side is OrderSide.BUY:
                seen_buy_symbols.add(order.symbol)
        return approved


@dataclass(frozen=True)
class MaxPositionSizeRiskModel:
    """Caps long exposure per symbol by quantity."""

    max_quantity: float
    name: str = "max_position_size"

    def validate(self, orders: list[Order], state: PortfolioState) -> list[Order]:
        projected_qty = {
            symbol: position.quantity for symbol, position in state.positions.items()
        }
        approved: list[Order] = []
        for order in orders:
            current = projected_qty.get(order.symbol, 0.0)
            if order.side is OrderSide.BUY:
                remaining = self.max_quantity - current
                if remaining <= 0:
                    continue
                qty = min(order.quantity, remaining)
                approved_order = order if qty == order.quantity else replace(order, quantity=qty)
                projected_qty[order.symbol] = current + qty
                approved.append(approved_order)
                continue

            sell_qty = min(order.quantity, current)
            if sell_qty <= 0:
                continue
            approved_order = order if sell_qty == order.quantity else replace(order, quantity=sell_qty)
            projected_qty[order.symbol] = current - sell_qty
            approved.append(approved_order)
        return approved


@dataclass(frozen=True)
class CompositeRiskModel:
    """Applies multiple risk models sequentially."""

    models: Sequence[RiskModel]
    name: str = "composite_risk"

    def validate(self, orders: list[Order], state: PortfolioState) -> list[Order]:
        approved = list(orders)
        for model in self.models:
            approved = model.validate(approved, state)
        return approved
