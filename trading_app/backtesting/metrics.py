"""Performance metrics to evaluate strategies (placeholder)."""
from __future__ import annotations

from typing import Mapping, Sequence

from trading_app.data.schemas import PriceBar
from trading_app.portfolio.models import PortfolioState


def summarize(portfolio: PortfolioState, bars: Sequence[PriceBar]) -> Mapping[str, float]:
    """Compute summary statistics like CAGR, max drawdown, Sharpe."""
    raise NotImplementedError("Implement metrics calculation")
