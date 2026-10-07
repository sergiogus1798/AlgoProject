"""The chain's own criteria applied to a population's facts, step by step: who is left."""

import json

import pandas as pd

from pipeline.autopilot import criteria
from studies.screening.falsePositives import model
from studies.screening.gate import level0, measures

TRADES_OOS = "spread.verdict_csv.operaciones_oos"


def as_harvest(trades: pd.DataFrame, real: dict) -> dict:
    """Monkey trade lists dressed as the harvest the gate reads.

    Args:
        trades: What model.monkeys() returned.
        real: The real population's harvest (gate `inputs.load`, plus `bars` and `market`).

    Returns:
        The gate's `data` dict: the real one's bars, market, split and end, and the monkeys'
        own trades, curve and `Net profit [OOS]`. Nobody is `missing`: SQX's red flags, which
        drop a real strategy from the retest databank, cannot fire on a list Python drew.
    """
    ids = trades["identity"].unique()
    net = trades[trades["sample"] == "OOS"].groupby("identity")["Profit/Loss"].sum()
    metrics = pd.DataFrame({"strategy": ids, "strategy_build": ids,
                            "Net profit [OOS]": net.reindex(ids, fill_value=0.0).to_numpy()},
                           index=pd.Index(ids, name="identity"))
    return {**real, "metrics": metrics, "trades": trades,
            "missing": pd.DataFrame(columns=["identity", "strategy_build"]),
            "curve": model.curve(trades, real["market"]["windows"]["IS"][0], real["end"])}


def facts8(data: dict, gate_cfg: dict) -> pd.DataFrame:
    """Step 8's facts the harvest alone gives: the gate's level 0 and its measured columns.

    Args:
        data: A harvest, real (gate `inputs.load`) or as_harvest()'s.
        gate_cfg: The gate's `inputs.config()`.

    Returns:
        Indexed by identity, one column per fact under the key the autopilot gives it
        (`gate.scorecard.<column>`, and the out-of-sample trade count under its old name).
        The levels past 0 need the staged harvest (`gate.inputs.staged`: costs, the report
        folder) and are not run here: `walk` reports their rules as not applied.
    """
    scores = level0.run(data, data["metrics"].index, gate_cfg).join(measures.table(data))
    wide = scores.astype(float).add_prefix("gate.scorecard.")
    wide[TRADES_OOS] = scores["sanidad_value"].astype(float)
    return wide


FACTS = {"8": facts8}


def walk(facts: dict[str, pd.DataFrame], who: list[str], steps: dict,
         tags: set[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """A population through every step of criteria.yaml, in its order.

    Args:
        facts: Step → its facts, identity x fact key, for the steps that could be computed.
        who: Everyone who enters the first step.
        steps: `steps` of criteria.yaml.
        tags: What the project is, for a rule's `by`.

    Returns:
        The funnel — per step `n_in`, `pass`, `limbo`, `n_out` (pass + limbo: a limbo goes
        on) and `applied`, how many of its rules were judged — and one row per rule with how
        many of the step's entrants it alone leaves in pass, limbo and fail, `applied` False
        where no fact for it exists. A step without facts lets everyone through, and from
        there on the counts are a ceiling, not a measurement.
    """
    alive, funnel, per_rule = list(who), [], []
    for n, spec in steps.items():
        rules = criteria.resolved(spec.get("rules") or [], tags)
        have = set(facts[n].columns) if n in facts else set()
        applied = [r for r in rules if criteria.reads([r]) <= have]
        for rule in rules:
            if rule not in applied:
                per_rule.append({"step": n, "rule": json.dumps(rule, ensure_ascii=False),
                                 "applied": False, "n_in": len(alive)})
        got = {w: ("pass", "") for w in alive}
        if applied and alive:
            long = facts[n].loc[alive].rename_axis("who").reset_index() \
                .melt("who", var_name="key").dropna()
            got = criteria.outcomes(long, alive, applied)
            for rule in applied:
                alone = pd.Series([s for s, _ in criteria.outcomes(long, alive, [rule]).values()])
                per_rule.append({"step": n, "rule": json.dumps(rule, ensure_ascii=False),
                                 "applied": True, "n_in": len(alive),
                                 **{s: int((alone == s).sum()) for s in criteria.RANK}})
        states = pd.Series([s for s, _ in got.values()], dtype=object)
        funnel.append({"step": n, "segment": spec.get("segment", "oos1"), "rules": len(rules),
                       "applied": len(applied), "n_in": len(alive),
                       "pass": int((states == "pass").sum()),
                       "limbo": int((states == "limbo").sum())})
        alive = [w for w in alive if got[w][0] != "fail"]
        funnel[-1]["n_out"] = len(alive)
    return pd.DataFrame(funnel), pd.DataFrame(per_rule)
