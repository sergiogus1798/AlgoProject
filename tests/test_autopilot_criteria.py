#!/usr/bin/env python3
"""The autopilot's inference: one rule gives pass, limbo or fail; a strategy is its worst rule;
a missing fact is limbo; and a rule's `by` swaps its thresholds for the project's timeframe,
symbol or asset class without touching a rule that has none."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot import criteria, judge
from sqx.projects import registry

T = {
    "fact": "t",
    "pass": ">= 2.33",
    "limbo": ">= 1.65",
    "by": {
        "H4+no_forex": {"pass": ">= 3"},
        "H4": {"pass": ">= 2.5", "limbo": ">= 1.9"},
        "XAUUSD": {"limbo": ">= 1.0"},
    },
}
NET = {"fact": "net", "pass": "> 0"}


def test_by_takes_the_first_entry_the_project_matches() -> None:
    """H1 forex matches nothing; H4 forex takes the H4 line; H4 gold takes the joint entry
    written first and keeps the rule's own limbo; H1 gold changes only its limbo."""
    plain = {"fact": "t", "pass": ">= 2.33", "limbo": ">= 1.65"}
    assert criteria.resolved([T, NET], {"H1", "USDJPY", "forex"}) == [plain, NET]
    assert criteria.resolved([T], {"H4", "USDJPY", "forex"})[0] == plain | T["by"]["H4"]
    assert criteria.resolved([T], {"H4", "XAUUSD", "no_forex"})[0] == plain | {
        "pass": ">= 3"
    }
    assert criteria.resolved([T], {"H1", "XAUUSD", "no_forex"})[0] == plain | {
        "limbo": ">= 1.0"
    }
    assert criteria.resolved([], {"H4"}) == [] and criteria.resolved([T], set()) == [
        plain
    ]
    assert "by" in T  # the rules are not edited


def test_outcomes_worst_rule_and_missing_is_limbo() -> None:
    """a passes both; b is limbo on t at H1 and fails it at H4 (1.8 < 1.9); c fails net;
    d has no t: limbo, said as «sin dato»; +inf fails a "<=" rule instead of going missing."""
    facts = pd.DataFrame(
        [
            ("a", "t", 2.6),
            ("a", "net", 5.0),
            ("b", "t", 1.8),
            ("b", "net", 1.0),
            ("c", "t", 3.0),
            ("c", "net", -1.0),
            ("d", "net", 2.0),
            ("a", "dd", float("inf")),
        ],
        columns=["who", "key", "value"],
    )
    who = ["a", "b", "c", "d"]
    h1 = criteria.outcomes(facts, who, criteria.resolved([T, NET], {"H1"}))
    h4 = criteria.outcomes(facts, who, criteria.resolved([T, NET], {"H4"}))
    assert [h1[w][0] for w in who] == ["pass", "limbo", "fail", "limbo"]
    assert [h4[w][0] for w in who] == ["pass", "fail", "fail", "limbo"]
    assert h1["d"][1] == "limbo: t=sin dato" and h1["a"][1] == ""
    dd = criteria.outcomes(
        facts, ["a"], [{"fact": "dd", "pass": "<= 1.5", "limbo": "<= 2.5"}]
    )
    assert dd["a"][0] == "fail"


def test_tags_come_from_the_registry() -> None:
    """The newest row of the project gives timeframe, symbol and the asset's class; a project
    nobody registered has no tags, so its rules apply as written."""
    kept = registry.rows
    registry.rows = lambda: [
        {"name": "Test_x", "symbol": "XAUUSD", "timeframe": "H1"},
        {"name": "Test_x", "symbol": "USDJPY", "timeframe": "H4"},
    ]
    try:
        assert judge.tags("Test_x") == {"H4", "USDJPY", "forex"}
        assert judge.tags("Test_unknown") == set()
    finally:
        registry.rows = kept


# a: t 2.6, test said yes · b: t 1.8, test said no · c: t 3.0, no verdict · d: nothing but net
SHAPES = pd.DataFrame(
    [
        ("a", "t", 2.6),
        ("a", "ok", 1.0),
        ("b", "t", 1.8),
        ("b", "ok", 0.0),
        ("c", "t", 3.0),
        ("d", "net", 2.0),
    ],
    columns=["who", "key", "value"],
)
WHO = ["a", "b", "c", "d"]


def states(rule: dict) -> list[str]:
    """The outcome of a, b, c and d under one rule."""
    got = criteria.outcomes(SHAPES, WHO, criteria.resolved([rule], {"H1"}))
    return [got[w][0] for w in WHO]


def test_verdict_rule() -> None:
    """`is: pass` wants the test's yes (1), `is: fail` its no (0); not met is fail, or limbo
    with `else: limbo` — which does the same for a threshold; a strategy without the verdict
    is limbo."""
    assert states({"fact": "ok", "is": "pass"}) == ["pass", "fail", "limbo", "limbo"]
    assert states({"fact": "ok", "is": "fail"}) == ["fail", "pass", "limbo", "limbo"]
    assert states({"fact": "ok", "is": "pass", "else": "limbo"})[1] == "limbo"
    assert states({"fact": "t", "pass": ">= 2.33", "else": "limbo"})[:2] == [
        "pass",
        "limbo",
    ]


def test_compound_rule() -> None:
    """`all` is its worst part and `any` its best, numeric and verdict parts mixed; a missing
    part is limbo, so `any` of a pass and a missing passes; the reason names every part; a
    part's `by` is folded in and a compound's facts are all listed."""
    t, ok = (
        {"fact": "t", "pass": ">= 2.33", "limbo": ">= 1.65"},
        {"fact": "ok", "is": "pass"},
    )
    assert states({"all": [t, ok]}) == ["pass", "fail", "limbo", "limbo"]
    assert states({"any": [t, ok]}) == ["pass", "limbo", "pass", "limbo"]
    assert (
        states({"any": [{"all": [t, ok]}, {"fact": "net", "pass": "> 0"}]})[3] == "pass"
    )
    got = criteria.outcomes(SHAPES, ["b"], [{"all": [t, ok]}])
    assert got["b"] == ("fail", "fail: all(t=1.8, ok=0.0)")
    by = {"all": [t | {"by": {"H4": {"pass": ">= 3"}}}, ok]}
    assert criteria.resolved([by], {"H4"})[0]["all"][0] == t | {"pass": ">= 3"}
    assert criteria.reads([by, {"fact": "net", "pass": "> 0"}]) == {"t", "ok", "net"}


def test_per_cell_rule_is_computed_from_b_and_signed() -> None:
    """An `alpha` rule has no number in the yaml: the judge gives it Φ⁻¹(1 − alpha/B) from the
    project's B (here faked as 2) and hands the ledger the B and the line it used; a step with
    no per-cell rule signs nothing and never reads B (compounds are walked too)."""
    z = {"fact": "z", "alpha": 0.05, "per": "cell", "missing": "fail"}
    plain = {"fact": "net", "pass": "> 0"}
    real, judge.cells.batches_for = judge.cells.batches_for, lambda project: 2
    try:
        rules, signed = judge.per_cell([plain, {"all": [z, plain]}], "P")
        assert judge.per_cell([plain], "P") == ([plain], {})
    finally:
        judge.cells.batches_for = real
    assert signed["batches_screened"] == 2 and round(signed["z_min"], 3) == 1.96
    assert rules[0] == plain and rules[1]["all"][0] == {
        "fact": "z",
        "missing": "fail",
        "pass": f">= {signed['z_min']!r}",
    }


if __name__ == "__main__":
    test_by_takes_the_first_entry_the_project_matches()
    test_outcomes_worst_rule_and_missing_is_limbo()
    test_tags_come_from_the_registry()
    test_verdict_rule()
    test_compound_rule()
    test_per_cell_rule_is_computed_from_b_and_signed()
    print("ok")
