"""Pytest-style: a never-ready databank and a short sync end in SystemExit instead of hanging or returning."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_wait_ready_gives_up(monkeypatch: pytest.MonkeyPatch) -> None:
    """A databank that never loads ends the wait with SystemExit instead of hanging."""
    from core import worker

    monkeypatch.setattr(worker, "call", lambda *a, **k: "Error: CLI not ready.")
    monkeypatch.setattr(worker, "sleep", lambda s: None)
    monkeypatch.setattr(worker, "READY_POLLS", 3)
    try:
        worker.wait_ready("P", "D")
    except SystemExit:
        return
    raise AssertionError("wait_ready returned")


def test_synced_short_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A synctofiles that leaves fewer .sqx than expected raises, not returns."""
    from sqx.variants import execute

    monkeypatch.setattr(execute, "_call", lambda *a, **k: "ok")
    monkeypatch.setattr(execute.legmod, "bank_dir", lambda *a: tmp_path)
    monkeypatch.setattr(execute.time, "sleep", lambda s: None)
    (tmp_path / "a.sqx").touch()
    cfg = {"project": "P", "role": "x", "sync_tries": 2, "poll_seconds": 0}
    try:
        execute.synced(2, cfg, "D")
    except SystemExit:
        return
    raise AssertionError("short sync returned")
