"""L2: a sweep leaves one line per value, a rerun with another config joins the first, and N moves."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ledger import study as studymod, tried, trials  # noqa: E402

S = "XAUUSD_H1_x"


@pytest.fixture(autouse=True)
def ledger(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A ledger that lives in a temporary folder."""
    monkeypatch.setattr(studymod, "ledger_file", lambda s: tmp_path / "ledger" / f"{s}.jsonl")


def l1(n: int, mean: float, sd: float) -> pd.DataFrame:
    """One L1 search of n candidates."""
    return pd.DataFrame([{"n_scored": n, "score_unit": "per_period", "sharpe_mean": mean, "sharpe_std": sd}])


def test_three_values_three_rows_one_chosen() -> None:
    """The report line says probados 3, elegido 1, and a studies() listing ignores the L2 folder."""
    sid = tried.sweep(S, "threshold", "p", ["1", "2", "3"], "t", chosen="2", why="x")
    got = tried.summary(S).set_index("search_id").loc[sid]
    assert (len(tried.read(S)), got["probados"], got["elegido"], got["cuenta"]) == (3, 3, "2", 3)
    assert studymod.studies() == []


def test_rerun_with_another_config_joins_the_first() -> None:
    """Two gate runs with two thresholds over one harvest share a search_id; an identical one adds nothing."""
    a = tried.note_run(S, "gate", "h1", "c1", "t")
    assert tried.note_run(S, "gate", "h1", "c2", "t") == a
    assert tried.note_run(S, "gate", "h1", "c2", "t") is None
    assert tried.note_run(S, "gate", "h2", "c1", "t") != a
    assert tried.summary(S).set_index("search_id").loc[a, "cuenta"] == 1


def test_n_rises_deflation_falls_and_a_look_moves_nothing() -> None:
    """Ten values raise N and widen the benchmark; a sweep with no chosen changes neither."""
    base = l1(100, 0.0, 0.05)
    n0 = trials.accumulated(base)["n"]
    tried.sweep(S, "parameter", "look", list("abcd"), "t")
    assert trials.accumulated(tried.with_sweeps(base, S))["n"] == n0
    tried.sweep(S, "parameter", "q", [str(i) for i in range(10)], "t", scores=[0.01 * i for i in range(10)],
                chosen="9")
    after = trials.accumulated(tried.with_sweeps(base, S))
    assert after["n"] == n0 + 10
    returns = pd.Series([0.001, 0.0004, -0.002, 0.0012] * 25).to_numpy()
    low = trials.deflated(returns, 0.05, n0)["dsr"]
    assert trials.deflated(returns, 0.05, after["n"])["dsr"] < low


def test_fix_never_counts() -> None:
    """A sweep repeated for a code error is written and not counted."""
    tried.sweep(S, "parameter", "q", ["1", "2"], "t", chosen="1", fix=True)
    assert len(tried.as_rows(S)) == 0 and len(tried.read(S)) == 2
