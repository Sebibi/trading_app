from __future__ import annotations

from datetime import datetime, timezone

import pytest

from trading_app.backtesting.costs import BpsSlippageModel, FixedAndBpsCommissionModel
from trading_app.backtesting.engine import BacktestEngine
from trading_app.data.schemas import PriceBar
from trading_app.execution.orders import Order, OrderSide, OrderType
from trading_app.portfolio.models import PortfolioState
from trading_app.portfolio.risk import MaxPositionSizeRiskModel, NoDuplicateBuyRiskModel

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


class _BuyThenSellAllStrategy:
    name = "buy_then_sell_all"

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
                    quantity=10.0,
                    side=OrderSide.SELL,
                    type=OrderType.MARKET,
                )
            ]
        return []

    def on_finish(self, state: PortfolioState) -> None:
        return None


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


class _DuplicateBuyOnStartStrategy:
    name = "duplicate_buy_start"

    def on_start(self, state: PortfolioState) -> list[Order]:
        return [
            Order(symbol="AAPL", quantity=2.0, side=OrderSide.BUY, type=OrderType.MARKET),
            Order(symbol="AAPL", quantity=2.0, side=OrderSide.BUY, type=OrderType.MARKET),
        ]

    def on_bar(self, bar: PriceBar, state: PortfolioState) -> list[Order]:
        return []

    def on_finish(self, state: PortfolioState) -> None:
        return None


def test_engine_applies_slippage_and_commission_to_cash_and_fills() -> None:
    bars = [_bar("AAPL", 100.0, 1), _bar("AAPL", 110.0, 2)]
    strategy = _BuyThenSellAllStrategy()
    engine = BacktestEngine(
        strategy=strategy,
        commission_model=FixedAndBpsCommissionModel(fixed=1.0, bps=10.0),
        slippage_model=BpsSlippageModel(bps=10.0),
    )

    result = engine.run(bars, starting_cash=2_500.0)
    state = result.final_state

    assert len(result.fills) == 2
    assert result.fills[0].fill_price == pytest.approx(100.1)
    assert result.fills[0].commission == pytest.approx(2.001)
    assert result.fills[1].fill_price == pytest.approx(109.89)
    assert result.fills[1].commission == pytest.approx(2.0989)
    assert state.cash == pytest.approx(2_593.8001)
    assert state.equity == pytest.approx(2_593.8001)
    assert state.positions == {}


def test_engine_applies_max_position_risk_before_execution() -> None:
    bars = [_bar("MSFT", 100.0, 1), _bar("MSFT", 101.0, 2)]
    engine = BacktestEngine(
        strategy=_OneShotBuyStrategy(),
        risk_model=MaxPositionSizeRiskModel(max_quantity=3.0),
    )

    result = engine.run(bars, starting_cash=1_000.0)
    state = result.final_state

    assert len(result.orders) == 1
    assert result.orders[0].quantity == pytest.approx(3.0)
    assert len(result.fills) == 1
    assert result.fills[0].fill_qty == pytest.approx(3.0)
    assert state.positions["MSFT"].quantity == pytest.approx(3.0)
    assert state.cash == pytest.approx(700.0)


def test_engine_applies_duplicate_buy_risk_on_start_orders() -> None:
    bars = [_bar("AAPL", 100.0, 1)]
    engine = BacktestEngine(
        strategy=_DuplicateBuyOnStartStrategy(),
        risk_model=NoDuplicateBuyRiskModel(),
    )

    result = engine.run(bars, starting_cash=1_000.0)
    state = result.final_state

    assert len(result.orders) == 1
    assert len(result.fills) == 1
    assert state.positions["AAPL"].quantity == pytest.approx(2.0)
    assert state.cash == pytest.approx(800.0)
