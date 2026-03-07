"""Performance metrics for backtest results."""

from __future__ import annotations

import math
import statistics
from typing import Mapping

from trading_app.backtesting.results import BacktestResult


def summarize(
    result: BacktestResult,
    *,
    periods_per_year: int = 252,
    risk_free_rate: float = 0.0,
) -> Mapping[str, float]:
    """Compute summary metrics for a completed backtest."""
    if not result.equity_curve:
        equity = result.final_state.equity if result.final_state.equity is not None else result.final_state.cash
        return {
            "total_return": 0.0,
            "cagr": 0.0,
            "max_drawdown": 0.0,
            "volatility": 0.0,
            "sharpe": 0.0,
            "initial_equity": equity,
            "final_equity": equity,
        }

    equity_values = [point.equity for point in result.equity_curve]
    initial_equity = equity_values[0]
    final_equity = equity_values[-1]
    total_return = (final_equity / initial_equity - 1.0) if initial_equity > 0 else 0.0

    periodic_returns = _periodic_returns(equity_values)
    max_drawdown = _max_drawdown(equity_values)
    volatility = _annualized_volatility(periodic_returns, periods_per_year)
    sharpe = _sharpe(periodic_returns, volatility, periods_per_year, risk_free_rate)
    cagr = _cagr(result, initial_equity, final_equity)

    return {
        "total_return": total_return,
        "cagr": cagr,
        "max_drawdown": max_drawdown,
        "volatility": volatility,
        "sharpe": sharpe,
        "initial_equity": initial_equity,
        "final_equity": final_equity,
    }


def _periodic_returns(equity_values: list[float]) -> list[float]:
    returns: list[float] = []
    for prev, curr in zip(equity_values, equity_values[1:]):
        if prev <= 0:
            continue
        returns.append(curr / prev - 1.0)
    return returns


def _max_drawdown(equity_values: list[float]) -> float:
    peak = equity_values[0]
    max_dd = 0.0
    for equity in equity_values:
        peak = max(peak, equity)
        if peak <= 0:
            continue
        drawdown = equity / peak - 1.0
        max_dd = min(max_dd, drawdown)
    return max_dd


def _annualized_volatility(periodic_returns: list[float], periods_per_year: int) -> float:
    if len(periodic_returns) < 2:
        return 0.0
    return statistics.stdev(periodic_returns) * math.sqrt(periods_per_year)


def _sharpe(
    periodic_returns: list[float],
    annualized_volatility: float,
    periods_per_year: int,
    risk_free_rate: float,
) -> float:
    if not periodic_returns or annualized_volatility <= 0:
        return 0.0
    annualized_return = statistics.mean(periodic_returns) * periods_per_year
    return (annualized_return - risk_free_rate) / annualized_volatility


def _cagr(result: BacktestResult, initial_equity: float, final_equity: float) -> float:
    if initial_equity <= 0 or len(result.equity_curve) < 2:
        return 0.0
    start = result.equity_curve[0].timestamp
    end = result.equity_curve[-1].timestamp
    elapsed_seconds = (end - start).total_seconds()
    if elapsed_seconds <= 0:
        return 0.0
    years = elapsed_seconds / (365.25 * 24 * 60 * 60)
    return (final_equity / initial_equity) ** (1.0 / years) - 1.0
