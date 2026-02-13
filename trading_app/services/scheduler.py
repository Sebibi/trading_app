"""Job scheduling façade (placeholder for APScheduler/celery/etc.)."""

from __future__ import annotations

from typing import Callable, Protocol


class Scheduler(Protocol):
    """Abstract scheduler for periodic or ad-hoc jobs."""

    def schedule_cron(self, name: str, cron: str, job: Callable[[], None]) -> None: ...

    def schedule_interval(self, name: str, seconds: int, job: Callable[[], None]) -> None: ...

    def cancel(self, name: str) -> None: ...
