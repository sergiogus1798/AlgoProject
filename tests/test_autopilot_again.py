"""`call.again`: one retry on SQX's transient abort, and on nothing else."""

from pathlib import Path

import pytest

from pipeline.autopilot import call


def _failing(times: int, words: str, calls: list[int]) -> object:
    """Fail with `words` on the first `times` calls, then answer."""
    calls.append(1)
    if len(calls) <= times:
        raise SystemExit(words)
    return "hecho"


def test_one_abort_is_retried_and_the_rest_is_not(
    capsys: pytest.CaptureFixture,
) -> None:
    """One abort: rerun and done. Two aborts, or another failure: the step ends."""
    calls: list[int] = []
    assert (
        call.again(lambda: _failing(1, f"{call.ABORT} P con 219 de 660", calls))
        == "hecho"
    )
    assert len(calls) == 2 and "se repite una vez" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        call.again(lambda: _failing(2, call.ABORT, []))
    other: list[int] = []
    with pytest.raises(SystemExit):
        call.again(lambda: _failing(1, "paso 14: fallaron", other))
    assert len(other) == 1


def test_the_undo_removes_only_what_the_aborted_run_added(tmp_path: Path) -> None:
    """The output's new files go before the rerun; what was there, and other databanks, stay."""
    for bank, name in (("OOS", "old.sqx"), ("Results", "r.sqx")):
        (tmp_path / "databanks" / bank).mkdir(parents=True)
        (tmp_path / "databanks" / bank / name).touch()
    undo = call.keeper(
        {
            "cfx": tmp_path / "p.cfx",
            "chosen": [{"output": "OOS"}, {"output": ""}],
        }
    )
    for bank in ("OOS", "Results"):
        (tmp_path / "databanks" / bank / "new.sqx").touch()
    calls: list[int] = []
    call.again(lambda: _failing(1, call.ABORT, calls), undo)
    assert sorted(f.name for f in tmp_path.rglob("*.sqx")) == [
        "new.sqx",
        "old.sqx",
        "r.sqx",
    ]


def test_a_live_abort_reruns_in_a_new_jvm(monkeypatch: pytest.MonkeyPatch) -> None:
    """The live route's retry closes the session as a failed step and starts a new one first:
    a rerun in the same JVM aborted again (🔬 2026-10-17)."""
    from pipeline.autopilot import run

    seen: list[tuple] = []
    monkeypatch.setattr(
        run.liverun,
        "close",
        lambda role, p, failed: seen.append(("close", role, p, failed)),
    )
    monkeypatch.setattr(
        run.live, "start", lambda role, p: seen.append(("start", role, p))
    )
    actions = [{"n": "19", "kind": "sqx"}]
    undo = run.fresh({"role": "custodian"}, "Test_P", actions)
    calls: list[int] = []
    assert call.again(lambda: _failing(1, call.ABORT, calls), undo) == "hecho"
    assert [s[0] for s in seen] == ["close", "start"]
    failed = seen[0][3]
    assert failed["n"] == "19" and failed["steps"] is actions and failed["since"] > 0
