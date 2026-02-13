"""Configuration object placeholders for the trading app.
Populate these with environment or file-based settings before runtime.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass
class DataSourceConfig:
    """Connection/configuration for a market or news data source."""

    name: str
    params: Mapping[str, Any] | None = None


@dataclass
class StorageConfig:
    """Configuration for the storage backend (filesystem, DB, object store)."""

    driver: str
    location: str
    options: Mapping[str, Any] | None = None


@dataclass
class StrategyConfig:
    """Identifies which strategy to run and with what parameters."""

    name: str
    params: Mapping[str, Any] | None = None


@dataclass
class AppConfig:
    """Root application configuration structure."""

    data_sources: Sequence[DataSourceConfig]
    storage: StorageConfig
    strategies: Sequence[StrategyConfig] | None = None
