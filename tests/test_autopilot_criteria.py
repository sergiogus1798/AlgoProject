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

T = {"fact": "t", "pass": ">= 2.33", "limbo": ">= 1.65",
     "by": {"H4+no_forex": {"pass": ">= 3"}, "H4": {"pass": ">= 2.5", "limbo": ">= 1.9"},
            "XAUUSD": {"limbo": ">= 1.0"}}}
NET = {"fact": "net", "pass": "> 0"}


def test_by_takes_the_first_entry_the_project_matches() -> None:
    """H1 forex matches nothing; H4 forex takes the H4 line; H4 gold takes the joint entry
    written first and keeps the rule's own limbo; H1 gold changes only its limbo."""
    plain = {"fact": "t", "pass": ">= 2.33", "limbo": ">= 1.65"}
    assert criteria.resolved([T, NET], {"H1", "USDJPY", "forex"}) == [plain, NET]
    assert criteria.resolved([T], {"H4", "USDJPY", "forex"})[0] == plain | T["by"]["H4"]
    assert criteria.resolved([T], {"H4", "XAUUSD", "no_forex"})[0] == plain | {"pass": ">= 3"}
    assert criteria.resolved([T], {"H1", "XAUUSD", "no_forex"})[0] == plain | {"limbo": ">= 1.0"}
    assert criteria.resolved([], {"H4"}) == [] and criteria.resolved([T], set()) == [plain]
    assert "by" in T                                              # the rules are not edited


def test_outcomes_worst_rule_and_missing_is_limbo() -> None:
    """a passes both; b is limbo on t at H1 and fails it at H4 (1.8 < 1.9); c fails net;
    d has no t: limbo, said as «sin dato»; +inf fails a "<=" rule instead of going missing."""
    facts = pd.DataFrame(
        [("a", "t", 2.6), ("a", "net", 5.0), ("b", "t", 1.8), ("b", "net", 1.0),
         ("c", "t", 3.0), ("c", "net", -1.0), ("d", "net", 2.0), ("a", "dd", float("inf"))],
        columns=["who", "key", "value"])
    who = ["a", "b", "c", "d"]
    h1 = criteria.outcomes(facts, who, criteria.resolved([T, NET], {"H1"}))
    h4 = criteria.outcomes(facts, who, criteria.resolved([T, NET], {"H4"}))
    assert [h1[w][0] for w in who] == ["pass", "limbo", "fail", "limbo"]
    assert [h4[w][0] for w in who] == ["pass", "fail", "fail", "limbo"]
    assert h1["d"][1] == "limbo: t=sin dato" and h1["a"][1] == ""
    dd = criteria.outcomes(facts, ["a"], [{"fact": "dd", "pass": "<= 1.5", "limbo": "<= 2.5"}])
    assert dd["a"][0] == "fail"


def test_tags_come_from_the_registry() -> None:
    """The newest row of the project gives timeframe, symbol and the asset's class; a project
    nobody registered has no tags, so its rules apply as written."""
    kept = registry.rows
    registry.rows = lambda: [{"name": "Test_x", "symbol": "XAUUSD", "timeframe": "H1"},
                             {"name": "Test_x", "symbol": "USDJPY", "timeframe": "H4"}]
    try:
        assert judge.tags("Test_x") == {"H4", "USDJPY", "forex"}
        assert judge.tags("Test_unknown") == set()
    finally:
        registry.rows = kept


if __name__ == "__main__":
    test_by_takes_the_first_entry_the_project_matches()
    test_outcomes_worst_rule_and_missing_is_limbo()
    test_tags_come_from_the_registry()
    print("ok")
