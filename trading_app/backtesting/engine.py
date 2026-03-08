"""Backtesting coordinator implementation."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Sequence

from trading_app.backtesting.costs import (
    CommissionModel,
    SlippageModel,
    ZeroCommissionModel,
    ZeroSlippageModel,
)
from trading_app.backtesting.results import BacktestResult, EquityPoint, TradeRecord
from trading_app.data.schemas import PriceBar
from trading_app.execution.orders import Fill, Order, OrderSide, OrderType
from trading_app.portfolio.models import Position
from trading_app.portfolio.models import PortfolioState
from trading_app.portfolio.risk import NoOpRiskModel, RiskModel
from trading_app.strategies.base import Strategy


class BacktestEngine:
    """Runs strategies against historical data and tracks portfolio state."""

    def __init__(
        self,
        strategy: Strategy,
        *,
        risk_model: RiskModel | None = None,
        commission_model: CommissionModel | None = None,
        slippage_model: SlippageModel | None = None,
    ) -> None:
        self.strategy = strategy
        self.risk_model = risk_model or NoOpRiskModel()
        self.commission_model = commission_model or ZeroCommissionModel()
        self.slippage_model = slippage_model or ZeroSlippageModel()

    def run(
        self,
        bars: Sequence[PriceBar],
        starting_cash: float = 100_000.0,
    ) -> BacktestResult:
        """Execute a deterministic bar-by-bar market-order backtest."""
        state = PortfolioState(cash=starting_cash, equity=starting_cash)
        pending_orders = self._validate_orders(self.strategy.on_start(state), state)
        submitted_orders: list[Order] = list(pending_orders)
        fills: list[Fill] = []
        trade_log: list[TradeRecord] = []
        equity_curve: list[EquityPoint] = []
        last_close_by_symbol: dict[str, float] = {}

        for bar in bars:
            last_close_by_symbol[bar.symbol] = bar.close
            pending_orders, executed_fills, executed_trades = self._execute_orders_for_symbol(
                pending_orders,
                state,
                symbol=bar.symbol,
                fill_price=bar.close,
                fill_timestamp=bar.timestamp,
            )
            fills.extend(executed_fills)
            trade_log.extend(executed_trades)

            new_orders = self._validate_orders(self.strategy.on_bar(bar, state), state)
            submitted_orders.extend(new_orders)
            pending_orders.extend(new_orders)
            pending_orders, executed_fills, executed_trades = self._execute_orders_for_symbol(
                pending_orders,
                state,
                symbol=bar.symbol,
                fill_price=bar.close,
                fill_timestamp=bar.timestamp,
            )
            fills.extend(executed_fills)
            trade_log.extend(executed_trades)
            state.equity = self._compute_equity(state, last_close_by_symbol)
            equity_curve.append(EquityPoint(timestamp=bar.timestamp, equity=state.equity))

        self.strategy.on_finish(state)
        state.equity = self._compute_equity(state, last_close_by_symbol)
        return BacktestResult(
            final_state=state,
            equity_curve=equity_curve,
            orders=submitted_orders,
            fills=fills,
            trade_log=trade_log,
            bars_processed=len(bars),
        )

    def _validate_orders(self, orders: Iterable[Order], state: PortfolioState) -> list[Order]:
        return self.risk_model.validate(list(orders), state)

    def _execute_orders_for_symbol(
        self,
        orders: Iterable[Order],
        state: PortfolioState,
        symbol: str,
        fill_price: float,
        fill_timestamp: datetime,
    ) -> tuple[list[Order], list[Fill], list[TradeRecord]]:
        remaining: list[Order] = []
        fills: list[Fill] = []
        trades: list[TradeRecord] = []
        for order in orders:
            if order.symbol != symbol:
                remaining.append(order)
                continue
            if order.type is not OrderType.MARKET or order.quantity <= 0:
                continue
            fill, trade = self._apply_fill(
                state,
                order,
                fill_price=fill_price,
                fill_timestamp=fill_timestamp,
            )
            if fill is not None:
                fills.append(fill)
            if trade is not None:
                trades.append(trade)
        return remaining, fills, trades

    def _apply_fill(
        self,
        state: PortfolioState,
        order: Order,
        fill_price: float,
        fill_timestamp: datetime,
    ) -> tuple[Fill | None, TradeRecord | None]:
        requested_qty = order.quantity
        if order.side is OrderSide.SELL:
            existing = state.positions.get(order.symbol)
            if existing is None:
                return None, None
            requested_qty = min(order.quantity, existing.quantity)
        if requested_qty <= 0:
            return None, None

        effective_fill_price = self.slippage_model.apply(order, fill_price)
        if effective_fill_price <= 0:
            return None, None
        commission = max(
            0.0,
            self.commission_model.calculate(
                order=order,
                fill_qty=requested_qty,
                fill_price=effective_fill_price,
            ),
        )

        if order.side is OrderSide.BUY:
            filled_qty = self._apply_buy_fill(
                state,
                order.symbol,
                requested_qty,
                effective_fill_price,
                commission,
            )
        else:
            filled_qty = self._apply_sell_fill(
                state,
                order.symbol,
                requested_qty,
                effective_fill_price,
                commission,
            )
        if filled_qty <= 0:
            return None, None

        position = state.positions.get(order.symbol)
        position_after = position.quantity if position is not None else 0.0
        return (
            Fill(
                order=order,
                fill_price=effective_fill_price,
                fill_qty=filled_qty,
                commission=commission,
            ),
            TradeRecord(
                timestamp=fill_timestamp,
                symbol=order.symbol,
                side=order.side,
                quantity=filled_qty,
                price=effective_fill_price,
                commission=commission,
                cash_after=state.cash,
                position_after=position_after,
            ),
        )

    def _apply_buy_fill(
        self,
        state: PortfolioState,
        symbol: str,
        quantity: float,
        fill_price: float,
        commission: float,
    ) -> float:
        notional = quantity * fill_price
        total_cost = notional + commission
        if total_cost > state.cash:
            return 0.0

        existing = state.positions.get(symbol)
        unit_cost = total_cost / quantity
        if existing is None:
            state.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                cost_basis=unit_cost,
            )
            state.cash -= total_cost
            return quantity

        new_quantity = existing.quantity + quantity
        new_cost_basis = (
            existing.quantity * existing.cost_basis + total_cost
        ) / new_quantity
        state.positions[symbol] = Position(
            symbol=symbol,
            quantity=new_quantity,
            cost_basis=new_cost_basis,
        )
        state.cash -= total_cost
        return quantity

    def _apply_sell_fill(
        self,
        state: PortfolioState,
        symbol: str,
        quantity: float,
        fill_price: float,
        commission: float,
    ) -> float:
        existing = state.positions.get(symbol)
        if existing is None or existing.quantity <= 0:
            return 0.0

        sell_quantity = min(quantity, existing.quantity)
        if sell_quantity <= 0:
            return 0.0

        proceeds = sell_quantity * fill_price - commission
        state.cash += proceeds
        remaining_quantity = existing.quantity - sell_quantity
        if remaining_quantity <= 0:
            del state.positions[symbol]
            return sell_quantity

        state.positions[symbol] = Position(
            symbol=symbol,
            quantity=remaining_quantity,
            cost_basis=existing.cost_basis,
        )
        return sell_quantity

    def _compute_equity(
        self, state: PortfolioState, last_close_by_symbol: dict[str, float]
    ) -> float:
        equity = state.cash
        for position in state.positions.values():
            mark = last_close_by_symbol.get(position.symbol, position.cost_basis)
            equity += position.quantity * mark
        return equity
