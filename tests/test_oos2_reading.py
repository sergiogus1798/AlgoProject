"""The single oos2 reading: a known edge passes, no edge is uniform, a loss is cut, the cell's looks are counted once and capped."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ledger import cells
from pipeline.autopilot import blind, criteria, judge
from studies.optimisation.oos2Reading import measure

NULL = {"draws": 2000, "alpha": 0.05}
WEEKS, RUNS = 140, 600


def run(x: np.ndarray, seed: int = 0) -> dict:
    """measure.read on a weekly series with a fixed stream."""
    return measure.read(x, NULL, np.random.SeedSequence(seed))


def test_weekly_sums_the_difference_by_calendar_week() -> None:
    """Two whole weeks of +1 a day against a flat monkey read 7 and 7."""
    days = pd.date_range("2024-01-01", periods=14)  # a Monday: two whole weeks
    got = measure.weekly(pd.Series(1.0, index=days), pd.Series(0.0, index=days))
    assert got.tolist() == [7.0, 7.0]


def test_a_clear_edge_passes() -> None:
    """A weekly mean of +1 with sd 1 over 140 weeks passes and is not cut."""
    got = run(np.random.default_rng(1).normal(1.0, 1.0, WEEKS))
    assert (
        got["p"] <= 0.05
        and got["z"] > 0
        and got["bajo_alfa"] == 1
        and got["corta"] == 0
    )


def test_no_edge_has_a_uniform_p_over_seeds() -> None:
    """Zero-mean noise: P(p <= .05) within 3 standard errors of .05 (N=600: +-0.027), mean p within .05 of .5."""
    p = np.array(
        [
            run(np.random.default_rng(s).standard_normal(WEEKS), s)["p"]
            for s in range(RUNS)
        ]
    )
    assert abs((p <= 0.05).mean() - 0.05) < 3 * np.sqrt(0.05 * 0.95 / RUNS)
    assert abs(p.mean() - 0.5) < 0.05


def test_a_negative_sum_is_cut() -> None:
    """A weekly mean of -1 is cut and does not pass."""
    got = run(np.random.default_rng(2).normal(-1.0, 1.0, WEEKS))
    assert got["corta"] == 1 and got["z"] < 0 and got["bajo_alfa"] == 0


def test_p_error_is_the_binomial_one() -> None:
    """The published Monte Carlo error is sqrt(p(1-p)/B)."""
    got = run(np.random.default_rng(3).standard_normal(WEEKS))
    assert got["p_error_mc"] == pytest.approx(
        np.sqrt(got["p"] * (1 - got["p"]) / NULL["draws"])
    )


@pytest.fixture
def ledger(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Four projects of one cell (USATEC H1 long breakout) and one of another, counter in a temp folder."""
    row = {
        "symbol": "USATEC",
        "timeframe": "H1",
        "template": "simple:long",
        "family": "breakout",
    }
    reg = {f"Test_P{i}": row for i in range(4)} | {"Test_Q": row | {"timeframe": "M30"}}
    monkeypatch.setattr(cells.sources, "registry_projects", lambda: reg)
    monkeypatch.setattr(cells.sources, "templates", lambda: {})
    monkeypatch.setattr(cells, "FOLDER", tmp_path)
    monkeypatch.setattr(cells, "EXTRAS", tmp_path / "extras.json")


def test_a_look_counts_once_and_the_fourth_is_refused(ledger: None) -> None:
    """A look adds one; the same project again adds none; the fourth project of a cell is refused."""
    assert cells.look_oos2("Test_P0", 3) == 1
    assert cells.look_oos2("Test_P0", 3) == 1  # the same sealed look again: no new look
    assert cells.look_oos2("Test_P1", 3) == 2
    assert cells.look_oos2("Test_P2", 3) == 3
    assert cells.look_oos2("Test_P2", 3) == 3
    with pytest.raises(PermissionError, match="solo vivo"):
        cells.look_oos2("Test_P3", 3)
    assert cells.look_oos2("Test_Q", 3) == 1  # another cell is untouched


def outcome(row: dict[str, float]) -> str:
    """Step 19.5's state for one mother carrying the facts of `row`, as criteria.yaml is read."""
    frame = pd.DataFrame(
        [("m", k, v) for k, v in row.items()] + [("o", "x", 1.0)],
        columns=["who", "key", "value"],
    )
    rules = criteria.resolved(judge.settings()["steps"]["19.5"]["rules"], set())
    return criteria.outcomes(frame, ["m"], rules)["m"][0]


def test_the_tail_cuts_only_by_sign() -> None:
    """z <= 0 is cut (fail), z > 0 passes, no fact (a «solo vivo» cell, never read) is limbo; the step cuts SPP OOS."""
    assert (
        outcome({"oos2Reading.z": -0.3}) == "fail"
        and outcome({"oos2Reading.z": 0.0}) == "fail"
    )
    assert outcome({"oos2Reading.z": 0.1}) == "pass"
    assert outcome({"other.z": 5.0}) == "limbo"
    assert judge.settings()["steps"]["19.5"]["cut"] == "SPP OOS"


def test_exit_3_goes_on_with_the_label(monkeypatch: pytest.MonkeyPatch) -> None:
    """A refused look (exit 3) does not raise: the step reports «solo vivo»; any other failure raises."""
    monkeypatch.setattr(blind.chain, "command", lambda argv: (3, "x"))
    assert "solo vivo" in blind.oos2read("P")
    monkeypatch.setattr(blind.chain, "command", lambda argv: (1, "boom"))
    with pytest.raises(SystemExit):
        blind.oos2read("P")
