"""The numbers of the screen: the excess panel, the SPA's p-values, the StepM set, one row each."""

import numpy as np
import pandas as pd

from engines.inference.snooping import superior
from studies.screening.snoopingScreen import benchmark

YEAR = 252


def run(data: dict, cfg: dict) -> dict:
    """Everything the screen measures over one harvest.

    Args:
        data: `panel`, `moves`, `point_value` and the gate's `scores`, as report.py loads
            them.
        cfg: What inputs.config() returned.

    Returns:
        `table` — one row per paired strategy: its names, whether the gate kept it, the
        lots of buy and hold it is held against, both Sharpe ratios, the mean daily excess
        and whether the StepM names it — plus `spa`, `named`, `block`, `flat`, `K` and
        `sharpe_bh`.

        K is every strategy the harvest paired, not the gate's survivors. The gate chose
        on this same window, and a test run on what a choice kept cannot pay for the
        choice. A strategy whose curve never moves is kept out: it has no variance to
        studentize by and could not be named.
    """
    excess, lots = benchmark.equal_risk(data["panel"], data["moves"], data["point_value"])
    flat = list(excess.columns[excess.std(ddof=1) == 0])
    tested = excess.drop(columns=flat)
    boot = cfg["bootstrap"]
    block = superior.block_length(tested)
    spa = superior.spa(tested, block, boot["reps"], boot["seed"])
    named = superior.stepm(tested, cfg["stepm"]["fwer"], block, boot["reps"], boot["seed"])

    days = data["panel"].loc[excess.index]
    held = data["moves"].loc[excess.index] * data["point_value"]
    scores = data["scores"].reindex(excess.columns)
    table = pd.DataFrame({
        "strategy": scores["strategy"], "strategy_build": scores["strategy_build"],
        "gate_survives": scores["survives"].astype(bool), "lots_bh": lots,
        "sharpe": days.mean() / days.std(ddof=1) * np.sqrt(YEAR),
        "excess_day": excess.mean(),
        "superior": excess.columns.isin(named)}).rename_axis("identity")
    return {"table": table, "spa": spa, "named": named, "block": block, "flat": flat,
            "K": tested.shape[1], "days": len(excess),
            "sharpe_bh": float(held.mean() / held.std(ddof=1) * np.sqrt(YEAR))}
