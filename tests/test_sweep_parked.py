"""A Test_ parked between workflow steps is never swept; a finished one is (OPEN #116)."""

import os
import sqlite3
from collections.abc import Callable
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.projects import sweep

Rail = dict[str, list[dict[str, str]]]


def candidates(tmp_path: Path, parked: bool) -> dict[str, object]:
    """Sweep one `Test_` untouched 48 h whose rail says `parked`."""
    p = tmp_path / "user/projects/Test_X_leaseWeb"
    p.mkdir(parents=True)
    old = time.time() - 48 * 3600
    os.utime(p, (old, old))
    describe = lambda _p: {"tasks": 15, "mb": 1, "mtime": old}  # noqa: E731
    rows = sweep.candidates(
        {"custodian": tmp_path},
        {"custodian": False},
        set(),
        describe,
        lambda _n: parked,
    )
    return rows[0]


def test_parked_test_is_kept(tmp_path: Path) -> None:
    """Parked at step 13: the workflow stopped between steps, so the sweep keeps it."""
    assert candidates(tmp_path, True)["action"] == "keep"


def test_finished_or_never_started_test_is_retired(tmp_path: Path) -> None:
    """A finished one, or one that never began the workflow, has answered: it is a candidate."""
    assert candidates(tmp_path, False)["action"] == "retire"


def test_parked_reads_the_rail(monkeypatch: pytest.MonkeyPatch) -> None:
    """No step from 6 on done -> not parked (retire); step 13 done, 21 not -> parked; unreadable -> parked."""
    from ui.daemon.projects import janitor

    def rail(states: dict[str, str]) -> Callable[[str], Rail]:
        """A stand-in for `workflow()` whose rail has these step states."""
        return lambda _p: {"steps": [{"n": n, "state": s} for n, s in states.items()]}

    for states, want in (
        ({"5": "done", "6": "pending", "21": "pending"}, False),
        ({"6": "done", "13": "done", "21": "pending"}, True),
        ({"6": "done", "21": "sealed"}, False),
    ):
        monkeypatch.setattr(janitor, "workflow", rail(states))
        assert janitor.parked("Test_X") is want

    def unreadable(_p: str) -> Rail:
        """A rail whose files cannot be parsed."""
        raise ValueError("corrupt rail")

    monkeypatch.setattr(janitor, "workflow", unreadable)
    assert janitor.parked("Test_X") is True


def test_sqlite_error_counts_as_parked(monkeypatch: pytest.MonkeyPatch) -> None:
    """A rail read that dies on sqlite never opens the door to a retire."""
    from ui.daemon.projects import janitor

    def broken(_p: str) -> Rail:
        """A store that cannot be read."""
        raise sqlite3.OperationalError("locked")

    monkeypatch.setattr(janitor, "workflow", broken)
    assert janitor.parked("Test_X") is True
