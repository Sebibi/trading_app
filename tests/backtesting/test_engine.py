from __future__ import annotations

from datetime import datetime, timezone

import pytest

from trading_app.backtesting.engine import BacktestEngine
from trading_app.data.schemas import PriceBar
from trading_app.execution.orders import Order, OrderSide, OrderType
from trading_app.portfolio.models import PortfolioState
from trading_app.strategies.buy_and_hold import BuyAndHoldStrategy
from trading_app.strategies.sma_crossover import SmaCrossoverStrategy

pytestmark = pytest.mark.unit


def _bar(symbol: str, close: float, day: int) -> PriceBar:
    return PriceBar(
        symbol=symbol,
        timestamp=datetime(2024, 1, day, tzinfo=timezone.utc),
        open=close,
        high=close,
        low=close,
        close=close,
        volume=100.0,
        provider="test",
    )


class _OneShotBuyStrategy:
    name = "one_shot_buy"

    def __init__(self) -> None:
        self._sent = False

    def on_start(self, state: PortfolioState) -> list[Order]:
        return []

    def on_bar(self, bar: PriceBar, state: PortfolioState) -> list[Order]:
        if self._sent:
            return []
        self._sent = True
        return [
            Order(
                symbol=bar.symbol,
                quantity=10.0,
                side=OrderSide.BUY,
                type=OrderType.MARKET,
            )
        ]

    def on_finish(self, state: PortfolioState) -> None:
        return None


class _BuyThenSellStrategy:
    name = "buy_then_sell"

    def __init__(self) -> None:
        self._step = 0

    def on_start(self, state: PortfolioState) -> list[Order]:
        return []

    def on_bar(self, bar: PriceBar, state: PortfolioState) -> list[Order]:
        if self._step == 0:
            self._step += 1
            return [
                Order(
                    symbol=bar.symbol,
                    quantity=10.0,
                    side=OrderSide.BUY,
                    type=OrderType.MARKET,
                )
            ]
        if self._step == 1:
            self._step += 1
            return [
                Order(
                    symbol=bar.symbol,
                    quantity=5.0,
                    side=OrderSide.SELL,
                    type=OrderType.MARKET,
                )
            ]
        return []

    def on_finish(self, state: PortfolioState) -> None:
        return None


def test_engine_executes_market_buy_and_updates_equity() -> None:
    bars = [_bar("AAPL", 100.0, 1), _bar("AAPL", 110.0, 2)]
    engine = BacktestEngine(strategy=_OneShotBuyStrategy())

    result = engine.run(bars, starting_cash=1_000.0)

    assert result.cash == pytest.approx(0.0)
    assert result.positions["AAPL"].quantity == pytest.approx(10.0)
    assert result.positions["AAPL"].cost_basis == pytest.approx(100.0)
    assert result.equity == pytest.approx(1_100.0)


def test_engine_executes_sell_and_keeps_remaining_position() -> None:
    bars = [_bar("MSFT", 100.0, 1), _bar("MSFT", 110.0, 2)]
    engine = BacktestEngine(strategy=_BuyThenSellStrategy())

    result = engine.run(bars, starting_cash=1_000.0)

    assert result.cash == pytest.approx(550.0)
    assert result.positions["MSFT"].quantity == pytest.approx(5.0)
    assert result.positions["MSFT"].cost_basis == pytest.approx(100.0)
    assert result.equity == pytest.approx(1_100.0)


def test_buy_and_hold_strategy_integrates_with_engine() -> None:
    bars = [_bar("NVDA", 50.0, 1), _bar("NVDA", 55.0, 2), _bar("NVDA", 60.0, 3)]
    strategy = BuyAndHoldStrategy(symbol="NVDA", quantity=10.0)
    engine = BacktestEngine(strategy=strategy)

    result = engine.run(bars, starting_cash=1_000.0)

    assert result.cash == pytest.approx(500.0)
    assert result.positions["NVDA"].quantity == pytest.approx(10.0)
    assert result.positions["NVDA"].cost_basis == pytest.approx(50.0)
    assert result.equity == pytest.approx(1_100.0)


def test_sma_crossover_strategy_integrates_with_engine() -> None:
    bars = [
        _bar("AAPL", 10.0, 1),
        _bar("AAPL", 9.0, 2),
        _bar("AAPL", 8.0, 3),
        _bar("AAPL", 12.0, 4),
        _bar("AAPL", 7.0, 5),
        _bar("AAPL", 6.0, 6),
    ]
    strategy = SmaCrossoverStrategy(symbol="AAPL", short_window=2, long_window=3, quantity=5.0)
    engine = BacktestEngine(strategy=strategy)

    result = engine.run(bars, starting_cash=1_000.0)

    assert "AAPL" not in result.positions
    assert result.cash == pytest.approx(970.0)
    assert result.equity == pytest.approx(970.0)
