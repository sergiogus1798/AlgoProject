"""Encargo 66 §3.4e: the footprint priced in blocks gives the daily series it gave — the oracle below is the code replaced."""

import itertools
import zlib

import numpy as np
import pandas as pd
import pytest
from test_perf66_resample import peak, same

from engines.market import reprice
from engines.nulls import footprint, windowed
from engines.nulls import inputs as nulls_inputs

COSTS = {
    "point_value": 1.0,
    "tick_size": 0.01,
    "spread": 0.05,
    "slippage": 0.0,
    "commission_method": "SizeBased",
    "rounds": True,
    "commission": 0.0,
    "swap_long": 0.0,
    "swap_short": 0.0,
    "triple": 4,
    "rollover": 23,
}


def old_footprint(
    trades: pd.DataFrame, bars: pd.DataFrame, costs: dict, knobs: dict
) -> tuple:
    """`footprint.footprint` before the blocks: every draw priced at once."""

    def per_bar(where: np.ndarray, what: np.ndarray, n: int) -> np.ndarray:
        """Average over draws of `what` summed per bar."""
        return np.bincount(where.ravel(), what.ravel(), n) / len(where)

    day = bars.index.normalize()
    if trades.empty:
        return pd.Series(0.0, index=day.unique()), 0.0
    where = nulls_inputs.on_grid(trades, bars.index, np.inf)
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
    drawn = windowed.draw(
        shared,
        mine,
        knobs["rung"],
        knobs["draws"],
        np.random.default_rng(  # the seed salted by the mother, as footprint() now does
            np.random.SeedSequence([knobs["seed"], zlib.crc32(b"m")])
        ),
    )
    drawn["sizes"] = np.broadcast_to(
        mine["size"].mean() if windowed.REDRAWS[knobs["rung"]][1] else mine["size"],
        drawn["entries"].shape,
    )
    enter, leave = drawn["entries"], drawn["entries"] + drawn["holds"]
    opens, closes, time_ = (
        bars["Open"].to_numpy(),
        bars["Close"].to_numpy(),
        bars.index.to_numpy(),
    )
    net, _ = reprice.pnl(
        opens[enter],
        opens[leave],
        time_[enter],
        time_[leave],
        side,
        drawn["sizes"],
        costs,
    )
    lots = side * drawn["sizes"]
    paid = net - costs["point_value"] * lots * (opens[leave] - opens[enter])
    held = (per_bar(enter, lots, len(bars)) - per_bar(leave, lots, len(bars))).cumsum()
    after = np.r_[opens[1:], closes[-1]]
    mark = np.where(np.r_[day[1:] != day[:-1], True], closes, after)
    gap = held * (after - mark)
    money = costs["point_value"] * (
        held * (mark - opens) + np.r_[0.0, gap[:-1]]
    ) + per_bar(leave, paid, len(bars))
    daily = pd.Series(money).groupby(day.to_numpy()).sum()
    return daily, float(
        net.sum(axis=1).std(ddof=1) / np.sqrt(knobs["draws"]) / len(daily)
    )


def market(
    trades: int, seed: int = 1, kind: str = "Buy"
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """A mother's trades and the M1 bars under them, as tests/test_blindjoint.py lays them."""
    rng = np.random.default_rng(seed)
    days = pd.bdate_range("2021-01-04", periods=120)
    index = pd.DatetimeIndex(
        np.add.outer(days.values, np.arange(60) * np.timedelta64(1, "m")).ravel()
    )
    price = 100 + np.cumsum(rng.normal(0.004, 0.05, len(index) + 1))
    bars = pd.DataFrame(
        {
            "Open": price[:-1],
            "Close": price[1:],
            "High": np.maximum(price[:-1], price[1:]) + 0.01,
            "Low": np.minimum(price[:-1], price[1:]) - 0.01,
        },
        index=index,
    )
    hold = rng.integers(30, 600, trades)
    enter = rng.integers(0, len(index) - hold)
    side = np.resize(["Buy", "Sell"], trades) if kind == "both" else kind
    return pd.DataFrame(
        {
            "Open time": index[enter],
            "Close time": index[enter + hold],
            "Type": side,
            "Size": rng.choice([0.5, 1.0, 1.7], trades),
        }
    ), bars


def test_footprint_in_blocks_is_the_old_one(monkeypatch: pytest.MonkeyPatch) -> None:
    """3.4e: the daily series and its Monte Carlo error, whatever the block the draws are priced in."""
    cases = [
        (150, "Buy", 500),
        (150, "Sell", 500),
        (40, "both", 333),
        (1, "Buy", 64),
        (2, "Sell", 2),
        (150, "Buy", 2),
    ]
    for (trades, kind, draws), rung in itertools.product(cases, windowed.REDRAWS):
        mother, bars = market(trades, trades + draws, kind)
        knobs = {"rung": rung, "draws": draws, "seed": 20261012}
        was = old_footprint(mother, bars, COSTS, knobs)
        for block in (1, 7 * trades, 64 * trades, windowed.BLOCK):
            monkeypatch.setattr(windowed, "BLOCK", block)
            now = footprint.footprint(mother, bars, COSTS, knobs, "m")
            assert same(was[0].to_numpy(), now[0].to_numpy()), (
                trades,
                kind,
                draws,
                rung,
                block,
            )
            assert was[0].index.equals(now[0].index) and was[1] == now[1]
        monkeypatch.undo()
    mother, bars = market(150)
    same_day = mother.assign(
        **{
            "Open time": mother["Open time"].iloc[0],
            "Close time": mother["Close time"].iloc[0],
            "Size": 1.0,
        }
    )
    knobs = {"rung": "timing", "draws": 300, "seed": 3}
    monkeypatch.setattr(windowed, "BLOCK", 1500)
    for frame in (same_day, mother.iloc[:0]):
        was, now = (
            old_footprint(frame, bars, COSTS, knobs),
            footprint.footprint(frame, bars, COSTS, knobs, "m"),
        )
        assert same(was[0].to_numpy(), now[0].to_numpy()) and was[1] == now[1]
    monkeypatch.setattr(windowed, "BLOCK", 20_000)
    knobs = {"rung": "free", "draws": 4000, "seed": 3}
    was = peak(lambda: old_footprint(mother, bars, COSTS, knobs))
    now = peak(lambda: footprint.footprint(mother, bars, COSTS, knobs, "m"))
    print(
        f"\n3.4e footprint 4000 draws x 150 trades: peak {was / 1e6:.0f} MB -> {now / 1e6:.0f} MB"
    )
    assert now < was / 4
