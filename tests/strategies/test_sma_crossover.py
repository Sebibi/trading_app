from __future__ import annotations

from datetime import datetime, timezone

import pytest

from trading_app.data.schemas import PriceBar
from trading_app.execution.orders import OrderSide
from trading_app.portfolio.models import PortfolioState, Position
from trading_app.strategies.sma_crossover import SmaCrossoverStrategy

pytestmark = pytest.mark.unit


def _bar(close: float, day: int) -> PriceBar:
    return PriceBar(
        symbol="AAPL",
        timestamp=datetime(2024, 1, day, tzinfo=timezone.utc),
        open=close,
        high=close,
        low=close,
        close=close,
        volume=100.0,
        provider="test",
    )


def test_sma_crossover_emits_buy_on_bullish_cross() -> None:
    strategy = SmaCrossoverStrategy(symbol="AAPL", short_window=2, long_window=3, quantity=5.0)
    state = PortfolioState(cash=10_000.0)
    strategy.on_start(state)

    bars = [_bar(10.0, 1), _bar(9.0, 2), _bar(8.0, 3), _bar(12.0, 4)]
    emitted = [strategy.on_bar(bar, state) for bar in bars]

    assert emitted[-1]
    assert emitted[-1][0].side is OrderSide.BUY
    assert emitted[-1][0].quantity == pytest.approx(5.0)


def test_sma_crossover_emits_sell_on_bearish_cross_when_holding() -> None:
    strategy = SmaCrossoverStrategy(symbol="AAPL", short_window=2, long_window=3, quantity=5.0)
    state = PortfolioState(cash=10_000.0)
    strategy.on_start(state)

    # Build an initial bullish state and mark the portfolio as invested.
    for bar in [_bar(10.0, 1), _bar(9.0, 2), _bar(8.0, 3), _bar(12.0, 4)]:
        strategy.on_bar(bar, state)
    state.positions["AAPL"] = Position(symbol="AAPL", quantity=5.0, cost_basis=12.0)

    strategy.on_bar(_bar(7.0, 5), state)
    orders = strategy.on_bar(_bar(6.0, 6), state)

    assert orders
    assert orders[0].side is OrderSide.SELL
    assert orders[0].quantity == pytest.approx(5.0)
