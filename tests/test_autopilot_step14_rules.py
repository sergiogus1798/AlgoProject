#!/usr/bin/env python3
"""Step 14 in criteria.yaml is a column (encargo 65 §3d, owner 2026-10-12): `rules: []`, so the
judge cuts nobody there, and the study's «Fragilidad» tab carries T1's facts alone, under the keys
`facts.flatten` gives them (the ones step 16.5's report reads)."""

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot import facts
from studies.breakage.mcRetest.contract import retention

FILE = (
    Path(__file__).resolve().parent.parent / "pipeline" / "autopilot" / "criteria.yaml"
)
STEP = yaml.safe_load(FILE.read_text(encoding="utf-8"))["steps"]["14"]


def test_step_14_judges_nothing() -> None:
    """No rules: the step records its facts and removes nobody."""
    assert STEP["rules"] == []


def test_the_tab_emits_only_t1() -> None:
    """T2 and T3 are gone: the flattened tab holds `fragilidad.t1.*` and nothing else."""
    t1 = {f"t1.{w}.{m}": 0.5 for w in ("build", "oos1") for m in ("ret_med", "f_pos")}
    emitted = {
        key
        for key, value in facts.flatten({"tabs": [retention.tab(t1)]})
        if value is not None
    }
    assert emitted == {
        f"fragilidad.t1.{w}.{m}"
        for w in ("build", "oos1")
        for m in ("ret_med", "f_pos")
    }
    assert retention.tab(None) is None


if __name__ == "__main__":
    test_step_14_judges_nothing()
    test_the_tab_emits_only_t1()
    print("ok")
