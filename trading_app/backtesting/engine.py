"""Backtesting coordinator stub."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Sequence

from trading_app.data.schemas import PriceBar
from trading_app.execution.orders import Order, OrderSide, OrderType
from trading_app.portfolio.models import Position
from trading_app.portfolio.models import PortfolioState
from trading_app.strategies.base import Strategy


class BacktestEngine:
    """Runs strategies against historical data and tracks portfolio state."""

    def __init__(self, strategy: Strategy) -> None:
        self.strategy = strategy

    def run(self, bars: Sequence[PriceBar], starting_cash: float = 100_000.0) -> PortfolioState:
        """Execute a deterministic bar-by-bar market-order backtest."""
        state = PortfolioState(cash=starting_cash, equity=starting_cash)
        pending_orders = list(self.strategy.on_start(state))
        last_close_by_symbol: dict[str, float] = {}

        for bar in bars:
            last_close_by_symbol[bar.symbol] = bar.close
            pending_orders = self._execute_orders_for_symbol(
                pending_orders,
                state,
                symbol=bar.symbol,
                fill_price=bar.close,
            )

            new_orders = self.strategy.on_bar(bar, state)
            pending_orders.extend(new_orders)
            pending_orders = self._execute_orders_for_symbol(
                pending_orders,
                state,
                symbol=bar.symbol,
                fill_price=bar.close,
            )

        self.strategy.on_finish(state)
        state.equity = self._compute_equity(state, last_close_by_symbol)
        return state

    def _execute_orders_for_symbol(
        self,
        orders: Iterable[Order],
        state: PortfolioState,
        symbol: str,
        fill_price: float,
    ) -> list[Order]:
        remaining: list[Order] = []
        for order in orders:
            if order.symbol != symbol:
                remaining.append(order)
                continue
            if order.type is not OrderType.MARKET or order.quantity <= 0:
                continue
            self._apply_fill(state, order, fill_price)
        return remaining

    def _apply_fill(self, state: PortfolioState, order: Order, fill_price: float) -> None:
        if order.side is OrderSide.BUY:
            self._apply_buy_fill(state, order.symbol, order.quantity, fill_price)
            return
        self._apply_sell_fill(state, order.symbol, order.quantity, fill_price)

    def _apply_buy_fill(
        self, state: PortfolioState, symbol: str, quantity: float, fill_price: float
    ) -> None:
        notional = quantity * fill_price
        if notional > state.cash:
            return

        existing = state.positions.get(symbol)
        if existing is None:
            state.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                cost_basis=fill_price,
            )
            state.cash -= notional
            return

        new_quantity = existing.quantity + quantity
        new_cost_basis = (
            existing.quantity * existing.cost_basis + quantity * fill_price
        ) / new_quantity
        state.positions[symbol] = Position(
            symbol=symbol,
            quantity=new_quantity,
            cost_basis=new_cost_basis,
        )
        state.cash -= notional

    def _apply_sell_fill(
        self, state: PortfolioState, symbol: str, quantity: float, fill_price: float
    ) -> None:
        existing = state.positions.get(symbol)
        if existing is None or existing.quantity <= 0:
            return

        sell_quantity = min(quantity, existing.quantity)
        if sell_quantity <= 0:
            return

        state.cash += sell_quantity * fill_price
        remaining_quantity = existing.quantity - sell_quantity
        if remaining_quantity <= 0:
            del state.positions[symbol]
            return

        state.positions[symbol] = Position(
            symbol=symbol,
            quantity=remaining_quantity,
            cost_basis=existing.cost_basis,
        )

    def _compute_equity(
        self, state: PortfolioState, last_close_by_symbol: dict[str, float]
    ) -> float:
        equity = state.cash
        for position in state.positions.values():
            mark = last_close_by_symbol.get(position.symbol, position.cost_basis)
            equity += position.quantity * mark
        return equity
