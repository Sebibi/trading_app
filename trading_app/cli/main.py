"""CLI entrypoint for common local research workflows."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Sequence

from trading_app.data.sources.yfinance_source import YFinanceSource
from trading_app.data.storage.parquet_store import ParquetDataStore


def _parse_datetime(raw: str | None) -> datetime | None:
    if raw is None:
        return None
    # Accept ISO date and datetime strings.
    return datetime.fromisoformat(raw)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="trading-app")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest-history", help="Fetch and store historical bars")
    ingest.add_argument("symbols", nargs="+", help="Ticker symbols (e.g. AAPL MSFT)")
    ingest.add_argument("--store-path", default="data", help="Root path for parquet files")
    ingest.add_argument("--start", help="ISO datetime/date (inclusive)")
    ingest.add_argument("--end", help="ISO datetime/date (exclusive)")

    latest = subparsers.add_parser("show-latest-prices", help="Show latest stored bars")
    latest.add_argument("symbols", nargs="+", help="Ticker symbols")
    latest.add_argument("--store-path", default="data", help="Root path for parquet files")
    latest.add_argument("--limit", type=int, default=1, help="Bars to load per symbol")

    dry_run = subparsers.add_parser(
        "backtest-dry-run",
        help="Validate backtest inputs and print planned execution metadata",
    )
    dry_run.add_argument("--symbol", required=True, help="Ticker symbol")
    dry_run.add_argument("--store-path", default="data", help="Root path for parquet files")
    dry_run.add_argument("--starting-cash", type=float, default=100_000.0, help="Starting cash")
    dry_run.add_argument("--bars-limit", type=int, default=252, help="How many bars to inspect")

    return parser


def _handle_ingest_history(args: argparse.Namespace) -> int:
    store = ParquetDataStore(args.store_path)
    source = YFinanceSource()

    start = _parse_datetime(args.start)
    end = _parse_datetime(args.end)

    bars = list(source.fetch_history(args.symbols, start=start, end=end))
    if bars:
        store.save_prices(bars)
    print(
        f"Ingested {len(bars)} bars for {len(args.symbols)} symbol(s) into "
        f"{Path(args.store_path).resolve()}."
    )
    return 0


def _handle_show_latest_prices(args: argparse.Namespace) -> int:
    store = ParquetDataStore(args.store_path)
    any_found = False

    for symbol in args.symbols:
        bars = store.load_prices(symbol, limit=args.limit)
        if not bars:
            print(f"{symbol}: no stored prices found")
            continue
        any_found = True
        latest = bars[-1]
        print(
            f"{symbol}: {latest.timestamp.isoformat()} "
            f"O={latest.open:.4f} H={latest.high:.4f} "
            f"L={latest.low:.4f} C={latest.close:.4f} V={latest.volume}"
        )

    return 0 if any_found else 1


def _handle_backtest_dry_run(args: argparse.Namespace) -> int:
    store = ParquetDataStore(args.store_path)
    bars = store.load_prices(args.symbol, limit=args.bars_limit)
    print("Backtest dry-run")
    print(f"symbol={args.symbol}")
    print(f"bars_loaded={len(bars)}")
    print(f"starting_cash={args.starting_cash:.2f}")
    print("engine_status=not_implemented")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Parse command line arguments and execute the requested action."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "ingest-history":
        return _handle_ingest_history(args)
    if args.command == "show-latest-prices":
        return _handle_show_latest_prices(args)
    if args.command == "backtest-dry-run":
        return _handle_backtest_dry_run(args)
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
