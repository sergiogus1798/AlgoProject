"""A task's <Symbol> range never runs past the bars the registry holds (step 16.5, 2026-10-06)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqx.projects import registryxml, setups  # noqa: E402

DAY = registryxml.DAY
TASK = (
    '<Resources><Symbol name="X_M1" source="2" dateFrom="100" dateTo="900"></Symbol>'
    '<Symbol name="Y_M1" source="2" dateFrom="100" dateTo="900"></Symbol></Resources>'
)


def test_clipped_to_bars(monkeypatch: pytest.MonkeyPatch) -> None:
    """A span past the bars is cut to them; a cross-check market keeps its range, clipped to its bars."""
    monkeypatch.setattr(registryxml, "bars", lambda feed: (3 * DAY + 5, 10 * DAY + 7))
    text, n = setups.set_data_range(TASK, {"sqx_symbol": "X_M1"}, (0, 20 * DAY))
    assert n == 1
    assert (
        f'name="X_M1" source="2" dateFrom="{3 * DAY}" dateTo="{10 * DAY + 7}"' in text
    )
    assert (
        f'name="Y_M1" source="2" dateFrom="{3 * DAY}" dateTo="900"' in text
    )  # a market: its own range, clipped too


def test_inside_bars_kept(monkeypatch: pytest.MonkeyPatch) -> None:
    """A span inside the bars is written as asked."""
    monkeypatch.setattr(registryxml, "bars", lambda feed: (0, 100 * DAY))
    text, _ = setups.set_data_range(TASK, {"sqx_symbol": "X_M1"}, (2 * DAY, 9 * DAY))
    assert f'dateFrom="{2 * DAY}" dateTo="{9 * DAY}"' in text


def test_unknown_feed_unclipped(monkeypatch: pytest.MonkeyPatch) -> None:
    """A feed the registry lacks is written as asked (the start will say so itself)."""
    monkeypatch.setattr(registryxml, "bars", lambda feed: None)
    text, _ = setups.set_data_range(TASK, {"sqx_symbol": "X_M1"}, (1, 2))
    assert 'dateFrom="1" dateTo="2"' in text
