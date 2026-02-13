"""Lightweight event bus abstraction (placeholder)."""
from __future__ import annotations

from typing import Callable, Protocol


class EventBus(Protocol):
    """Allows decoupled publishers/subscribers within the app."""

    def publish(self, topic: str, *args, **kwargs) -> None:
        ...

    def subscribe(self, topic: str, handler: Callable[..., None]) -> None:
        ...
