#!/usr/bin/env python3
"""Per-segment and per-market metrics read off the .sqx, and the exact union of any of them."""

import os
import sys
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core import fanout, sqxstats
from sqx.variants import legs as legmod

FULL = sqxstats.FULL
KEY = ["variant_id", "market"]
# What a union is allowed to add up, and it is the whole reason the union is exact rather
# than an approximation: these are counts and sums of the same trades, so three segments'
# values add to the value the same backtest would have produced unsplit.
ADDITIVE = ["NetProfit", "GrossProfit", "GrossLoss", "NumberOfTrades", "NumberOfLosses"]
# What C3 spreads into columns. The rest of the 82 stored metrics stay in the long frame.
HEADLINE = ["NetProfit", "NumberOfTrades", "ProfitFactor", "WinningPct", "AvgTrade",
            "GrossProfit", "GrossLoss", "Drawdown", "DrawdownPct", "SharpeRatio",
            "RExpectancy", "Stability", "ReturnDDRatio"]
BLOCK = 100          # files per worker task

# What the block readers see, set before the fork: one leg's sorted files and its name.
_SHARED: dict = {}


def per_result(folder: Path, segment: str,
               say: Callable[[int, str], None]) -> pd.DataFrame:
    """Every variant's stored metrics, one row per result the .sqx carries.

    Args:
        folder: One leg's databank folder inside the install.
        segment: Which leg this is, written into the rows.
        say: Called with a percentage and a status line.

    Returns:
        One row per (variant, market) with the FULL-sample metrics SQX stored — the same
        numbers the databank shows, not a recomputation. `Portfolio` is dropped: it is
        every market summed, so keeping it would double-count the moment anything adds a
        column up. The per-result scoping is what makes this correct on a cross-market
        retest (`core.sqxstats.stats`, measured 2026-09-24).
    """
    files = sorted(folder.glob("*.sqx"))
    _SHARED.update(files=files, segment=segment)
    # Blocks of files on every core, each file's settings.xml parsed once for all its
    # results: 🔬 2026-09-25, 15,000 files x 10 results took 196 s on one core.
    blocks = dict(fanout.run(_rows, {i: BLOCK for i in range(0, len(files), BLOCK)},
                             os.cpu_count()))
    say(100, f"{len(files)} de {len(files)} .sqx leidos ({segment})")
    return pd.DataFrame([row for i in sorted(blocks) for row in blocks[i]])


def _rows(start: int) -> list[dict]:
    """per_result()'s rows for one block of a leg's files, in file order."""
    rows = []
    for path in _SHARED["files"][start:start + BLOCK]:
        for key, stats in sqxstats.every(path).items():
            name = legmod.market(key)
            if name not in (legmod.MAIN,) and not key.startswith(legmod.EXTRA):
                continue
            rows.append({"variant_id": path.stem, "segment": _SHARED["segment"],
                         "market": name, "result_key": key} | stats[FULL])
    return rows


def combine(rows: pd.DataFrame, segments: list[str], curves: pd.DataFrame | None = None,
            label: str = "ALL") -> pd.DataFrame:
    """Add a set of segments up into the one backtest they would have been unsplit.

    Args:
        rows: What `per_result` returned for every leg, concatenated.
        segments: Which segments to join, e.g. ["oos1", "oos2"].
        curves: Daily P&L of the joined window, dates down and `variant_id` across, for
            the main market. Drawdown and Sharpe are recomputed from it because neither is
            additive — three segments' drawdowns say nothing about the drawdown of the
            whole, which can be deeper than any of them. None leaves those two columns out.
        label: What to call the result in the `segment` column.

    Returns:
        One row per (variant, market), with the additive metrics summed and the ratios
        rebuilt from those sums: profit factor from gross profit over gross loss, win rate
        from wins over trades, average trade from net over trades. Rebuilding beats
        averaging the per-segment ratios, which weights a five-year leg like a ten-year one.
    """
    part = rows[rows["segment"].isin(segments)]
    out = part.groupby(KEY, as_index=False)[ADDITIVE].sum()
    out["segment"] = label
    out["NumberOfWins"] = out["NumberOfTrades"] - out["NumberOfLosses"]
    # Three cases, and the middle one is why this is not a one-liner. No trades at all ->
    # undefined, never 0: SQX stores 0.0 there and a 0 sorts like the worst result in the
    # grid when it is actually the absence of one. Winners and no losers -> genuinely
    # infinite; 🔬 SQX stores 5.0 for that (`Strategy 9.6.29` on Brent, 3 trades, no loss),
    # a cap that would be a lie once three segments are added up.
    out["ProfitFactor"] = np.where(
        out["NumberOfTrades"] == 0, np.nan,
        np.where(out["GrossLoss"] > 0,
                 out["GrossProfit"] / out["GrossLoss"].replace(0, np.nan), np.inf))
    out["WinningPct"] = 100 * out["NumberOfWins"] / out["NumberOfTrades"].replace(0, np.nan)
    out["AvgTrade"] = out["NetProfit"] / out["NumberOfTrades"].replace(0, np.nan)
    if curves is None:
        return out
    # The curve is the MAIN market's, so its drawdown and Sharpe are attached to the main
    # rows only. Writing them onto an extra market's row would label silver's union with
    # gold's drawdown -- the same number under three market names, and no error anywhere.
    # The per-market curves live in `equity_markets.parquet` for whoever wants them there.
    return out.merge(from_curves(curves).assign(market=legmod.MAIN),
                     on=["variant_id", "market"], how="left")


def from_curves(daily: pd.DataFrame) -> pd.DataFrame:
    """The two metrics no sum can produce: the joined window's drawdown and its Sharpe.

    Args:
        daily: Per-day P&L, dates down and `variant_id` across.

    Returns:
        One row per variant with `Drawdown` (the deepest peak-to-trough of the joined
        curve, in account currency and positive) and `SharpeRatio` (annualised from the
        daily series, 252 days). Both are properties of the whole window: a variant can
        end each segment above water and still have crossed a deeper trough than any
        segment saw, which is exactly the kind of thing this study exists to catch.
    """
    cum = daily.cumsum()
    drawdown = (cum.cummax() - cum).max()
    sd = daily.std(ddof=1)
    sharpe = (daily.mean() / sd.replace(0, np.nan)) * np.sqrt(252)
    return pd.DataFrame({"variant_id": daily.columns, "Drawdown": drawdown.to_numpy(),
                         "SharpeRatio": sharpe.to_numpy()})


def thin(rows: pd.DataFrame, floor: int, over: list[str]) -> pd.DataFrame:
    """Which (variant, market) backtests trade too little to be a result at all.

    Args:
        rows: What `per_result` returned for every leg, concatenated.
        floor: `wfc.min_trades_total` — trades over the whole study window, not per leg.
        over: The segments the total is counted across, normally all three.

    Returns:
        One row per (variant, market) with its total trade count and whether it clears the
        floor. **It is counted per market on purpose**: a backtest is one strategy on one
        market, and a variant that trades 400 times on gold and 9 times on silver has one
        result and one non-result, not two thin ones.

        The floor is a hard exclusion and not a weight (owner, 2026-09-24): a variant that
        barely trades does not produce a bad result, it produces a number that measures one
        or two trades, and on a grid of thousands those degenerate corners decide the
        correlation. Everything it touches is reported as a count, never dropped in silence.
    """
    part = rows[rows["segment"].isin(over)]
    total = part.groupby(KEY, as_index=False)["NumberOfTrades"].sum()
    return total.rename(columns={"NumberOfTrades": "trades_total"}).assign(
        usable=lambda d: d["trades_total"] >= floor)


def wide(rows: pd.DataFrame, market: str = legmod.MAIN,
         metrics: list[str] | None = None) -> pd.DataFrame:
    """One market's per-segment metrics spread across columns, one row per variant.

    Args:
        rows: `per_result` output, plus whatever `combine` added.
        market: Which market to lay out.
        metrics: Which metrics to spread. None takes `HEADLINE`, which is what the studies
            downstream actually read — all 82 across six segment labels would be five
            hundred columns of C3 nobody opens. The full detail stays in
            `segments.parquet`, one row per variant, segment and market.

    Returns:
        `variant_id` and then `<metric> (<segment>)` for every segment present — the shape
        `collect.py` joins onto the manifest, and the shape the WFC reads its two sides
        from. The segment is in the column name rather than in rows because every
        downstream study wants one row per variant.
    """
    columns = [c for c in (metrics or HEADLINE) if c in rows.columns]
    one = rows[rows["market"] == market]
    out = one.pivot(index="variant_id", columns="segment", values=columns)
    out.columns = [f"{metric} ({segment})" for metric, segment in out.columns]
    return out.reset_index()
