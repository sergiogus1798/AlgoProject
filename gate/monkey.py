"""The two screens that need the null study: the monkey itself, and the family correction."""

import os

import pandas as pd

from core import fanout
from nulls import simulate, verdict
from tasks.analysis.correlations import discoveries

# What the workers read. Set by mono() before the pool is built and never written again:
# `fork` hands every worker the bars, the ATR already computed over them and the whole OOS
# table without pickling any of it. Sending them instead costs more than the nulls do.
_SHARED: dict = {}


def _one(name: str) -> dict:
    """One strategy's monkey, in a worker that inherited its inputs by fork.

    Args:
        name: The strategy's identity.

    Returns:
        Its empirical p and the correlation of the reconstruction against SQX's own P/L.
    """
    kept = simulate.fixed(_SHARED["oos"][name], _SHARED["bars"], _SHARED["cfg"])
    seen = simulate.real(kept, _SHARED["cfg"]["statistics"]["report"])
    drawn = simulate.nulls(kept, _SHARED["rung"], _SHARED["cfg"], name)
    stat = _SHARED["statistic"]
    return {"p": verdict.pvalue(seen[stat], drawn[stat], stat), "corr": kept["checks"]["corr"]}


def mono(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
    """Does this beat a random trader with the same opportunity set?

    Args:
        data: What inputs.load returned, plus `bars` and `null_cfg`.
        alive: Strategies still in the cascade.
        cfg: This screen's row of config.yaml: which statistic, which rung, which p.

    Returns:
        `value` is the empirical p of the chosen statistic under the chosen rung. Only one
        rung is run, not the four `nulls.report` runs: the gate needs one p, and the
        attribution across the ladder is a question for the strategies that survive.

        A p whose run did not reconcile against the P/L SQX reported is not read at all —
        it fails on the reconciliation, with the correlation in the note. The cost the null
        runs are charged is measured from these very trades, so the retest task's own
        spread and slippage are carried without this module knowing what they were.

        The strategies are independent by construction and are run in parallel, the ones
        with the most trades first (`core.fanout`). Each strategy's monkeys are seeded by its
        identity, so its p does not depend on which others were in the batch.
    """
    trades = data["trades"]
    oos = trades[trades["sample"] == "OOS"]
    # The gate reads one statistic and `nulls.report` reads the whole ladder, so the gate
    # asks for one: the drawdown scan and the profit factor of every null run were 46% of
    # this screen and four statistics of five were being computed and thrown away.
    null_cfg = {**data["null_cfg"],
                "statistics": {**data["null_cfg"]["statistics"], "report": [cfg["statistic"]]}}
    # Grouped once, not filtered once per strategy: the column is `object`, so the boolean
    # mask this replaces spent 4.2 s of the gate's 33 comparing strings 234 times over.
    _SHARED.update(oos=dict(tuple(oos.groupby("identity", observed=True))), bars=data["bars"],
                   cfg=null_cfg, rung=cfg["rung"], statistic=cfg["statistic"])
    # Warmed and compiled in the parent, so the fork hands every worker the same ATR array
    # and the kernel's machine code instead of each recomputing or recompiling them.
    simulate.warm(data["bars"], data["null_cfg"])
    first = next(iter(alive))
    simulate.prime(simulate.fixed(_SHARED["oos"][first], data["bars"], data["null_cfg"]),
                   data["null_cfg"])
    costs = {name: len(_SHARED["oos"][name]) for name in alive}
    got = {}
    for i, (name, one) in enumerate(fanout.run(_one, costs, os.cpu_count()), 1):
        got[name] = one
        print(f"PROGRESS {100 * i // len(alive)} mono {i}/{len(alive)} {name}", flush=True)
    frame = pd.DataFrame(got).T.reindex(alive)
    ok = (frame["p"] <= cfg["max_p"]) & (frame["corr"] >= verdict.RECONCILE_FLOOR)
    note = "reconcilia " + frame["corr"].round(4).astype(str)
    return pd.DataFrame({"value": frame["p"], "passed": ok, "note": note, "p": frame["p"]})


def familia(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
    """Of those that beat their monkey, how many would chance alone have handed over?

    Args:
        data: What inputs.load returned; `scores` carries what the earlier screens found.
        alive: Strategies still in the cascade.
        cfg: This screen's row of config.yaml.

    Returns:
        `value` is the same p the monkey screen produced and `passed` is whether it
        survives Benjamini-Hochberg over the surviving family. Soft by default: it is a
        statement about the population, and reading it as a per-strategy verdict is what
        the owner has not decided yet.
    """
    p = data["scores"]["mono_p"].reindex(alive)
    named = discoveries([{"metric": s, "p": v} for s, v in p.items()], cfg["alpha"])
    return pd.DataFrame({"value": p, "passed": p.index.isin(named),
                         "note": f"BH al {cfg['alpha']} sobre {len(p)} supervivientes"})
