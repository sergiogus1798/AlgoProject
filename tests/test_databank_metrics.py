"""The databank metrics reader: the (IS)/(OOS) block swap and the verdict summary of a split study."""

import pandas as pd
import pytest

from ui.daemon.databank import cells
from ui.daemon.databank.metrics import swap_block


def test_swap_block_recovers_oos_filed_as_is() -> None:
    """`SPP OOS` files its real numbers as `(IS)`, `(OOS)` at zero — swap to `(OOS)`."""
    frame = pd.DataFrame(
        {
            "Net profit (IS)": [100.0, 200.0],
            "Net profit (OOS)": [0.0, 0.0],
            "TimeFrame (IS)": ["H1", "H1"],
        }
    )
    got = swap_block(frame, "SPP OOS")
    assert list(got["Net profit (OOS)"]) == [100.0, 200.0]
    assert list(got["Net profit (IS)"]) == [0.0, 0.0]


def test_swap_block_recovers_is_filed_as_oos() -> None:
    """A build..oos1 databank (`CrossTF_Mothers`) filed its numbers as `(OOS)`: they are OOS1's,
    and the header must say so (owner, 2026-10-04), not «IS»."""
    frame = pd.DataFrame(
        {"Net profit (IS)": [0.0, 0.0], "Net profit (OOS)": [50.0, 75.0]}
    )
    got = swap_block(frame, "CrossTF_Mothers")
    assert list(got["Net profit (OOS1)"]) == [50.0, 75.0]
    assert list(got["Net profit (IS)"]) == [0.0, 0.0]
    assert "Net profit (OOS)" not in got


def test_swap_block_leaves_a_real_split_alone() -> None:
    """Both blocks carrying numbers is an actual IS/OOS pair, not the quirk: never touched."""
    frame = pd.DataFrame({"Net profit (IS)": [100.0], "Net profit (OOS)": [80.0]})
    got = swap_block(frame, "OOS")
    assert (got["Net profit (IS)"].iloc[0], got["Net profit (OOS)"].iloc[0]) == (
        100.0,
        80.0,
    )


def test_swap_block_leaves_true_zero_alone() -> None:
    """Neither block filled (a strategy with no trades at all) is not this quirk's business."""
    frame = pd.DataFrame({"Net profit (IS)": [0.0], "Net profit (OOS)": [0.0]})
    got = swap_block(frame, "SPP OOS")
    assert (got["Net profit (IS)"].iloc[0], got["Net profit (OOS)"].iloc[0]) == (
        0.0,
        0.0,
    )


def test_split_study_verdict_summarises_the_worst_sub(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """crossTF writes one row per timeframe and no top-level verdict; `from_csv` used to leave
    the summary column («Resumen») always None, so a table that shows only it filtered out
    every row (📓 2026-09-30, 0/105 on a real project)."""
    rows = [
        {
            "strategy": "S1",
            "identity": "id1",
            "timeframe": "M30",
            "verdict": "survives",
            "verdict_state": "",
        },
        {
            "strategy": "S1",
            "identity": "id1",
            "timeframe": "H4",
            "verdict": "fails",
            "verdict_state": "",
        },
    ]
    monkeypatch.setattr(cells.store, "rows", lambda folder: rows)
    out = cells.from_csv("crossTF", None)
    assert out["S1"]["state"] == "fail"
    assert out["S1"]["verdict"] == "fails"  # the worst sub's own word, not None
