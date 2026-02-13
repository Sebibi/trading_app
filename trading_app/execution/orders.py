"""Order and execution primitives."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


@dataclass
class Order:
    """Basic order representation to be used by strategies and brokers."""

    symbol: str
    quantity: float
    side: OrderSide
    type: OrderType = OrderType.MARKET
    limit_price: float | None = None
    stop_price: float | None = None
    time_in_force: Literal["DAY", "GTC"] = "DAY"


@dataclass
class Fill:
    """Execution report for an order fill."""

    order: Order
    fill_price: float
    fill_qty: float
    commission: float | None = None
