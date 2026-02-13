"""Basic import smoke tests."""

import pytest

from trading_app.cli.main import main

pytestmark = pytest.mark.unit


def test_cli_main_is_callable() -> None:
    assert callable(main)
