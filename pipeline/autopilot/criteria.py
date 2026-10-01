"""Pass, limbo or fail for each strategy of a population, from its facts and a step's rules."""

import operator

import pandas as pd

OPS = {">=": operator.ge, ">": operator.gt, "<=": operator.le, "<": operator.lt,
       "==": operator.eq}
RANK = {"pass": 0, "limbo": 1, "fail": 2}


def holds(value: float, test: str) -> bool:
    """Whether `value` meets a test written as "<op> <number>", e.g. ">= 0.5"."""
    op, bound = test.split()
    return OPS[op](value, float(bound))


def one(value: float, rule: dict, median: float) -> str:
    """One rule's outcome for one value.

    Args:
        value: The strategy's fact.
        rule: A rule of criteria.yaml, threshold (`pass`, `limbo`) or median (`near_median`,
            `limbo_near_median`, tolerances as a fraction of |median|).
        median: The fact's median over the population judged.
    """
    if "near_median" in rule:
        gap = abs(value - median)
        if gap <= rule["near_median"] * abs(median):
            return "pass"
        if "limbo_near_median" in rule and gap <= rule["limbo_near_median"] * abs(median):
            return "limbo"
        return "fail"
    if holds(value, rule["pass"]):
        return "pass"
    return "limbo" if "limbo" in rule and holds(value, rule["limbo"]) else "fail"


def outcomes(facts: pd.DataFrame, who: list[str], rules: list[dict]) -> dict[str, tuple[str, str]]:
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
    got = {w: ("pass", []) for w in who}
    for rule in rules:
        col = wide[rule["fact"]] if rule["fact"] in wide else pd.Series(dtype=float)
        median = col.median()
        for w in who:
            value = col.get(w)
            missing = value is None or value != value
            state = "limbo" if missing else one(value, rule, median)
            if state != "pass":
                worst, why = got[w]
                got[w] = (max(worst, state, key=RANK.get),
                          why + [f"{state}: {rule['fact']}={'sin dato' if missing else value}"])
    return {w: (state, "; ".join(why)) for w, (state, why) in got.items()}
