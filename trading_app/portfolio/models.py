"""Portfolio state models used by strategies and backtests."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Position:
    """Represents holdings for a single symbol."""

    symbol: str
    quantity: float
    cost_basis: float


@dataclass
class PortfolioState:
    """Snapshot of portfolio holdings and cash."""

    cash: float
    positions: Dict[str, Position] = field(default_factory=dict)
    equity: float | None = None  # computed value of cash + positions
