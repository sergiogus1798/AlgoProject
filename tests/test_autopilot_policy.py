#!/usr/bin/env python3
"""Owner's 2026-10-04 decisions on the autopilot: a missing fact fails only in the two sanity rules,
steps 10-16 declare their segment, and the autopilot's entry shuts the oos2 door."""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.assetdata import AUTONOMOUS
from ledger import gate
from pipeline.autopilot import judge, run


def test_missing_is_fail_in_exactly_the_two_sanity_rules() -> None:
    """R3: presencia/sanidad `fail`, every other rule `limbo`, `pass` nowhere."""
    seen = {}
    for spec in judge.settings()["steps"].values():
        for rule in spec["rules"]:
            for r in rule.get("all", rule.get("any", [rule])):
                seen[r["fact"]] = r.get("missing", "limbo")
    assert {k for k, v in seen.items() if v == "fail"} == {
        "gate.scorecard.presencia_passed", "gate.scorecard.sanidad_passed"}
    assert "pass" not in seen.values()


def test_steps_8_to_16_declare_oos1() -> None:
    """R4: no step relies on the judge's default segment."""
    steps = judge.settings()["steps"]
    assert {n for n in steps if 8 <= int(n) <= 16 and steps[n].get("segment") != "oos1"} == set()


def test_the_autopilot_entry_shuts_the_oos2_door(monkeypatch: pytest.MonkeyPatch) -> None:
    """R2: `run.main` sets ALGO_AUTONOMOUS=1; then step 8 may not read oos2 and 19 may."""
    monkeypatch.delenv(AUTONOMOUS, raising=False)
    monkeypatch.setattr(sys, "argv", ["run", "--project", "Test_X", "--plan"])
    monkeypatch.setattr(run.tail, "inputs", lambda *a: run.tail.NOTHING)
    monkeypatch.setattr(run.plan, "plan", lambda *a: {})
    monkeypatch.setattr(run.workflow, "workflow", lambda p: {})
    run.main()
    assert os.environ[AUTONOMOUS] == "1"
    with pytest.raises(PermissionError):
        gate.allow(8, "oos2", "XAUUSD")
    gate.allow(19, "oos2", "XAUUSD")
    monkeypatch.delenv(AUTONOMOUS)
