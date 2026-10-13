"""Encargo 66 §7.1 variant A: `ALGO_AGED_EMPTY=1` empties liverun.AGED, the default is unchanged."""

import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui.daemon.launch import liverun


def test_aged_default_is_spp_and_wfm_and_the_env_empties_it(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default keeps the aged titles; the env var gives the empty set (reload restores)."""
    monkeypatch.delenv("ALGO_AGED_EMPTY", raising=False)
    default = importlib.reload(liverun).AGED
    assert default
    monkeypatch.setenv("ALGO_AGED_EMPTY", "1")
    assert importlib.reload(liverun).AGED == set()
    monkeypatch.delenv("ALGO_AGED_EMPTY")
    assert importlib.reload(liverun).AGED == default
