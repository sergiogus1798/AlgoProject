"""The proposal's stamp does not count the proposal's own ideas as spent (OPEN #101)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from studies.research.board import inputs, proposal  # noqa: E402


def test_stamp_leaves_out_its_own_idea_files(monkeypatch: pytest.MonkeyPatch) -> None:
    """The three ideas the ideaExpert filed for this proposal are not «ya van»; an older file still is."""
    row = {
        "idea": "x",
        "symbol": "XAUUSD",
        "timeframe": "H4",
        "direction": "short",
        "chosen": "no",
        "hypotheses_measured": 0,
    }
    rows = [row | {"file": "XAUUSD/new.md"}] * 3 + [row | {"file": "XAUUSD/old.md"}]
    monkeypatch.setattr(inputs.ideas, "index", lambda *a: rows)
    monkeypatch.setattr(inputs.attempts, "table", lambda *a: [])
    own = proposal.own_idea_files(
        {"ideas": [{"idea_file": "/d/AlgoData/ideas/XAUUSD/new.md"}]}
    )

    def total(m: dict) -> int:
        """Ideas counted in the memory's `spent`."""
        return sum(r["ideas"] for r in m["spent"])

    assert (total(inputs.memory()), total(inputs.memory(own))) == (4, 1)
