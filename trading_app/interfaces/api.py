"""API boundary for exposing backend functionality (REST/GraphQL/WebSocket)."""
from __future__ import annotations

from typing import Protocol


class TradingAPI(Protocol):
    """Defines how the frontend or external clients talk to the backend."""

    def start(self) -> None:
        ...

    def stop(self) -> None:
        ...
