"""Basic import smoke tests."""

from trading_app.cli.main import main


def test_cli_main_is_callable() -> None:
    assert callable(main)
