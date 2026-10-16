"""The numbers of every cell: what it earned, and where it sits among its own timeframe's nulls."""

from typing import Any, TypedDict, cast

import numpy as np
import pandas as pd

from core import fanout, metrics, tradestore
from core.study import draws
from engines.nulls import simulate, verdict
from studies.transfer.crossTF import siblings

# 2026-09-30 (feedback §5): "P saturado" speaks of a run's own reconstruction, never of the
# reading a cell is judged on -- it fires whenever `nulls.draws` is the binding constraint (a
# config knob, not a cell fact). Kept out of this study's warnings;
# `engines.nulls.verdict.distrust` still raises it for whoever else reads the same engine.
DROP_WARNINGS = ("P SATURADO",)
# The owner's one Sharpe (`core.metrics`: daily P&L on trading days, annualised), measured beside the null's
# statistics so the window can draw it; never a key of `engines.nulls.stats`.
TOTAL = "sharpe_total"


class _Cell(TypedDict):
    """One cell's statistics, their empirical p, the nulls' mean and sd, and what there is to distrust."""

    trades: int
    seen: float
    p: float
    null_mean: float
    null_sd: float
    z: float
    seen_all: dict[str, float]
    p_all: dict[str, float]
    warnings: list[str]


class CellNumbers(_Cell, total=False):
    """A cell's numbers; `draws` (the `core.study.draws` rows of every statistic) only when the caller asked for them."""

    draws: list[dict[str, Any]]


def _trusted(said: list[str]) -> list[str]:
    """`verdict.distrust`'s sentences, minus the two this study does not surface."""
    return [s for s in said if not s.upper().startswith(DROP_WARNINGS)]


def numbers(
    rows: pd.DataFrame,
    frame: pd.DataFrame,
    nullcfg: dict,
    statistic: str,
    rung: str,
    key: str,
    min_trades: int,
    cell: dict | None = None,
) -> CellNumbers:
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
        min_trades: `usable.min_trades` of this study's config; below it the cell gets no p.
        cell: What tells this cell apart (strategy, block, timeframe, role, mother, seed): given,
            the result carries `draws`, one `core.study.draws` row per statistic of `seen_all`
            (metric = the statistic's name; z and p of the headline one are made of its row).

    Returns:
        `trades`, `seen`, `p`, `null_mean`, `null_sd`, `z` (the headline statistic's distance
        from its null's mean, in the null's standard deviations: unlike `p` it does not
        saturate at 1/(draws+1)), `seen_all`, `p_all` and `warnings`. `p` and the three null
        numbers are NaN when the cell has too few trades for one, which is a fact about the
        cell and not a missing input.
        `seen_all` also carries `sharpe_total` (`core.metrics.sharpe` of `weekday_pnl` of the
        cell's own trades, by close date), which is read and never judged: the null draws
        carry no calendar, so it has no p.

    A cell with NO trades is that fact taken to its limit: the entry condition never fired
    on that timeframe. It returns before the nulls are drawn, because pricing an empty
    trade list against the bars raises rather than returning nothing.
    """
    names = nullcfg["statistics"]["report"]
    if rows.empty:
        empty = {n: np.nan for n in names}
        return CellNumbers(
            trades=0,
            seen=np.nan,
            p=np.nan,
            null_mean=np.nan,
            null_sd=np.nan,
            z=np.nan,
            seen_all={**empty, TOTAL: np.nan},
            p_all=empty,
            warnings=[
                "La estrategia no operó en este timeframe: no hay nada que juzgar."
            ],
        )
    kept = simulate.fixed(rows, frame, nullcfg)
    seen_all = {
        **simulate.real(kept, names),
        TOTAL: metrics.sharpe(
            metrics.weekday_pnl(
                rows["Profit/Loss"].to_numpy(dtype=float),
                cast(np.ndarray, rows["Close time"]),
            ),
            metrics.TRADING_DAYS,
        ),
    }
    if len(rows) < min_trades:
        p_all = {n: np.nan for n in names}
        return CellNumbers(
            trades=len(rows),
            seen=seen_all[statistic],
            p=np.nan,
            null_mean=np.nan,
            null_sd=np.nan,
            z=np.nan,
            seen_all=seen_all,
            p_all=p_all,
            warnings=[
                f"Solo {len(rows)} operaciones en oos1, menos de las {min_trades} que hacen falta para calcular un p."
            ],
        )
    drawn = simulate.nulls(kept, rung, nullcfg, key)
    p_all = {n: verdict.pvalue(seen_all[n], drawn[n], n) for n in names}
    mean, sd = float(np.mean(drawn[statistic])), float(np.std(drawn[statistic], ddof=1))
    rec = (
        {}
        if cell is None
        else {
            "draws": [
                draws.record(
                    "crossTF.cell", n, seen_all[n], drawn[n], raw=False, **cell
                )
                for n in names
            ]
        }
    )
    return cast(
        CellNumbers,
        {
            **rec,
            "trades": len(rows),
            "seen": seen_all[statistic],
            "p": p_all[statistic],
            "null_mean": mean,
            "null_sd": sd,
            "z": (seen_all[statistic] - mean) / sd if sd else np.nan,
            "seen_all": seen_all,
            "p_all": p_all,
            "warnings": _trusted(verdict.distrust(kept, p_all, len(rows), nullcfg)),
        },
    )


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


_SHARED: dict = {}  # set by `panel` before the fork, read by `_cell` in the workers


def _cell(i: int) -> CellNumbers:
    """`numbers` of cell `i` of `panel`, in a worker that inherited the parent's inputs."""
    g, row = _SHARED, _SHARED["rows"][i]
    return numbers(
        tradestore.block(g["packed"], row.strategy, row.block),
        g["frames"][row.timeframe],
        g["nullcfg"],
        g["statistic"],
        g["rung"],
        f"{row.strategy}|{row.block}",
        g["min_trades"],
        g["where"](row),
    )


def panel(
    plan: pd.DataFrame,
    packed: pd.DataFrame,
    frames: dict,
    nullcfg: dict,
    cfg: dict,
    sink: list | None = None,
) -> pd.DataFrame:
    """Every cell of the matrix, measured.

    Args:
        plan: What `inputs.plan` returned.
        packed: What `inputs.trades` returned.
        frames: Timeframe to bars, from `inputs.bars`.
        nullcfg: What `engines.nulls.inputs.config` returned.
        cfg: What `inputs.config` returned.
        sink: When given, the `draws` rows of every cell are appended to it.

    Returns:
        The plan with what `numbers` returned joined onto it, one row per cell,
        `corr_vs_baseline` (`correlations`, NaN on a baseline) and what `beyond` adds.
    """
    statistic, rung = cfg["verdict"]["statistic"], cfg["verdict"]["rung"]
    where = lambda r: (
        None
        if sink is None
        else dict(
            strategy=r.strategy,
            block=r.block,
            timeframe=r.timeframe,
            role=r.role,
            mother=r.mother,
            seed=nullcfg["nulls"]["seed"],
        )
    )
    rows = list(cast(Any, plan.itertuples()))
    _SHARED.update(
        rows=rows,
        packed=packed,
        frames=frames,
        nullcfg=nullcfg,
        statistic=statistic,
        rung=rung,
        min_trades=cfg["usable"]["min_trades"],
        where=where,
    )
    # One cell per task: the seed is `strategy|block`, so a cell draws the same on any process.
    cost = {
        i: len(tradestore.block(packed, r.strategy, r.block))
        for i, r in enumerate(rows)
    }
    got = dict(fanout.run(_cell, cost, fanout.CORES))
    measured = [got[i] for i in range(len(rows))]
    for m in measured:
        rows = m.pop("draws", [])
        if sink is not None:
            sink.extend(rows)
    alike = siblings.correlations(plan, packed).rename(
        columns={"corr": "corr_vs_baseline"}
    )
    out = pd.concat([plan.reset_index(drop=True), pd.DataFrame(measured)], axis=1)
    return siblings.beyond(
        out.merge(
            alike[["strategy", "timeframe", "role", "corr_vs_baseline"]],
            on=["strategy", "timeframe", "role"],
            how="left",
        )
    )


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
    value = (
        panel["seen_all"].map(
            lambda d: d.get(statistic) if isinstance(d, dict) else None
        )
        if "seen_all" in panel
        else panel["seen"]
    )
    wide = panel.assign(cell=panel["role"] + "_" + panel["timeframe"], _value=value)
    return wide.pivot_table(
        index="mother", columns="cell", values="_value", observed=True
    )
