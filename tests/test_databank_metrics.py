"""The databank metrics reader: the (IS)/(OOS) block swap and the verdict summary of a split study."""

import json
from pathlib import Path

import pandas as pd
import pytest

from ui.daemon.databank import cells
from ui.daemon.databank.metrics import swap_block


def _lote_file(data: Path, root: str, project: str, lote: str, study: str, name: str,
               label: str) -> None:
    """One strategy's result inside a one-off multi-mother lote, contract-shaped enough for
    `store.slim` to read it — `<data>/<root>/<project>/<lote>/estudios/<study>/estrategias/`."""
    path = (data / root / project / lote / "estudios" / study / "estrategias" / f"{name}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"strategy": name, "identity": f"id-{name}", "config_hash": "h",
                                "computed_at": "2026-09-30T00:00:00", "study": study, "tabs": [],
                                "verdict": {"label": label, "state": "pass"}}),
                    encoding="utf-8")


def test_swap_block_recovers_oos_filed_as_is() -> None:
    """`SPP OOS` files its real numbers as `(IS)`, `(OOS)` at zero — swap to `(OOS)`."""
    frame = pd.DataFrame({"Net profit (IS)": [100.0, 200.0], "Net profit (OOS)": [0.0, 0.0],
                          "TimeFrame (IS)": ["H1", "H1"]})
    got = swap_block(frame, "SPP OOS")
    assert list(got["Net profit (OOS)"]) == [100.0, 200.0]
    assert list(got["Net profit (IS)"]) == [0.0, 0.0]


def test_swap_block_recovers_is_filed_as_oos() -> None:
    """A build-side databank (`CrossTF_Mothers`) that filed its numbers as `(OOS)` instead."""
    frame = pd.DataFrame({"Net profit (IS)": [0.0, 0.0], "Net profit (OOS)": [50.0, 75.0]})
    got = swap_block(frame, "CrossTF_Mothers")
    assert list(got["Net profit (IS)"]) == [50.0, 75.0]
    assert list(got["Net profit (OOS)"]) == [0.0, 0.0]


def test_swap_block_leaves_a_real_split_alone() -> None:
    """Both blocks carrying numbers is an actual IS/OOS pair, not the quirk: never touched."""
    frame = pd.DataFrame({"Net profit (IS)": [100.0], "Net profit (OOS)": [80.0]})
    got = swap_block(frame, "OOS")
    assert (got["Net profit (IS)"].iloc[0], got["Net profit (OOS)"].iloc[0]) == (100.0, 80.0)


def test_swap_block_leaves_true_zero_alone() -> None:
    """Neither block filled (a strategy with no trades at all) is not this quirk's business."""
    frame = pd.DataFrame({"Net profit (IS)": [0.0], "Net profit (OOS)": [0.0]})
    got = swap_block(frame, "SPP OOS")
    assert (got["Net profit (IS)"].iloc[0], got["Net profit (OOS)"].iloc[0]) == (0.0, 0.0)


def test_split_study_verdict_summarises_the_worst_sub(monkeypatch: pytest.MonkeyPatch) -> None:
    """crossTF writes one row per timeframe and no top-level verdict; `from_csv` used to leave
    the summary column («Resumen») always None, so a table that shows only it filtered out
    every row (📓 2026-09-30, 0/105 on a real project)."""
    rows = [
        {"strategy": "S1", "identity": "id1", "timeframe": "M30", "verdict": "survives",
         "verdict_state": ""},
        {"strategy": "S1", "identity": "id1", "timeframe": "H4", "verdict": "fails",
         "verdict_state": ""},
    ]
    monkeypatch.setattr(cells.store, "rows", lambda folder: rows)
    out = cells.from_csv("crossTF", None)
    assert out["S1"]["state"] == "fail"
    assert out["S1"]["verdict"] == "fails"          # the worst sub's own word, not None


def test_lotes_reads_a_one_off_multi_mother_batch(tmp_path: Path,
                                                   monkeypatch: pytest.MonkeyPatch) -> None:
    """`structure`/`atrCalculator` never write under `reports/` — `cells.lotes()` is the only
    reader that finds them, by name, project-wide (📓 2026-09-30, block G/A1's audit: the
    Cierre «Estructura» sub-panel fell back to the whole 300-row build roster for 3 real
    mothers)."""
    monkeypatch.setattr(cells, "DATA", tmp_path)
    _lote_file(tmp_path, "structural", "P", "lote1", "structure", "Strategy 1.1.1", "ok")
    got = cells.lotes("P")
    assert set(got) == {"1.1.1"}
    assert got["1.1.1"]["structure"]["verdict"] == "ok"


def test_lotes_refuses_two_lotes_of_the_same_strategy(tmp_path: Path,
                                                       monkeypatch: pytest.MonkeyPatch) -> None:
    """Two passes of the ATR batch over the same mothers (real case on `..._H1`): no entry
    beats a wrong one, same as `lote.path`'s own ambiguity refusal."""
    monkeypatch.setattr(cells, "DATA", tmp_path)
    _lote_file(tmp_path, "atrCalculator", "P", "pass1", "atrCalculator", "Strategy 1.1.1", "ok")
    _lote_file(tmp_path, "atrCalculator", "P", "pass2", "atrCalculator", "Strategy 1.1.1", "ok")
    assert cells.lotes("P") == {}
