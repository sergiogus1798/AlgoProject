"""The chain's own criteria applied to a population's facts, step by step: who is left."""

import json
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

from core.datapaths import tmp_dir
from engines.market import tradelevel
from pipeline.autopilot import criteria
from studies.screening.analysis import delay
from studies.screening.falsePositives import model
from studies.screening.gate import (
    cascade,
    level0,
    level1a,
    level2,
    level3ab,
    level3c,
    measures,
)
from studies.screening.gate import (
    inputs as gate_inputs,
)
from studies.screening.gate.levels import LEVELS


def as_harvest(trades: pd.DataFrame, real: dict) -> dict[str, Any]:
    """Monkey trade lists dressed as the harvest the gate reads.

    Args:
        trades: What model.monkeys() returned.
        real: The real population's staged harvest (what inputs.load() returns as `real`).

    Returns:
        The gate's `data` dict: the real one's bars, market, costs, split and end, and the
        monkeys' own trades, curve and `Net profit [OOS]`. Nobody is `missing`: SQX's red
        flags, which drop a real strategy from the retest databank, cannot fire on a list
        Python drew.
    """
    ids = trades["identity"].unique()
    net = trades[trades["sample"] == "OOS"].groupby("identity")["Profit/Loss"].sum()
    metrics = pd.DataFrame(
        {
            "strategy": ids,
            "strategy_build": ids,
            "Net profit [OOS]": net.reindex(ids, fill_value=0.0).to_numpy(),
        },
        index=pd.Index(ids, name="identity"),
    )
    return {
        **real,
        "metrics": metrics,
        "trades": trades,
        "missing": pd.DataFrame(columns=pd.Index(["identity", "strategy_build"])),
        "curve": model.curve(trades, real["market"]["windows"]["IS"][0], real["end"]),
    }


def _plant(
    data: dict, scores: pd.DataFrame, edge: float, cfg: dict
) -> tuple[pd.DataFrame, pd.Series]:
    """The edge planted right after level 1a, everywhere a later reader looks.

    Args:
        data: The harvest, with level 1a's `oos`; changed in place.
        scores: The facts so far; level 0's net of oos1 gains the planted money.
        edge: The planted Sharpe per trade.
        cfg: The gate's config.

    Returns:
        R3's fact on the planted excess, and per identity the share of its mean excess that
        is planted. The harvest's own P/L and curve gain the same money, so the measured
        columns see the strategy every level sees.
    """
    data["bare"] = data["oos"]
    data["oos"], add = model.planted(data["oos"], edge)
    raw, out = data["trades"], data["trades"]["sample"] == "OOS"
    data["trades"] = raw.assign(
        **{
            "Profit/Loss": raw["Profit/Loss"]
            + raw["identity"].map(add).where(out, 0.0).to_numpy(float)
        }
    )
    data["curve"] = model.curve(
        data["trades"], data["market"]["windows"]["IS"][0], data["end"]
    )
    by = data["oos"].groupby("identity", sort=False)["excess"]
    scores["estaticas_value"] += (add * by.size()).reindex(scores.index)
    t = tradelevel.t_skew_kurt if cfg["drift"]["se_skew_kurt"] else tradelevel.t
    facts = pd.DataFrame(
        t(data["oos"], "excess")[["ar1"]].set_axis(list(level1a.FACTS), axis=1)
    )
    return facts, pd.Series(add / by.mean())


def _delayed(
    data: dict,
    got: pd.DataFrame,
    everyone: pd.Index,
    cfg: dict,
    share: pd.Series,
    bare: pd.DataFrame | None,
) -> pd.DataFrame:
    """Level 2's facts of a planted population: the edge is in the moved trade too.

    Args:
        data: The harvest, `oos` planted and `bare`, the table before the plant.
        got: What level 2 gave on the planted table: it reprices the moved trade from the
            bars, so its retention is bare moved / planted original.
        everyone: The population.
        cfg: The gate's config.
        share: Per identity, the planted amount over the planted mean excess.
        bare: Level 2's table on `bare` (what the unplanted population got), or None to
            run level 2 on it.

    Returns:
        `retraso_ret_min` with the plant added back to the moved mean, and `retraso_t_delta`
        of that same variant from the bare table, where original minus moved carries no plant.
    """
    # ponytail: adds planted / mean original excess over ALL trades; a variant that drops
    # trades (hold shorter than the shift) has its own mean. Exact = delay.measure taking a
    # planted `moved`, which is the gate's file.
    worst = delay.worst(pd.read_parquet(data["out"] / "retraso.parquet"))["variant"]
    if bare is None:
        level2.run({**data, "oos": data["bare"]}, everyone, cfg)
        bare = pd.read_parquet(data["out"] / "retraso.parquet")
    paired = (
        bare.set_index(["identity", "variant"])["t_delta"]
        .reindex(list(zip(worst.index, worst)))
        .to_numpy()
    )
    return pd.DataFrame(
        {
            "retraso_ret_min": got["retraso_ret_min"].reindex(worst.index) + share,
            "retraso_t_delta": paired,
        },
        index=worst.index,
    )


def _pass(
    base: dict, everyone: pd.Index, gate_cfg: dict, edge: float, cache: dict
) -> pd.DataFrame:
    """One population's facts, taking from `cache` what an earlier pass already measured and leaving there what a later one can take.

    What an edge planted after level 1a cannot move is measured once, on the unplanted pass:
    levels 0 and 1a, the moved excess and the unplanted table of level 2, `q_p` (Q is centred on the
    mean) and the monkeys of level 3c, which are the same whatever the strategy earned.
    """
    data, scores = dict(base), pd.DataFrame(index=everyone)
    pre, planted = cache.setdefault("pre", {}), edge != 0
    for _, module in LEVELS:
        if module in pre:
            got = pre[module]
            if module is level1a:
                data["oos"] = pre["oos"]
        elif module is level3c and planted and edge in cache.get("mono", {}):
            got = cache["mono"][edge]
        else:
            if module is level3ab:
                data["build"] = gate_inputs.build_pnl(data, everyone)
                if planted and "q_p" in cache:
                    data["q_p"] = cache["q_p"]
            if module is level3c and not planted:
                data["shifts"] = {
                    e: model.planted(data["oos"], e)[1] for e in cache["edges"] if e
                }
                data["shifted"] = cache["mono"] = {}
            # the build delay no fact reads: written once, on the unplanted pass
            cfg = (
                {**gate_cfg, "delay": {**gate_cfg["delay"], "on_build": False}}
                if planted and module is level2
                else gate_cfg
            )
            got = module.run(data, everyone, cfg)
            if module in (level0, level1a):
                pre[module] = got
                if module is level1a:
                    pre["oos"] = data["oos"]
            if not planted and module is level2:
                cache["delay"] = pd.read_parquet(data["out"] / "retraso.parquet")
            if not planted and module is level3ab:
                cache["q_p"] = got["q_p"]
        if planted and module is level1a:
            got, share = _plant(data, scores, edge, gate_cfg)
        if planted and module is level2:
            got = _delayed(data, got, everyone, gate_cfg, share, cache.get("delay"))
        scores = scores.join(got.reindex(everyone).astype(float))
    return scores.join(measures.table(data).astype(float)).add_prefix(cascade.PREFIX)


def facts_edges(
    data: dict,
    gate_cfg: dict,
    edges: tuple[float, ...],
    each: Callable[[float], None] = lambda edge: None,
) -> dict[float, pd.DataFrame]:
    """Step 8's facts with the cascade off, for one population and the same one with edges planted.

    Args:
        data: A staged harvest, real (inputs.load()'s `real`) or as_harvest()'s.
        gate_cfg: The gate's `inputs.config()`.
        edges: Sharpe per trade, net of costs, planted on every oos1 trade (model.planted),
            each a pass; 0 plants nothing. Only for a harvest of monkeys: the curve is rebuilt
            from closed trades. Put 0 first and every later pass takes what the edge cannot
            move from it (_pass) instead of measuring it again.
        each: Called with the edge after its pass.

    Returns:
        Edge to the facts, indexed by identity, one column per fact under the key the
        autopilot gives it (`gate.scorecard.<column>`): every level of `levels.LEVELS` in
        order, each over the whole population, and the measured columns. Nobody leaves, so
        the facts centred on the population (R5, R5d) are centred on everyone: diagnostic
        only (owner, 2026-10-07). Nothing nobody reads is kept: no distribution is recorded
        and level 3c draws only the rung `z_mono` is (`z_mono_<other rung>` is empty). The
        levels' per-trade tables go to a folder that dies with the call.

        The planted edge is a constant per trade (the mean cost it pays back included): it
        does not depend on the fill, so it survives the one-bar delay whole (_delayed).
    """
    everyone = cascade.population(data).index
    cache = {"edges": edges, "moved": {}}
    with tempfile.TemporaryDirectory(
        dir=tmp_dir()
    ) as tmp:  # off the 3.9 GB /tmp: a 10,000 build filled it (2026-10-17)
        data = {
            **data,
            "out": Path(tmp),
            "keep_draws": False,
            "rungs": (level3c.HEADLINE,),
            "moved": cache["moved"],
        }
        got = {}
        for edge in edges:
            got[edge] = _pass(data, everyone, gate_cfg, edge, cache)
            each(edge)
    return got


def facts8(data: dict, gate_cfg: dict, edge: float = 0.0) -> pd.DataFrame:
    """Step 8's facts for one population with `edge` planted: facts_edges() of one pass."""
    return facts_edges(data, gate_cfg, (edge,))[edge]


FACTS = {"8": facts8}


def walk(
    facts: dict[str, pd.DataFrame],
    who: list[str],
    steps: dict,
    tags: set[str],
    batches: int = 1,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """A population through every step of criteria.yaml, in its order.

    Args:
        facts: Step → its facts, identity x fact key, for the steps that could be computed.
        who: Everyone who enters the first step.
        steps: `steps` of criteria.yaml.
        tags: What the project is, for a rule's `by`.
        batches: B, for a per-cell rule's line (`criteria.thresholded`): the project's cell.

    Returns:
        The funnel — per step `n_in`, `pass`, `limbo`, `n_out` (pass + limbo: a limbo goes
        on) and `applied`, how many of its rules were judged — and one row per rule: `label`,
        how many of the step's entrants it ALONE leaves in pass, limbo and fail, and `died`,
        how many fall at it first, the rules taken in the file's order (the gate's cascade).
        `applied` is False where no fact for it exists. A step without facts lets everyone
        through, and from there on the counts are a ceiling, not a measurement.
    """
    alive, funnel, per_rule = list(who), [], []
    for n, spec in steps.items():
        rules = criteria.thresholded(
            criteria.resolved(spec.get("rules") or [], tags), batches
        )
        have = facts[n] if n in facts else pd.DataFrame()
        cols: dict[str, pd.Series] = {key: pd.Series(have[key]) for key in have}
        medians = pd.Series(have.reindex(alive).median())
        standing, doubt, applied = set(alive), set(), 0
        for rule in rules:
            row = {
                "step": n,
                "rule": json.dumps(rule, ensure_ascii=False),
                "label": cascade.label(rule),
                "n_in": len(alive),
                "applied": criteria.reads([rule]) <= cols.keys(),
            }
            if row["applied"]:
                said = pd.Series(
                    {w: criteria.judged(rule, cols, w, medians)[0] for w in alive},
                    dtype=object,
                )
                fell = set(pd.Index(said.index[(said == "fail").to_numpy()]))
                row |= {s: int((said == s).sum()) for s in criteria.RANK}
                row["died"] = len(standing & fell)
                standing -= fell
                doubt |= set(pd.Index(said.index[(said == "limbo").to_numpy()]))
                applied += 1
            per_rule.append(row)
        limbo = len(standing & doubt)
        funnel.append(
            {
                "step": n,
                "segment": spec.get("segment", "oos1"),
                "rules": len(rules),
                "applied": applied,
                "n_in": len(alive),
                "pass": len(standing) - limbo,
                "limbo": limbo,
                "n_out": len(standing),
            }
        )
        alive = [w for w in alive if w in standing]
    return pd.DataFrame(funnel), pd.DataFrame(per_rule)
