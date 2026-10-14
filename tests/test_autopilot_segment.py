"""18.5's second judgement is signed with oos2: the plan's judge action and the ledger row it writes."""

import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot import judge, plan
from test_autopilot_tail import GIVEN, rail


def test_185_second_judgement_carries_oos2() -> None:
    """The plan judges 18.5 once, with the oos2 segment; ledger_row signs a segment override and
    falls back to criteria.yaml's segment."""
    got = plan.plan(rail(), GIVEN | {"judged": {"18.5"}})
    assert [
        a.get("segment") for a in got["do"] if a["n"] == "18.5" and a["kind"] == "judge"
    ] == ["build+oos1+oos2"]
    rows = []
    with (
        mock.patch.object(
            judge.survivors,
            "about",
            return_value={"symbol": "X", "timeframe": "H1", "family": "f"},
        ),
        mock.patch.object(judge.record, "log", lambda sid, row: rows.append(row)),
    ):
        judge.ledger_row("P", "18.5", {"segment": "build+oos1"}, 1, 1)
        judge.ledger_row(
            "P", "18.5", {"segment": "build+oos1"}, 1, 1, "build+oos1+oos2"
        )
    assert [r["segment"] for r in rows] == ["build+oos1", "build+oos1+oos2"]
