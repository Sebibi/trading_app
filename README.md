# Trading App

Personal framework for researching, backtesting, and running low-frequency (daily/weekly/monthly) trading strategies across stocks and ETFs. Python backend powers data pipelines, strategy execution, and APIs; a TypeScript frontend (e.g., Next.js/React or SvelteKit) will surface dashboards and controls.

## Current scope
- Backend scaffolding now includes:
  - `YFinanceSource` for historical prices and simple quotes.
  - `ParquetDataStore` for local persistence of prices/quotes/news using pyarrow.
- Focus on clear separation of concerns: data ingestion/storage, strategies, backtesting/live execution, and APIs.

## Proposed backend layout
```
trading_app/
  config/            # Configuration objects
  data/              # Data schemas, ingestion pipeline, source/storage interfaces
    sources/
    storage/
  strategies/        # Strategy protocol and registry placeholder
  backtesting/       # Backtest engine + metrics stubs
  execution/         # Orders and broker abstractions
  portfolio/         # Portfolio state and risk interfaces
  services/          # Scheduler/event bus placeholders
  utils/             # Shared utilities (logging, time, etc.)
  interfaces/        # API boundary (REST/GraphQL/WebSocket)
  cli/               # CLI entrypoint stub
```

## Frontend note
A typed front-end framework such as **Next.js (React + TypeScript)** or **SvelteKit (TypeScript)** is recommended for dashboards, live charts, and strategy management. Choose based on developer preference; both integrate well with REST/GraphQL and WebSockets for live data.

## Getting started
1. Create and activate the virtual environment (already present at `.venv` if desired).
2. Install dev dependencies with uv: `uv venv .venv && source .venv/bin/activate && uv sync --group dev`.
3. Fill in remaining implementations for data sources, storage, strategies, and APIs following the scaffolding above.

## CLI workflows
- Ingest historical bars into local parquet storage:
  - `python main.py ingest-history AAPL MSFT --store-path data --start 2024-01-01 --end 2024-02-01`
- Show latest stored bar(s) for one or more symbols:
  - `python main.py show-latest-prices AAPL MSFT --store-path data --limit 1`
- Backtest dry-run (input/data check only for now):
  - `python main.py backtest-dry-run --symbol AAPL --store-path data --starting-cash 100000 --bars-limit 252`

## Testing
- Run full default suite:
  - `uv run pytest -q`
- Marker taxonomy:
  - `unit`: fast, deterministic tests with no external services.
  - `integration`: broader cross-component tests.
  - `network`: tests requiring outbound internet access.
- Run only network tests:
  - `uv run pytest -m network -q`
- Enable network-gated tests (disabled by default):
  - `RUN_NETWORK_TESTS=1 uv run pytest -m network -q`
