"""Pass, limbo or fail for each strategy of a population, from its facts and a step's rules."""

import operator
from statistics import NormalDist
from typing import Any, cast

import pandas as pd

Rule = dict[str, Any]   # a step's rule as criteria.yaml spells it: `fact`, `pass`, `missing`, or an `all`/`any` compound
OPS = {">=": operator.ge, ">": operator.gt, "<=": operator.le, "<": operator.lt,
       "==": operator.eq}
RANK = {"pass": 0, "limbo": 1, "fail": 2}
GROUPS = {"all": max, "any": min}     # a compound's outcome: its worst part, or its best


def holds(value: float, test: str) -> bool:
    """Whether `value` meets a test written as "<op> <number>", e.g. ">= 0.5"."""
    op, bound = test.split()
    return OPS[op](value, float(bound))


def one(value: float, rule: Rule, median: float) -> str:
    """One rule's outcome for one value.

    Args:
        value: The strategy's fact.
        rule: A rule of criteria.yaml, threshold (`pass`, `limbo`), median (`near_median`,
            `limbo_near_median`, tolerances as a fraction of |median|) or verdict (`is: pass`
            or `is: fail` — what a test that answers yes/no must have said, its fact being 1
            or 0). With `else: limbo` a rule of any shape never fails: not met is limbo.
        median: The fact's median over the population judged.
    """
    if "is" in rule:
        return "pass" if (value > 0) == (rule["is"] == "pass") else rule.get("else", "fail")
    if "near_median" in rule:
        gap = abs(value - median)
        if gap <= rule["near_median"] * abs(median):
            return "pass"
        if "limbo_near_median" in rule and gap <= rule["limbo_near_median"] * abs(median):
            return "limbo"
        return rule.get("else", "fail")
    if holds(value, rule["pass"]):
        return "pass"
    return "limbo" if "limbo" in rule and holds(value, rule["limbo"]) else rule.get("else", "fail")


def resolved(rules: list[Rule], tags: set[str]) -> list[Rule]:
    """A step's rules as they apply to one project: each rule's `by` folded in.

    Args:
        rules: The step's rules. One may carry `by: {<tags>: {pass: ..., limbo: ...}}`, where
            `<tags>` is one tag or several joined by "+" (all must hold), e.g. `H4` or
            `H4+no_forex`.
        tags: What the project is: its timeframe, symbol and asset class.

    Returns:
        The rules without `by`: the fields of the FIRST entry of `by` whose tags the project
        has replace the rule's own; a rule without a matching entry is as written. The parts
        of a compound (`all`, `any`) are resolved the same way.
    """
    out = []
    for rule in rules:
        extra = next((fields for key, fields in (rule.get("by") or {}).items()
                      if set(str(key).split("+")) <= tags), {})
        rule = Rule({k: v for k, v in rule.items() if k != "by"} | extra)
        out.append(rule | {g: resolved(rule[g], tags) for g in GROUPS if g in rule})
    return out


def threshold(alpha: float, batches: int) -> float:
    """Φ⁻¹(1 − alpha / B): the z a strategy must reach when B batches were screened in its cell."""
    return NormalDist().inv_cdf(1 - alpha / max(1, batches))


def per_cell(rules: list[Rule]) -> list[Rule]:
    """The rules, compounds unfolded, that declare `alpha` instead of a line."""
    return [r for rule in rules for r in ([rule] if "alpha" in rule else
                                          per_cell(rule.get("all") or rule.get("any") or []))]


def thresholded(rules: list[Rule], batches: int) -> list[Rule]:
    """The rules with each per-cell one (`alpha:` instead of `pass:`) given its line for B batches.

    Args:
        rules: A step's rules, resolved. A rule with `alpha` declares only the level; it gets
            `pass: ">= Φ⁻¹(1 − alpha / B)"`, `alpha` and `per` dropped. Compounds are walked.
        batches: B, the batches screened in the project's cell counting the current one.
    """
    out = []
    for rule in rules:
        if "alpha" in rule:
            rule = Rule({k: v for k, v in rule.items() if k not in ("alpha", "per")} | {
                "pass": f">= {threshold(rule['alpha'], batches)!r}"})
        out.append(rule | {g: thresholded(rule[g], batches) for g in GROUPS if g in rule})
    return out


def reads(rules: list[Rule]) -> set[str]:
    """Every fact the rules read, the parts of a compound included."""
    return {f for r in rules
            for f in ([r["fact"]] if "fact" in r else reads(cast(list[Rule], r.get("all") or r.get("any"))))}


def judged(rule: Rule, cols: dict[str, pd.Series], who: str, medians: pd.Series) -> tuple[str, str]:
    """One rule's outcome for one strategy, and what it read.

    Args:
        rule: A resolved rule: one fact, or a compound — `all: [rules]` is its worst part,
            `any: [rules]` its best — whose parts may be compounds too.
        cols: Fact → its value per strategy.
        who: The strategy.
        medians: Fact → its median over the population judged.

    Returns:
        (pass|limbo|fail, `fact=value`, or `all(…, …)` / `any(…, …)` of its parts). A
        missing fact goes where the rule's `missing:` says (pass|limbo|fail; limbo when it does not), inside a compound too: `any` of a pass and a missing is pass.
    """
    for group, pick in GROUPS.items():
        if group in rule:
            parts = [judged(r, cols, who, medians) for r in rule[group]]
            return (pick((state for state, _ in parts), key=RANK.__getitem__),
                    f"{group}({', '.join(said for _, said in parts)})")
    fact = rule["fact"]
    value = cols[fact].get(who) if fact in cols else None
    if value is None or value != value:
        return rule.get("missing", "limbo"), f"{fact}=sin dato"   # `missing:` is the rule's destination
    return one(value, rule, float(medians[fact])), f"{fact}={value}"


def outcomes(facts: pd.DataFrame, who: list[str], rules: list[Rule]) -> dict[str, tuple[str, str]]:
    """Every strategy's outcome: its worst rule.

    Args:
        facts: Long frame `who, key, value` restricted to the population judged.
        who: The population, one id per strategy.
        rules: The step's rules; empty passes everyone.

    Returns:
        id → (pass|limbo|fail, the rules that were not passed, "; "-joined). A strategy
        without the fact is limbo for that rule ("sin dato").
    """
    wide = facts.pivot_table(index="who", columns="key", values="value", aggfunc="first")
    cols: dict[str, pd.Series] = {str(key): cast(pd.Series, wide[key]) for key in wide}
    medians = cast(pd.Series, wide.median())
    got = {w: ("pass", []) for w in who}
    for rule in rules:
        for w in who:
            state, said = judged(rule, cols, w, medians)
            if state != "pass":
                worst, why = got[w]
                got[w] = (max(worst, state, key=RANK.__getitem__), why + [f"{state}: {said}"])
    return {w: (state, "; ".join(why)) for w, (state, why) in got.items()}
