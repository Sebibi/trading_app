from __future__ import annotations

from datetime import datetime, timezone
import statistics

import pytest

from trading_app.backtesting.metrics import summarize
from trading_app.backtesting.results import BacktestResult, EquityPoint
from trading_app.portfolio.models import PortfolioState

pytestmark = pytest.mark.unit


def _result_from_equity_curve(equity_values: list[float], years: list[int]) -> BacktestResult:
    points = [
        EquityPoint(
            timestamp=datetime(year, 1, 1, tzinfo=timezone.utc),
            equity=equity,
        )
        for year, equity in zip(years, equity_values)
    ]
    return BacktestResult(
        final_state=PortfolioState(cash=equity_values[-1], equity=equity_values[-1]),
        equity_curve=points,
        orders=[],
        fills=[],
        trade_log=[],
        bars_processed=len(points),
    )


def test_summarize_returns_zero_metrics_for_empty_curve() -> None:
    result = BacktestResult(
        final_state=PortfolioState(cash=1_000.0, equity=1_000.0),
        equity_curve=[],
        orders=[],
        fills=[],
        trade_log=[],
        bars_processed=0,
    )

    summary = summarize(result)

    assert summary["total_return"] == pytest.approx(0.0)
    assert summary["cagr"] == pytest.approx(0.0)
    assert summary["max_drawdown"] == pytest.approx(0.0)
    assert summary["volatility"] == pytest.approx(0.0)
    assert summary["sharpe"] == pytest.approx(0.0)


def test_summarize_computes_core_metrics() -> None:
    equities = [100.0, 120.0, 90.0, 110.0]
    years = [2020, 2021, 2022, 2023]
    result = _result_from_equity_curve(equities, years)

    summary = summarize(result, periods_per_year=1, risk_free_rate=0.0)

    periodic_returns = [0.2, -0.25, 110.0 / 90.0 - 1.0]
    expected_volatility = statistics.stdev(periodic_returns)
    expected_sharpe = statistics.mean(periodic_returns) / expected_volatility
    elapsed_years = (
        result.equity_curve[-1].timestamp - result.equity_curve[0].timestamp
    ).total_seconds() / (365.25 * 24 * 60 * 60)
    expected_cagr = (equities[-1] / equities[0]) ** (1.0 / elapsed_years) - 1.0

    assert summary["initial_equity"] == pytest.approx(100.0)
    assert summary["final_equity"] == pytest.approx(110.0)
    assert summary["total_return"] == pytest.approx(0.1)
    assert summary["max_drawdown"] == pytest.approx(-0.25)
    assert summary["volatility"] == pytest.approx(expected_volatility)
    assert summary["sharpe"] == pytest.approx(expected_sharpe)
    assert summary["cagr"] == pytest.approx(expected_cagr)
