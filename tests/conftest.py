"""Marks tests by what they need, so `pytest -m "not ui and not sqx and not slow"` filters a file."""

from functools import cache
from pathlib import Path

import pytest


@cache
def _needs(path: Path) -> tuple[bool, bool]:
    """(imports PySide6, uses live_only) for one test module, read once."""
    text = path.read_text(encoding="utf-8", errors="replace")
    return "PySide6" in text, "live_only" in text


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Add `ui` to tests of modules importing PySide6 and `sqx` to those using `live_only`."""
    for item in items:
        ui, sqx = _needs(item.path)
        if ui:
            item.add_marker(pytest.mark.ui)
        if sqx:
            item.add_marker(pytest.mark.sqx)
