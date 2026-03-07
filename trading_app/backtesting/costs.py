"""Execution cost models for backtests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from trading_app.execution.orders import Order, OrderSide


class CommissionModel(Protocol):
    """Computes commission charged for an executed fill."""

    def calculate(self, order: Order, fill_qty: float, fill_price: float) -> float:
        """Return commission amount in cash units."""
        ...


class SlippageModel(Protocol):
    """Adjusts reference bar price to an effective execution price."""

    def apply(self, order: Order, reference_price: float) -> float:
        """Return effective execution price after slippage."""
        ...


@dataclass(frozen=True)
class ZeroCommissionModel:
    """Commission model that charges nothing."""

    def calculate(self, order: Order, fill_qty: float, fill_price: float) -> float:
        del order, fill_qty, fill_price
        return 0.0


@dataclass(frozen=True)
class FixedAndBpsCommissionModel:
    """Commission model supporting fixed and notional-based fees."""

    fixed: float = 0.0
    bps: float = 0.0

    def calculate(self, order: Order, fill_qty: float, fill_price: float) -> float:
        del order
        notional = fill_qty * fill_price
        return self.fixed + (notional * self.bps / 10_000.0)


@dataclass(frozen=True)
class ZeroSlippageModel:
    """Slippage model that keeps execution at reference price."""

    def apply(self, order: Order, reference_price: float) -> float:
        del order
        return reference_price


@dataclass(frozen=True)
class BpsSlippageModel:
    """Apply side-aware slippage in basis points."""

    bps: float

    def apply(self, order: Order, reference_price: float) -> float:
        multiplier = self.bps / 10_000.0
        if order.side is OrderSide.BUY:
            return reference_price * (1.0 + multiplier)
        return reference_price * (1.0 - multiplier)
