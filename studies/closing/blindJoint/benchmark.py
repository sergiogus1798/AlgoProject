"""What a random trader with a mother's own footprint earns per day: the benchmark of step 20."""

import numpy as np
import pandas as pd

from engines.market import reprice
from engines.nulls import inputs as nulls_inputs, model


def footprint(trades: pd.DataFrame, bars: pd.DataFrame, costs: reprice.Costs,
              knobs: dict) -> tuple[pd.Series, float]:
    """The expected daily P&L of trading one mother's footprint at random entries.

    Args:
        trades: One mother's trades inside the segment (schema T).
        bars: The feed's M1 bars over the segment: Open and Close, naive bar-open index.
        costs: `reprice.costs()` of the feed and segment — what the mother's own retest paid.
        knobs: `benchmark` of config.yaml: `rung`, `draws`, `seed`.

    Returns:
        One value per feed day: the MEAN over `draws` random traders of the day's P&L marked
        at the day's last M1 close; and the Monte Carlo standard error of that series' mean
        per day, same unit. No trades, a flat zero.

        Each trader is drawn by the ladder's own rung (`engines.nulls.model`): the mother's
        trade count, side and lots, each trade's holding time (in M1 bars), the entry at a
        uniform bar of the WHOLE segment — not from her first trade to her last, which would
        hand her when she started. Trades may overlap, as on the ladder. Priced by the one
        repricer at the declared costs, so every draw pays spread, slippage, commission and
        the swap of its own nights; the ladder's `calibrate.charged` holds no spread and
        would hand the benchmark what the mother paid
        (knowhow/research/monkey-reprice-audit.md).

        A mean is linear, so the traders are never priced day by day: their average position
        per bar is, and what each paid is booked on the bar it closed at. The series sums to
        the traders' mean net P&L exactly.
    """
    day = bars.index.normalize()
    if trades.empty:
        return pd.Series(0.0, index=day.unique()), 0.0
    located = {**nulls_inputs.on_grid(trades, bars.index, np.inf), "window": (0, len(bars) - 1)}
    # ponytail: every draw priced at once, ~100 bytes per draw x trade (200 MB at 2,000 x
    # 1,000 trades); price in blocks as engines.nulls.windowed does if draws grows tenfold.
    drawn = model.RUNGS[knobs["rung"]](located, knobs["draws"],
                                       np.random.default_rng(knobs["seed"]))
    enter, leave = drawn["entries"], drawn["entries"] + drawn["holds"]
    side = np.where(trades["Type"].astype(object) == "Buy", 1.0, -1.0)
    opens, closes, time = bars["Open"].to_numpy(), bars["Close"].to_numpy(), bars.index.to_numpy()
    net, _ = reprice.pnl(opens[enter], opens[leave], time[enter], time[leave], side,
                         drawn["sizes"], costs)
    lots = side * drawn["sizes"]
    paid = net - costs["point_value"] * lots * (opens[leave] - opens[enter])
    held = (_per_bar(enter, lots, len(bars)) - _per_bar(leave, lots, len(bars))).cumsum()
    # A bar's position is carried from its open to the next bar's; over a day's last bar it
    # is marked at that close, and the gap to the next open is the next day's.
    after = np.r_[opens[1:], closes[-1]]
    mark = np.where(np.r_[day[1:] != day[:-1], True], closes, after)
    gap = held * (after - mark)
    money = (costs["point_value"] * (held * (mark - opens) + np.r_[0.0, gap[:-1]])
             + _per_bar(leave, paid, len(bars)))
    daily = pd.Series(money).groupby(day.to_numpy()).sum()
    return daily, float(net.sum(axis=1).std(ddof=1) / np.sqrt(knobs["draws"]) / len(daily))


def _per_bar(where: np.ndarray, what: np.ndarray, bars: int) -> np.ndarray:
    """The mean over the traders (rows) of `what`, summed on the bar each entry of `where` names."""
    return np.bincount(where.ravel(), what.ravel(), bars) / len(where)
