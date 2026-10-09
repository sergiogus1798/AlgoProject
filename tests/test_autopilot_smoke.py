"""The autopilot's smoke mode: only the readability rules judge, and only on a Test_ project."""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from pipeline.autopilot import judge  # noqa: E402


def test_smoke_keeps_only_readability(monkeypatch: pytest.MonkeyPatch) -> None:
    """With `ALGO_SMOKE=1` every step's rules are a subset of `READABLE`; without it, untouched."""
    monkeypatch.delenv(judge.SMOKE, raising=False)
    full = {n: len(s.get("rules") or []) for n, s in judge.settings()["steps"].items()}
    monkeypatch.setenv(judge.SMOKE, "1")
    steps = judge.settings()["steps"]
    kept = {r["fact"] for s in steps.values() for r in s["rules"]}
    assert kept and kept <= judge.READABLE
    assert all(len(s["rules"]) <= full[n] for n, s in steps.items())
    notes = ("17", "18", "18.5", "19")      # the blind block annotates: cut null
    assert all(s.get("cut") for n, s in steps.items() if full[n] and n not in notes)
    assert all(steps[n]["cut"] is None for n in notes)


def test_smoke_refuses_a_trade_project() -> None:
    """`--smoke` on anything but a Test_ project ends before a plan is read."""
    got = subprocess.run([sys.executable, "-m", "pipeline.autopilot.run", "--project",
                          "Trade_X_Y_M30", "--smoke", "--plan"], capture_output=True, text=True,
                         cwd=Path(__file__).resolve().parents[1])
    assert got.returncode and "solo para proyectos Test_" in got.stderr
