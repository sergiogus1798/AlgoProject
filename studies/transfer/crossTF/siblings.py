"""What a scaled sibling adds to its mother: the monthly P/L correlation and the z beyond hers."""

from typing import Any, cast

import numpy as np
import pandas as pd

from core import tradestore

# 🔬 2026-10-02 (AlgoData/scratch/calib_step12/null12.py): what two siblings of one mother add
# beyond her is uncorrelated under the null (0.03 and 0.07), so their sum over sqrt(k) is a z.
MOST_ALIKE = 0.95


def monthly(rows: pd.DataFrame) -> pd.Series:
    """One cell's trades as monthly P/L, indexed by calendar month.

    Args:
        rows: That cell's trades, as `tradestore.block` returned them.

    Returns:
        Empty for a cell with no trades; otherwise one value per month it closed a trade in.
    """
    if rows.empty:
        return pd.Series(dtype=float)
    month = pd.to_datetime(rows["Close time"]).dt.to_period("M")
    return cast(pd.Series, rows.groupby(month)["Profit/Loss"].sum())


def beyond(panel: pd.DataFrame) -> pd.DataFrame:
    """What each scaled sibling adds to what its mother already showed, and the mother's sum.

    A sibling trades the same asset over the same years, so under no edge its z follows its
    mother's: with correlation rho, z_sibling given z_mother is N(rho z_mother, 1 - rho^2).
    `z_new` is the sibling's z with that expectation taken out and rescaled, a standard
    normal under no edge WHATEVER the mother's luck; rho is the pair's own
    `corr_vs_baseline`, kept inside [0, `MOST_ALIKE`].

    Args:
        panel: The measured cells, with `corr_vs_baseline` and the fabrication's columns.

    Returns:
        The panel with `z_new` on every scaled cell (NaN where either z is), and on each
        baseline cell, over the siblings `verdict.usable` would read: `combined_n_tested`
        (those with a `z_new`), `combined_z_new` (their sum over sqrt(n), NaN with none)
        and `combined_z_new_max`.
    """
    mother = panel[panel["role"] == "baseline"].set_index("mother")["z"]
    scaled = panel["role"] == "scaled"
    rho = panel.loc[scaled, "corr_vs_baseline"].clip(0.0, MOST_ALIKE).fillna(0.0)
    theirs = panel.loc[scaled, "mother"].map(mother).to_numpy()
    panel.loc[scaled, "z_new"] = (panel.loc[scaled, "z"] - rho * theirs) / np.sqrt(
        1 - rho**2
    )
    fair = scaled & (panel["unverified"] == 0)
    new = panel[fair].groupby("mother")["z_new"]
    summed = pd.DataFrame(
        {
            "combined_n_tested": new.count(),
            "combined_z_new": new.sum(min_count=1) / np.sqrt(new.count()),
            "combined_z_new_max": new.max(),
        }
    )
    base = panel["role"] == "baseline"
    for name in summed:
        panel.loc[base, name] = panel.loc[base, "mother"].map(summed[name]).to_numpy()
    panel.loc[base, "combined_n_tested"] = panel.loc[base, "combined_n_tested"].fillna(
        0
    )
    return panel


def correlations(plan: pd.DataFrame, packed: pd.DataFrame) -> pd.DataFrame:
    """How each cell's monthly P/L compares with its own mother's baseline (feedback §5).

    Args:
        plan: What `inputs.plan` returned.
        packed: What `inputs.trades`/`inputs.gather` returned.

    Returns:
        One row per non-baseline cell: `mother`, `timeframe`, `role`, the Pearson correlation
        of monthly P/L against the baseline of the same mother (months either side did not
        trade count as 0, not as missing — a quiet month is real information), and `months`,
        how many calendar months either side covers. NaN when fewer than two months overlap
        or exist at all: whether the timeframes are looking at the same bets, not whether
        each one individually made money, which `verdict.read` already judges.
    """
    out = []
    close = pd.to_datetime(packed["Close time"]).dt.to_period("M")
    span = pd.period_range(close.min(), close.max(), freq="M")
    for mother, rows_m in plan.groupby("mother", sort=True):
        base_row = rows_m[rows_m["role"] == "baseline"].iloc[0]
        base = monthly(tradestore.block(packed, base_row.strategy, base_row.block))
        for row in cast(Any, rows_m[rows_m["role"] != "baseline"].itertuples()):
            other = monthly(tradestore.block(packed, row.strategy, row.block))
            joined = (
                pd.concat([base, other], axis=1, join="outer").reindex(span).fillna(0.0)
            )
            n = len(joined)
            corr = (
                float(joined.iloc[:, 0].corr(joined.iloc[:, 1]))
                if n >= 2
                else float("nan")
            )
            out.append(
                {
                    "mother": mother,
                    "timeframe": row.timeframe,
                    "role": row.role,
                    "strategy": row.strategy,
                    "corr": corr,
                    "months": n,
                }
            )
    return pd.DataFrame(out)
