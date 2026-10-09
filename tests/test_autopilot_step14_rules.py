#!/usr/bin/env python3
"""Step 14's rules in criteria.yaml (T1, T2, T3; provisional, owner 2026-10-07) through the judge's
own path (`criteria.resolved` -> `criteria.outcomes`): each rule's pass / limbo / fail, both
discard branches of T1 build, T3 never failing, a missing fact giving limbo, and every fact the
rules name being a key `facts.flatten` really gives the study's «Fragilidad» tab."""

import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot import criteria, facts
from studies.breakage.mcRetest.contract import retention

FILE = Path(__file__).resolve().parent.parent / "pipeline" / "autopilot" / "criteria.yaml"
STEP = yaml.safe_load(FILE.read_text(encoding="utf-8"))["steps"]["14"]
RULES = criteria.resolved(STEP["rules"], set())
P = "mcRetest.fragilidad."
# a strategy that passes every rule, each fact at its line; each case below changes some
GOOD = {"t1.build.ret_med": 0.6, "t1.build.f_pos": 0.9, "t1.oos1.ret_med": 0.01,
        "t2.build.ret_med_aprox": 0.6, "t3.build.ret_med": 0.8}


def state(**change: float | None) -> str:
    """The outcome of GOOD with some facts changed (`t1_build_f_pos=0.5`); None removes one."""
    got = GOOD | {{k.replace(".", "_"): k for k in GOOD}[name]: v for name, v in change.items()}
    frame = pd.DataFrame([("s", P + k, v) for k, v in got.items() if v is not None],
                         columns=["who", "key", "value"])
    return criteria.outcomes(frame, ["s"], RULES)["s"][0]


def test_at_its_lines_the_strategy_passes_and_every_rule_has_a_name() -> None:
    """Every threshold is inclusive where the plan says `>=`; four rules, each named."""
    assert state() == "pass"
    assert len(RULES) == 4 and all(r.get("name") for r in RULES)


def test_each_rule_has_its_outcomes() -> None:
    """(changes, outcome), one line of the plan's «Thresholds» each."""
    cases = [
        # T1 build: pass needs both; fail on either discard branch; limbo between
        ({"t1_build_ret_med": 0.59}, "limbo"), ({"t1_build_ret_med": 0.3}, "limbo"),
        ({"t1_build_ret_med": 0.29}, "fail"),
        ({"t1_build_f_pos": 0.89}, "limbo"), ({"t1_build_f_pos": 0.7}, "limbo"),
        ({"t1_build_f_pos": 0.69}, "fail"),
        ({"t1_build_ret_med": 0.95, "t1_build_f_pos": 0.69}, "fail"),
        ({"t1_build_ret_med": 0.29, "t1_build_f_pos": 1.0}, "fail"),
        # T1 oos1: discard only
        ({"t1_oos1_ret_med": 0.0}, "fail"), ({"t1_oos1_ret_med": -0.2}, "fail"),
        # T2 build
        ({"t2_build_ret_med_aprox": 0.59}, "limbo"), ({"t2_build_ret_med_aprox": 0.25}, "limbo"),
        ({"t2_build_ret_med_aprox": 0.24}, "fail"),
        # T3: pass or limbo, never fail
        ({"t3_build_ret_med": 0.79}, "limbo"), ({"t3_build_ret_med": -5.0}, "limbo"),
        # the worst rule wins
        ({"t3_build_ret_med": 0.1, "t2_build_ret_med_aprox": 0.1}, "fail"),
    ]
    for change, want in cases:
        assert state(**change) == want, (change, want, state(**change))


def test_a_missing_fact_is_limbo_and_never_hides_a_discard() -> None:
    """No T1 batch, an ingest without build trades, a NaN retention: limbo — unless another
    rule discards, or the other half of T1 build does."""
    for name in GOOD:
        assert state(**{name.replace(".", "_"): None}) == "limbo", name
        assert state(**{name.replace(".", "_"): float("nan")}) == "limbo", name
    assert state(t1_build_ret_med=None, t1_build_f_pos=0.5) == "fail"
    assert state(t3_build_ret_med=None, t1_oos1_ret_med=-1.0) == "fail"
    assert state(**{name.replace(".", "_"): None for name in GOOD}) == "limbo"


def test_the_rules_read_keys_the_study_really_emits() -> None:
    """Every fact a rule names is a key of the «Fragilidad» tab flattened as the judge does."""
    t1 = {f"t1.{w}.{m}": 0.5 for w in ("build", "oos1") for m in ("ret_med", "f_pos")}
    got = {"retention": {t: dict.fromkeys(retention.COLUMNS[t], 0.5) for t in ("t2", "t3")}}
    emitted = {"mcRetest." + key for key, value in
               facts.flatten({"tabs": [retention.tab(got, t1)]}) if value is not None}
    assert criteria.reads(RULES) <= emitted, criteria.reads(RULES) - emitted
    assert criteria.reads(RULES) == {P + k for k in GOOD}


if __name__ == "__main__":
    test_at_its_lines_the_strategy_passes_and_every_rule_has_a_name()
    test_each_rule_has_its_outcomes()
    test_a_missing_fact_is_limbo_and_never_hides_a_discard()
    test_the_rules_read_keys_the_study_really_emits()
    print("ok")
