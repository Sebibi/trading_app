"""Strategy implementations and interfaces."""

from trading_app.strategies.base import Strategy
from trading_app.strategies.buy_and_hold import BuyAndHoldStrategy
from trading_app.strategies.sma_crossover import SmaCrossoverStrategy

__all__ = ["Strategy", "BuyAndHoldStrategy", "SmaCrossoverStrategy"]
