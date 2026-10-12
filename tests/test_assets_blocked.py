#!/usr/bin/env python3
"""An asset card with an undecided commission ends in BLOQUEADO and exit 2, never a traceback."""

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import assets


@pytest.mark.parametrize("cut", ["use_none", "segment_null", "segment_missing"])
def test_undecided_commission_blocks(cut: str, monkeypatch: pytest.MonkeyPatch,
                                     capsys: pytest.CaptureFixture) -> None:
    """USOIL's card with its commission nulled three ways: exit 2 and the word BLOQUEADO."""
    card = copy.deepcopy(assets.load("USOIL"))
    use = card["costs"]["commission"]
    seg = next(iter(card["segments"]))
    if cut == "use_none":
        use["use"] = None
    elif cut == "segment_null":
        use["use"][seg] = None
    else:
        del use["use"][seg]
    monkeypatch.setattr(assets, "load", lambda symbol: card)
    monkeypatch.setattr(sys, "argv", ["assets", "USOIL"])
    with pytest.raises(SystemExit) as stop:
        assets.main()
    assert stop.value.code == 2 and "BLOQUEADO" in capsys.readouterr().out
