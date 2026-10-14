"""Stage B over a whole shortlist, its winner, and the same measures re-read on another stretch."""

from typing import Any

import numpy as np
import pandas as pd

from portfolio.common.construct.search import stageb, stageb_data
from portfolio.common.construct.search.stageb_data import StageBData
from portfolio.funded.rules import machine
from portfolio.funded.rules.catalog import Plan

FLAVOURS = ("D", "T1", "T2")


def rows_of(data: StageBData, members: str) -> np.ndarray:
    """A combination's member rows in `data`, from its identities joined with "+"."""
    index = {identity: row for row, identity in enumerate(data["identities"])}
    return np.array([index[m] for m in members.split("+")], dtype=np.int64)


def run(shortlisted: pd.DataFrame, data: StageBData, plan: Plan, cfg: dict,
        rng: np.random.Generator) -> dict[str, Any]:
    """Every shortlisted combination through stage B, and the one that comes out best.

    Args:
        shortlisted: `shortlist.diverse()` output (`members`, `score`, `level`, `rank`).
        data: `stageb_data.prepare()` output on the stretch the search reads.
        plan: A `catalog.plan()` dict.
        cfg: The construct config.
        rng: Source of randomness.

    Returns:
        `rows` (every figure: `stageb.evaluate()`'s rows with `members`), `table` (one row per
        combination: its stage-A `score` and `level`, `k`, the deciding `p`, the risk per
        phase kept, which Monte Carlo decided and at which length, each flavour's own lowest
        P(pass) there, and the deciding row's time and failure figures) and `winner` (the
        table row with the highest `p`, the better stage-A rank on a tie, as a dict). `p` selects
        and is never the figure to report: the highest of shortlist × settings noisy estimates
        reads high (`funded_b.build` re-draws the winner as `p_fresh`).
    """
    risk = stageb.risk_grid(plan, cfg)
    every, table = [], []
    for members in shortlisted["members"]:
        rows = stageb.evaluate(data, rows_of(data, members), plan, cfg, risk, rng)
        got = stageb.decide(rows)
        rows.insert(0, "members", members)
        every.append(rows)
        table.append({"members": members, "k": members.count("+") + 1, "p": got["p"],
                      "setting": got["setting"],
                      **{f"r_{phase}": r for phase, r in got["risk"].items()},
                      "flavour": got["flavour"], "length": got["length"],
                      **{f"p_{f}": got["by_flavour"].get(f, np.nan) for f in FLAVOURS},
                      **{k: got["figures"].get(k, np.nan)
                         for k in rows.columns if k.startswith(("p_stage", "fail_", "t_"))
                         or k == "p_open"}})
    table = pd.concat([shortlisted.reset_index(drop=True).drop(columns="members"),
                       pd.DataFrame(table)], axis=1)
    winner = table.loc[table["p"].idxmax()].to_dict() if bool(table["p"].notna().any()) else None
    return {"rows": pd.concat(every, ignore_index=True), "table": table, "winner": winner,
            "n_settings": len(risk)}


def risk_of(winner: dict, plan: Plan) -> np.ndarray:
    """The risk per phase a winner was kept at, float64 [1, phases]."""
    return np.array([[winner[f"r_{name}"] for name in stageb.judge.stage_names(plan)]])


def judged(data: StageBData, members: str, plan: Plan, cfg: dict, risk: np.ndarray,
           rng: np.random.Generator) -> dict[str, Any]:
    """One combination at one fixed risk, on another stretch: the real path and the Monte Carlos.

    Args:
        data: `stageb_data.prepare()` output on the stretch that judges.
        members: The combination, identities joined with "+".
        risk: float64 [1, phases], the setting it was chosen at.

    Returns:
        `start_p` (the share of the stretch's start days, each with a full horizon after it,
        from which the real path passes), `n_starts`, `mc_p` (the lowest P(pass) over the
        three Monte Carlos and every block length), `by_flavour` and `rows` (every figure).
    """
    idxs = rows_of(data, members)
    days = stageb_data.joint(data, idxs)
    horizon = cfg["funded"]["horizon_days"]
    starts = np.arange(0, max(len(days["closed"]) - horizon + 1, 0), dtype=np.int64)
    names = stageb.judge.stage_names(plan)
    codes = machine.sweep(days, plan, dict(zip(names, risk[0] * plan["size"])), starts, horizon)
    rows = stageb.evaluate(data, idxs, plan, cfg, risk, rng)
    return {"start_p": float((codes == 1).mean()), "n_starts": int(len(starts)),
            "mc_p": float(rows["p_pass"].min()),
            "by_flavour": rows.groupby("flavour")["p_pass"].min().to_dict(), "rows": rows}
