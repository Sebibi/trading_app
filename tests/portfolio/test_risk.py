from __future__ import annotations

import pytest

from trading_app.execution.orders import Order, OrderSide, OrderType
from trading_app.portfolio.models import PortfolioState, Position
from trading_app.portfolio.risk import (
    CompositeRiskModel,
    MaxPositionSizeRiskModel,
    NoDuplicateBuyRiskModel,
)

pytestmark = pytest.mark.unit


def test_max_position_size_risk_caps_buy_quantity() -> None:
    model = MaxPositionSizeRiskModel(max_quantity=5.0)
    state = PortfolioState(
        cash=10_000.0,
        positions={"AAPL": Position(symbol="AAPL", quantity=4.0, cost_basis=100.0)},
    )
    orders = [
        Order(symbol="AAPL", quantity=3.0, side=OrderSide.BUY, type=OrderType.MARKET),
    ]

    approved = model.validate(orders, state)

    assert len(approved) == 1
    assert approved[0].quantity == pytest.approx(1.0)


def test_no_duplicate_buy_risk_filters_extra_buy_orders() -> None:
    model = NoDuplicateBuyRiskModel()
    state = PortfolioState(cash=10_000.0)
    orders = [
        Order(symbol="AAPL", quantity=1.0, side=OrderSide.BUY, type=OrderType.MARKET),
        Order(symbol="AAPL", quantity=2.0, side=OrderSide.BUY, type=OrderType.MARKET),
    ]

    approved = model.validate(orders, state)

    assert len(approved) == 1
    assert approved[0].quantity == pytest.approx(1.0)


def test_composite_risk_model_applies_models_sequentially() -> None:
    state = PortfolioState(
        cash=10_000.0,
        positions={"AAPL": Position(symbol="AAPL", quantity=4.0, cost_basis=100.0)},
    )
    model = CompositeRiskModel(
        models=[NoDuplicateBuyRiskModel(), MaxPositionSizeRiskModel(max_quantity=5.0)]
    )
    orders = [
        Order(symbol="AAPL", quantity=3.0, side=OrderSide.BUY, type=OrderType.MARKET),
        Order(symbol="AAPL", quantity=1.0, side=OrderSide.BUY, type=OrderType.MARKET),
    ]

    approved = model.validate(orders, state)

    assert approved == []
