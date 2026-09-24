"""The numbers of every cell: what it earned, and where it sits among its own timeframe's nulls."""

import numpy as np
import pandas as pd

from core import tradestore
from nulls import model, simulate, verdict


def numbers(rows: pd.DataFrame, frame: pd.DataFrame, nullcfg: dict,
            statistic: str, rung: str) -> dict:
    """One cell's statistic, its empirical p, and what there is to distrust about them.

    The statistic is priced from the bars by `nulls.simulate`, never read off SQX, because
    the cell and its nulls have to come out of the same three lines for the p to mean
    anything.

    Args:
        rows: That cell's trades, as `tradestore.block` returned them.
        frame: The bars of that cell's own timeframe.
        nullcfg: What `nulls.inputs.config` returned.
        statistic: A key of `nulls.stats.measure`.
        rung: A key of `nulls.model.RUNGS`.

    Returns:
        `trades`, `seen`, `p` and `warnings`. `p` is NaN when the cell has too few trades
        for one, which is a fact about the cell and not a missing input.

    A cell with NO trades is that fact taken to its limit: the entry condition never fired
    on that timeframe. It returns before the nulls are drawn, because pricing an empty
    trade list against the bars raises rather than returning nothing.
    """
    if rows.empty:
        return {"trades": 0, "seen": np.nan, "p": np.nan,
                "warnings": ["the strategy never traded on this timeframe"]}
    kept = simulate.fixed(rows, frame, nullcfg)
    seen = simulate.real(kept, [statistic])
    if len(rows) < nullcfg["verdict"]["min_trades"]:
        return {"trades": len(rows), "seen": seen[statistic], "p": np.nan,
                "warnings": ["too few trades for a p"]}
    drawn = simulate.nulls(kept, rung, nullcfg)
    return {"trades": len(rows), "seen": seen[statistic],
            "p": verdict.pvalue(seen[statistic], drawn[statistic], statistic),
            "warnings": verdict.distrust(kept, seen, len(rows), nullcfg)}


def panel(plan: pd.DataFrame, packed: pd.DataFrame, frames: dict, nullcfg: dict,
          cfg: dict) -> pd.DataFrame:
    """Every cell of the matrix, measured.

    Args:
        plan: What `inputs.plan` returned.
        packed: What `inputs.trades` returned.
        frames: Timeframe to bars, from `inputs.bars`.
        nullcfg: What `nulls.inputs.config` returned.
        cfg: What `inputs.config` returned.

    Returns:
        The plan with `trades`, `seen`, `p` and `warnings` joined onto it, one row per cell.
    """
    statistic, rung = cfg["verdict"]["statistic"], cfg["verdict"]["rung"]
    measured = [numbers(tradestore.block(packed, row.strategy, row.block),
                        frames[row.timeframe], nullcfg, statistic, rung)
                for row in plan.itertuples()]
    return pd.concat([plan.reset_index(drop=True), pd.DataFrame(measured)], axis=1)


def matrix(panel: pd.DataFrame, statistic: str) -> pd.DataFrame:
    """The panel as the table the study is actually read from: one row per mother.

    Args:
        panel: What `panel` returned.
        statistic: Name of the column the cells hold, for the header.

    Returns:
        Mother by `role_timeframe`, holding the statistic. The empty corners are real: a
        sibling scaled to H4 has no D1 cell, because scaling to two targets at once is not
        a thing the fabrication makes.
    """
    wide = panel.assign(cell=panel["role"] + "_" + panel["timeframe"])
    return wide.pivot_table(index="mother", columns="cell", values="seen", observed=True)
