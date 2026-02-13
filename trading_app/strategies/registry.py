"""Registry for available strategies (placeholder)."""
from __future__ import annotations

from typing import Protocol

from trading_app.strategies.base import Strategy


class StrategyRegistry(Protocol):
    """Keeps track of named strategy instances for discovery."""

    def register(self, strategy: Strategy) -> None:
        ...

    def get(self, name: str) -> Strategy:
        ...

    def list(self) -> list[str]:
        ...
