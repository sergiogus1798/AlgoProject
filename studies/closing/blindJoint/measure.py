"""The numbers of step 20: each mother against buy and hold on oos2, the SPA, and the StepM per reading."""

import numpy as np
import pandas as pd

from engines.inference.snooping import superior
from studies.closing.blindJoint import benchmark, readings

YEAR = 252


def states(population: pd.DataFrame) -> pd.DataFrame:
    """The four state words of every complete mother.

    Args:
        population: What `pieces.population` returned.

    Returns:
        Complete mothers down, pieces across.
    """
    complete = population[population["complete"]]
    return pd.DataFrame({p: complete[p].map(lambda s: s["state"])
                         for p in ("wfc", "cscv", "marketSurfaces", "wfm")})


def stepm(excess: pd.DataFrame, columns: list[str], cfg: dict, block: int) -> list[str]:
    """What the StepM names among some of the mothers.

    Args:
        excess: The whole excess panel.
        columns: The mothers this reading counts its search over.
        cfg: What inputs.config() returned.
        block: The block length, one for every reading so they differ only in K.

    Returns:
        The names it can name at the FWER; none when there is nobody to test.
    """
    if not columns:
        return []
    boot = cfg["bootstrap"]
    return superior.stepm(excess[columns], cfg["stepm"]["fwer"], block, boot["reps"],
                          boot["seed"])


def run(data: dict, cfg: dict) -> dict:
    """Everything step 20 measures.

    Args:
        data: `population` (pieces.population), and — only when the policy let step 20
            read oos2 — `panel`, `moves` and `point_value`; otherwise `refused`, the
            policy's text.
        cfg: What inputs.config() returned.

    Returns:
        `states`, `calls` (readings.verdicts), `named` per reading, and when the SPA ran
        `spa`, `table` (one row per complete mother: lots, both Sharpe ratios, the mean
        daily excess, whether the StepM over every entrant names it), `sharpe_bh`,
        `block`, `days`, `flat` and `K`. A mother whose curve never moves on oos2 is kept
        out of the test: it has no variance to studentize by and could not be named.
    """
    got = {"states": states(data["population"]), "refused": data.get("refused")}
    if got["refused"]:
        got["named"] = {readings.label(r): None for r in readings.names()}
        got["calls"] = readings.verdicts(got["states"], got["named"])
        return got

    excess, lots = benchmark.equal_risk(data["panel"], data["moves"], data["point_value"])
    flat = list(excess.columns[excess.std(ddof=1) == 0])
    tested = excess.drop(columns=flat)
    boot = cfg["bootstrap"]
    block = superior.block_length(tested)
    named = {}
    for reading in readings.names():
        pool = (readings.kept(got["states"], reading[0]) if reading[1] == "supervivientes"
                else list(got["states"].index))
        named[readings.label(reading)] = stepm(tested, [m for m in pool if m not in flat],
                                               cfg, block)
    days = data["panel"].loc[excess.index]
    held = data["moves"].loc[excess.index] * data["point_value"]
    everyone = named[readings.label(("ninguna", "entrantes"))]
    table = pd.DataFrame({
        "lots_bh": lots, "sharpe": days.mean() / days.std(ddof=1) * np.sqrt(YEAR),
        "excess_day": excess.mean(), "named_all": excess.columns.isin(everyone)})
    return {**got, "named": named, "calls": readings.verdicts(got["states"], named),
            "spa": superior.spa(tested, block, boot["reps"], boot["seed"]),
            "table": table, "block": block, "days": len(excess), "flat": flat,
            "K": tested.shape[1],
            "sharpe_bh": float(held.mean() / held.std(ddof=1) * np.sqrt(YEAR))}
