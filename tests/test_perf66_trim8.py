"""Encargo 66 D16: after step 8 the store is saved, checked, and only then `Results` is cut. No SQX."""

from pathlib import Path

import pandas as pd
import pytest

from pipeline.autopilot import trim
from sqx.curate import apply_verdict

POP = pd.DataFrame({"strategy": ["S_a", "S_b", "S_c"], "identity": ["a", "b", "c"],
                    "verdict": ["MANTENER", "MANTENER", apply_verdict.DROP]})


def held(*ids: str) -> pd.DataFrame:
    """What `Results` holds: one file per identity."""
    return pd.DataFrame({"strategy": [f"S_{i}" for i in ids], "identity": list(ids)})


def rig(monkeypatch: pytest.MonkeyPatch, unsaved: list[str]) -> list[str]:
    """Fake the save, the check and the cut; return the call log."""
    calls: list[str] = []
    monkeypatch.setattr(trim.save, "project", lambda *a: calls.append("save"))
    monkeypatch.setattr(trim.save, "unsaved", lambda p: calls.append("check") or unsaved)
    monkeypatch.setattr(trim.apply_verdict, "apply", lambda *a: calls.append("trim") or {"before": 3, "after": 2})
    return calls


def go(calls: list[str], path: Path, hold: pd.DataFrame = None, full: set | None = ("a", "b", "c")) -> str:
    """`trim.results` over `POP` with a harvest of `full` and a seal that logs its two calls."""
    return trim.results("P", "custodian", POP, held("a", "b", "c") if hold is None else hold, path,
                        lambda: None if full is None else set(full),
                        lambda: calls.append("seal") or (lambda: calls.append("resign")))


def test_order_is_save_check_trim(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Save, then the store check, then the cut, then the exports re-signed; only the rejected identity drops."""
    calls = rig(monkeypatch, [])
    assert go(calls, tmp_path) == "Results: 3 → 2"
    assert calls == ["save", "check", "seal", "trim", "resign"]
    assert "S_c,c,DESCARTAR" in (tmp_path / "verdict-results.csv").read_text()


def test_refuses_when_a_kept_strategy_is_unsaved(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A kept strategy (survivor or limbo: both MANTENER) not stored: a report line, no cut, no exit."""
    calls = rig(monkeypatch, ["S_b"])
    line = go(calls, tmp_path)
    assert line.startswith("RESULTS SIN RECORTAR:") and "S_b" in line
    assert calls == ["save", "check"]


def test_unsaved_of_another_run_or_rejected_never_refuse(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """`unsaved` reads every run's verdicts: a name this run did not keep (S_c rejected, S_old) cannot block."""
    calls = rig(monkeypatch, ["S_c", "S_old"])
    go(calls, tmp_path)
    assert "trim" in calls


def test_refuses_without_the_full_harvest(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """No harvest on disk, or one lacking a kept identity: refused before anything is saved."""
    calls = rig(monkeypatch, [])
    assert go(calls, tmp_path, full={"a"}).startswith("RESULTS SIN RECORTAR:")
    assert go(calls, tmp_path, full=None).startswith("RESULTS SIN RECORTAR:")
    assert calls == []


def test_a_failed_save_is_a_refusal(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """`save.project` raising does not end the workflow."""
    calls = rig(monkeypatch, [])
    monkeypatch.setattr(trim.save, "project", lambda *a: (_ for _ in ()).throw(RuntimeError("boom")))
    assert go(calls, tmp_path).startswith("RESULTS SIN RECORTAR:")


def test_empty_results_is_skipped(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """`Results` holding no file (no `identity` column) is nothing to cut, not a KeyError."""
    calls = rig(monkeypatch, [])
    assert go(calls, tmp_path, pd.DataFrame()) == "Results: nada que recortar"
    assert calls == []


def test_unsaved_over_two_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    """The real `save.unsaved` names an older run's survivor too: that is why `trim` intersects with this run."""
    monkeypatch.setattr(trim.save, "survivors", lambda p: {"i1": {"8": {"strategy": "S_old", "verdict": "MANTENER"}},
                                                          "i2": {"8": {"strategy": "S_b", "verdict": "MANTENER"}}})
    monkeypatch.setattr(trim.save.verify, "check", lambda i: ["no_sqx"])
    assert trim.save.unsaved("P") == ["S_b", "S_old"]
    assert sorted(set(trim.save.unsaved("P")) & {"S_a", "S_b"}) == ["S_b"]


def test_second_call_is_skipped(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Results already holds only survivors: nothing is saved, checked or cut."""
    calls = rig(monkeypatch, ["x"])
    assert go(calls, tmp_path, held("a", "b")) == "Results: nada que recortar"
    assert calls == []
