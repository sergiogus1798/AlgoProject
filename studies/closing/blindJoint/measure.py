"""The numbers of step 20: each mother against her random trader on oos2, the SPA, and the StepM per reading."""

from typing import Any, cast
import numpy as np
import pandas as pd

from engines.inference.snooping import superior
from studies.closing.blindJoint import readings
from studies.closing.blindJoint.pieces import PIECES

YEAR = 252  # SQX's own convention (its SharpeRatio is weekday rows x sqrt(252))
# A column is flat when its std is under this fraction of the panel's largest |daily P&L|:
# an excess that is zero up to float noise (1e-17) has no variance to studentize by, and its
# Sharpe would be an enormous number made of rounding.
FLAT = 1e-9


def states(population: pd.DataFrame) -> pd.DataFrame:
    """The state words of every complete mother.

    Args:
        population: What `pieces.population` returned.

    Returns:
        Complete mothers down, pieces across.
    """
    complete = cast(pd.DataFrame, population[population["complete"]])
    return pd.DataFrame({p: complete[p].map(lambda s: s["state"]) for p in PIECES})


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
    return superior.stepm(
        cast(pd.DataFrame, excess[columns]),
        cfg["stepm"]["fwer"],
        block,
        boot["reps"],
        boot["seed"],
    )


def run(data: dict, cfg: dict) -> dict[str, Any]:
    """Everything step 20 measures.

    Args:
        data: `population` (pieces.population), and — only when the policy let step 20
            read oos2 — `panel`, `benchmark` and `mc` (inputs.random_traders); otherwise
            `refused`, the policy's text.
        cfg: What inputs.config() returned.

    Returns:
        `states`, `calls` (readings.verdicts), `named` per reading, and when the SPA ran
        `spa`, `table` (one row per complete mother: her Sharpe ratio, her mean daily
        excess over her random trader, that trader's mean day and its Monte Carlo error,
        whether the StepM over every entrant names her), `block`, `days`, `flat` and `K`.
        Also `panel` and `benchmark`, so `one.py` can draw the two equity curves. A mother
        whose excess never moves on oos2 (she did not trade) is kept out of the test: it
        has no variance to studentize by and could not be named.

        The excess is the mother's day minus the MEAN day of the random traders with her
        footprint, so the null the SPA tests is «no mother earns more than her own trades
        entered at random»: the asset's drift, her time in the market, her side, her lots
        and her costs are on both sides and cancel. The mean is simulated, and its error
        is not bootstrapped: at `benchmark.draws` it is `mc_day`, about 1/sqrt(draws) of
        the mother's own standard error (config.yaml).
    """
    got: dict[str, Any] = {
        "states": states(data["population"]),
        "refused": data.get("refused"),
    }
    if got["refused"]:
        got["named"] = {readings.label(r): None for r in readings.names()}
        got["calls"] = readings.verdicts(got["states"], got["named"])
        return got

    days, random = data["panel"], data["benchmark"]
    excess = cast(pd.DataFrame, days - random)
    flat = list(
        excess.columns[
            excess.std(ddof=1) <= FLAT * float(np.abs(days.to_numpy()).max())
        ]
    )
    tested = cast(pd.DataFrame, excess.drop(columns=flat))
    boot = cfg["bootstrap"]
    block = superior.block_length(tested)
    named = {}
    for reading in readings.names():
        pool = (
            readings.kept(got["states"], reading[0])
            if reading[1] == "supervivientes"
            else list(got["states"].index)
        )
        named[readings.label(reading)] = stepm(
            tested, [m for m in pool if m not in flat], cfg, block
        )
    everyone = named[readings.label(("ninguna", "entrantes"))]
    table = pd.DataFrame(
        {
            "sharpe": days.mean() / days.std(ddof=1) * np.sqrt(YEAR),
            "excess_day": excess.mean(),
            "random_day": random.mean(),
            "mc_day": data["mc"],
            "named_all": excess.columns.isin(everyone),
        }
    )
    drawn: dict = {}
    return {
        **got,
        "named": named,
        "calls": readings.verdicts(got["states"], named),
        "spa": superior.spa(tested, block, boot["reps"], boot["seed"], drawn),
        "spa_drawn": drawn,
        "table": table,
        "block": block,
        "days": len(excess),
        "flat": flat,
        "K": tested.shape[1],
        "panel": days,
        "benchmark": random,
    }
