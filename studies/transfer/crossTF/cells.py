"""The numbers of every cell: what it earned, and where it sits among its own timeframe's nulls."""

import numpy as np
import pandas as pd

from core import tradestore
from core.significance import annual_sharpe
from engines.nulls import model, simulate, verdict

# 2026-09-30 (feedback §5): these two speak of a run's own reconstruction, never of the
# reading a cell is judged on -- "P saturado" fires whenever `nulls.draws` is the binding
# constraint (a config knob, not a cell fact) and "Convención intrabar" fires on every
# strategy carrying no stop or target, which is the whole cross-TF corpus today. Kept out of
# this study's warnings; `engines.nulls.verdict.distrust` still raises them for whoever else
# reads the same engine.
DROP_WARNINGS = ("P SATURADO", "CONVENCION INTRABAR")
# The owner's one Sharpe (daily P&L on trading days, x sqrt(252)), measured beside the null's
# statistics so the window can draw it; never a key of `engines.nulls.stats`.
TOTAL = "sharpe_total"


def _trusted(said: list[str]) -> list[str]:
    """`verdict.distrust`'s sentences, minus the two this study does not surface."""
    return [s for s in said if not s.upper().startswith(DROP_WARNINGS)]


def numbers(rows: pd.DataFrame, frame: pd.DataFrame, nullcfg: dict,
            statistic: str, rung: str, key: str) -> dict:
    """One cell's statistics, their empirical p, and what there is to distrust about them.

    The statistics are priced from the bars by `engines.nulls.simulate`, never read off SQX,
    because the cell and its nulls have to come out of the same three lines for the p to mean
    anything. Every one of `nullcfg["statistics"]["report"]` is measured on the same draws
    (`simulate.nulls` prices them all in one pass), so a reader that wants a statistic other
    than the headline `sharpe` costs nothing extra here — `seen_all`/`p_all` carry them all.

    Args:
        rows: That cell's trades, as `tradestore.block` returned them.
        frame: The bars of that cell's own timeframe.
        nullcfg: What `engines.nulls.inputs.config` returned.
        statistic: A key of `engines.nulls.stats.measure`; the headline `seen`/`p` this
            cell's own verdict is read on.
        rung: A key of `engines.nulls.model.RUNGS`.
        key: What identifies the cell, strategy and block; it seeds the cell's monkeys.

    Returns:
        `trades`, `seen`, `p`, `seen_all`, `p_all` and `warnings`. `p` is NaN when the cell
        has too few trades for one, which is a fact about the cell and not a missing input.
        `seen_all` also carries `sharpe_total` (`core.significance.annual_sharpe` of the
        cell's own trades, by close date), which is read and never judged: the null draws
        carry no calendar, so it has no p.

    A cell with NO trades is that fact taken to its limit: the entry condition never fired
    on that timeframe. It returns before the nulls are drawn, because pricing an empty
    trade list against the bars raises rather than returning nothing.
    """
    names = nullcfg["statistics"]["report"]
    if rows.empty:
        empty = {n: np.nan for n in names}
        return {"trades": 0, "seen": np.nan, "p": np.nan,
                "seen_all": {**empty, TOTAL: np.nan}, "p_all": empty,
                "warnings": ["the strategy never traded on this timeframe"]}
    kept = simulate.fixed(rows, frame, nullcfg)
    seen_all = {**simulate.real(kept, names),
                TOTAL: annual_sharpe(rows["Profit/Loss"].to_numpy(dtype=float), rows["Close time"])}
    if len(rows) < nullcfg["verdict"]["min_trades"]:
        p_all = {n: np.nan for n in names}
        return {"trades": len(rows), "seen": seen_all[statistic], "p": np.nan,
                "seen_all": seen_all, "p_all": p_all, "warnings": ["too few trades for a p"]}
    drawn = simulate.nulls(kept, rung, nullcfg, key)
    p_all = {n: verdict.pvalue(seen_all[n], drawn[n], n) for n in names}
    return {"trades": len(rows), "seen": seen_all[statistic], "p": p_all[statistic],
            "seen_all": seen_all, "p_all": p_all,
            "warnings": _trusted(verdict.distrust(kept, p_all, len(rows), nullcfg))}


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
    return rows.groupby(month)["Profit/Loss"].sum()


def curve(rows: pd.DataFrame, points: int = 50) -> list[float] | None:
    """One cell's equity, resampled onto a shared 0-100 progress axis.

    Args:
        rows: That cell's trades, as `tradestore.block` returned them.
        points: How many points the shared axis carries.

    Returns:
        None for a cell with fewer than two trades -- nothing to draw a line through. Progress
        rather than trade number, because siblings on different timeframes trade a different
        count and there is no shared x otherwise (the same reason `mcRetest.fragility.fan`
        uses it).
    """
    if len(rows) < 2:
        return None
    pnl = rows.sort_values("Close time")["Profit/Loss"].to_numpy(dtype=float).cumsum()
    grid = np.linspace(0.0, 1.0, points)
    return [float(v) for v in np.interp(grid, np.linspace(0.0, 1.0, len(pnl)), pnl)]


def panel(plan: pd.DataFrame, packed: pd.DataFrame, frames: dict, nullcfg: dict,
          cfg: dict) -> pd.DataFrame:
    """Every cell of the matrix, measured.

    Args:
        plan: What `inputs.plan` returned.
        packed: What `inputs.trades` returned.
        frames: Timeframe to bars, from `inputs.bars`.
        nullcfg: What `engines.nulls.inputs.config` returned.
        cfg: What `inputs.config` returned.

    Returns:
        The plan with `trades`, `seen`, `p` and `warnings` joined onto it, one row per cell.
    """
    statistic, rung = cfg["verdict"]["statistic"], cfg["verdict"]["rung"]
    measured = [numbers(tradestore.block(packed, row.strategy, row.block),
                        frames[row.timeframe], nullcfg, statistic, rung,
                        f"{row.strategy}|{row.block}")
                for row in plan.itertuples()]
    return pd.concat([plan.reset_index(drop=True), pd.DataFrame(measured)], axis=1)


def matrix(panel: pd.DataFrame, statistic: str) -> pd.DataFrame:
    """The panel as the table the study is actually read from: one row per mother.

    Args:
        panel: What `panel` returned.
        statistic: A key of `seen_all` to read; falls back to the headline `seen` column for
            an old panel computed before `seen_all` existed.

    Returns:
        Mother by `role_timeframe`, holding the statistic. The empty corners are real: a
        sibling scaled to H4 has no D1 cell, because scaling to two targets at once is not
        a thing the fabrication makes.
    """
    value = (panel["seen_all"].map(lambda d: d.get(statistic) if isinstance(d, dict) else None)
             if "seen_all" in panel else panel["seen"])
    wide = panel.assign(cell=panel["role"] + "_" + panel["timeframe"], _value=value)
    return wide.pivot_table(index="mother", columns="cell", values="_value", observed=True)


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
    for mother, rows_m in plan.groupby("mother", sort=True):
        base_row = rows_m[rows_m["role"] == "baseline"].iloc[0]
        base = monthly(tradestore.block(packed, base_row.strategy, base_row.block))
        for row in rows_m[rows_m["role"] != "baseline"].itertuples():
            other = monthly(tradestore.block(packed, row.strategy, row.block))
            joined = pd.concat([base, other], axis=1, join="outer").fillna(0.0)
            n = len(joined)
            corr = float(joined.iloc[:, 0].corr(joined.iloc[:, 1])) if n >= 2 else float("nan")
            out.append({"mother": mother, "timeframe": row.timeframe, "role": row.role,
                        "strategy": row.strategy, "corr": corr, "months": n})
    return pd.DataFrame(out)
