# Repository Guidelines

## Project Structure & Module Organization
- Backend package lives in `trading_app/` with clear domains: `data/` (schemas, sources, storage, pipeline), `strategies/`, `backtesting/`, `execution/`, `portfolio/`, `services/`, `utils/`, `interfaces/` (API boundary), and `cli/`.
- Entry point for developers: `main.py` delegates to `trading_app/cli/main.py` (stub). Tests sit under `tests/` (currently `test_smoke.py`).
- Configuration objects reside in `trading_app/config/`; storage implementations under `trading_app/data/storage/` (e.g., `parquet_store.py`).

## Build, Test, and Development Commands
- Dependency manager: **uv**. Create venv (`uv venv .venv`) then install dev deps: `uv sync --group dev`.
- Code formatting: `uv run black .` (line length 100).
- Run tests: `pytest` (uses `tests/`).
- Linting not yet configured; add `ruff` (or similar) when ready and document its commands.

## Coding Style & Naming Conventions
- Python 3.11+ assumed; use type hints everywhere (Protocols/dataclasses already used).
- Prefer functional module boundaries over monoliths; keep files small and purpose-specific.
- Naming: modules/files are snake_case; classes are PascalCase; interfaces marked via `Protocol`; config/value objects use `dataclass`.
- Add concise docstrings for public classes/functions; keep comments minimal and purposeful.
- All new Python dependencies must be added to `pyproject.toml` (dev deps in `[dependency-groups].dev`), then synced via `uv sync`.

## Testing Guidelines
- Use `pytest`; place tests mirroring package paths (e.g., `tests/data/test_pipeline.py`).
- Name tests descriptively: `test_<behavior>`. Include regression tests when fixing bugs.
- Aim for fast, deterministic tests; when adding slow/external I/O, guard with markers (e.g., `@pytest.mark.integration`).

## Commit & Pull Request Guidelines
- Commits: present tense, concise scope (e.g., `Add backtest engine skeleton`, `Refactor data pipeline config`).
- Each PR should describe the change, testing performed (`pytest`, etc.), and any follow-ups. Include screenshots/gifs only when UI exists.
- Keep unrelated changes out of the same PR; prefer small, reviewable diffs.

## Security & Configuration Tips
- Do not hardcode secrets or API keys; load them via env vars or config files ignored by Git.
- When adding data sources/brokers, encapsulate credentials in config objects and document required env vars in `README.md`.

## Frontend Note
- Planned typed frontend (Next.js or SvelteKit). Expose backend via REST/GraphQL/WebSocket under `interfaces/api.py`; keep API shape stable once published.
