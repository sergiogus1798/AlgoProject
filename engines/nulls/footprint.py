"""What a random trader with a mother's own footprint and clock hours earns per day: step 20's benchmark and the oos2 reading's monkey."""

import zlib
from typing import cast

import numpy as np
import pandas as pd

from engines.market import reprice
from engines.nulls import inputs as nulls_inputs
from engines.nulls import windowed


def footprint(
    trades: pd.DataFrame,
    bars: pd.DataFrame,
    costs: reprice.Costs,
    knobs: dict,
    mother: str,
) -> tuple[pd.Series, float]:
    """The expected daily P&L of trading one mother's footprint at random entries.

    Args:
        trades: One mother's trades inside the segment (schema T).
        bars: The feed's M1 bars over the segment: Open, High, Low and Close (the last two for the
            hours null's ATR), naive bar-open index.
        costs: `reprice.costs()` of the feed and segment — what the mother's own retest paid.
        knobs: `benchmark` of config.yaml: `rung`, `draws`, `seed`.
        mother: Her name, which salts the seed: each mother's random traders are her own
            draws, never the same stream shared by every mother of the batch.

    Returns:
        One value per feed day: the MEAN over `draws` random traders of the day's P&L marked
        at the day's last M1 close; and the Monte Carlo standard error of that series' mean
        per day, same unit. No trades, a flat zero.

        Each trader is drawn by the hours null (`engines.nulls.windowed`, owner 2026-10-12):
        the mother's trade count, side and lots, each trade's holding time (in M1 bars), the
        entry at a uniform bar of the WHOLE segment — not from her first trade to her last,
        which would hand her when she started — at the clock hour of the trade it replaces.
        The lots stay hers: `windowed.draw` re-sizes by ATR, and here that is put back. Trades may overlap, as on the ladder. Priced by the one
        repricer at the declared costs, so every draw pays spread, slippage, commission and
        the swap of its own nights; the ladder's `calibrate.charged` holds no spread and
        would hand the benchmark what the mother paid
        (knowhow/research/monkey-reprice-audit.md).

        A mean is linear, so the traders are never priced day by day: their average position
        per bar is, and what each paid is booked on the bar it closed at. The series sums to
        the traders' mean net P&L exactly.
    """
    stamps = cast(pd.DatetimeIndex, bars.index)
    day = stamps.normalize()  # pyright: ignore[reportAttributeAccessIssue]  # stub lacks DatetimeIndex.normalize
    if trades.empty:
        return pd.Series(0.0, index=day.unique()), 0.0
    where = nulls_inputs.on_grid(trades, stamps, np.inf)
    side = np.where(trades["Type"].astype(object) == "Buy", 1.0, -1.0)
    shared = windowed.grid(bars, np.arange(len(bars)), np.zeros(len(bars), int))
    mine = windowed.located(
        shared,
        where["entry"],
        where["exit"],
        where["size"],
        side,
        np.zeros(where["entry"].size, int),
    )
    opens, closes, time = (
        bars["Open"].to_numpy(),
        bars["Close"].to_numpy(),
        bars.index.to_numpy(),
    )
    draws = knobs["draws"]
    rng = np.random.default_rng(
        np.random.SeedSequence([knobs["seed"], zlib.crc32(mother.encode())])
    )
    entered, left, paid = np.zeros((3, len(bars)))
    total = np.empty(draws)
    # Priced in blocks, as windowed.means: a draw takes the same random numbers whatever the
    # block, and np.add.at adds each bar's lots in bincount's very order, so nothing moves.
    block = max(1, windowed.BLOCK // mine["entry"].size)
    for done in range(0, draws, block):
        drawn = windowed.draw(
            shared, mine, knobs["rung"], min(block, draws - done), rng
        )
        enter, leave = drawn["entries"], drawn["entries"] + drawn["holds"]
        sizes = (
            mine["size"].mean() if windowed.REDRAWS[knobs["rung"]][1] else mine["size"]
        )
        lots = np.broadcast_to(side * sizes, enter.shape)
        net, _ = reprice.pnl(
            opens[enter],
            opens[leave],
            time[enter],
            time[leave],
            side,
            np.broadcast_to(sizes, enter.shape),
            costs,
        )
        np.add.at(entered, enter.ravel(), lots.ravel())
        np.add.at(left, leave.ravel(), lots.ravel())
        np.add.at(
            paid,
            leave.ravel(),
            (net - costs["point_value"] * lots * (opens[leave] - opens[enter])).ravel(),
        )
        total[done : done + len(net)] = net.sum(axis=1)
    held = (entered / draws - left / draws).cumsum()
    # A bar's position is carried from its open to the next bar's; over a day's last bar it
    # is marked at that close, and the gap to the next open is the next day's.
    after = np.r_[opens[1:], closes[-1]]
    mark = np.where(np.r_[day[1:] != day[:-1], True], closes, after)
    gap = held * (after - mark)
    money = (
        costs["point_value"] * (held * (mark - opens) + np.r_[0.0, gap[:-1]])
        + paid / draws
    )
    daily = cast(pd.Series, pd.Series(money).groupby(day.to_numpy()).sum())
    return daily, float(total.std(ddof=1) / np.sqrt(draws) / len(daily))
