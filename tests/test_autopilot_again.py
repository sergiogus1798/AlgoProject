"""`call.again`: one retry on SQX's transient abort, and on nothing else."""

import pytest

from pipeline.autopilot import call


def _failing(times: int, words: str, calls: list[int]) -> object:
    """Fail with `words` on the first `times` calls, then answer."""
    calls.append(1)
    if len(calls) <= times:
        raise SystemExit(words)
    return "hecho"


def test_one_abort_is_retried_and_the_rest_is_not(capsys: pytest.CaptureFixture) -> None:
    """One abort: rerun and done. Two aborts, or another failure: the step ends."""
    calls: list[int] = []
    assert call.again(lambda: _failing(1, f"{call.ABORT} P con 219 de 660", calls)) == "hecho"
    assert len(calls) == 2 and "se repite una vez" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        call.again(lambda: _failing(2, call.ABORT, []))
    other: list[int] = []
    with pytest.raises(SystemExit):
        call.again(lambda: _failing(1, "paso 14: fallaron", other))
    assert len(other) == 1
