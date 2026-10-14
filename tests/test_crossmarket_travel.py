#!/usr/bin/env python3
"""Known-answer battery of crossmarket/travel (encargo 46, part A's gate): synthetic prices with no
edge, 11 markets, 300 random-entry strategies — z centred, unit spread, nominal rejection; a planted
drift's z by hand; zero shift, market labels, Amount, seed, joint shifts; a missing year is not 0."""

import functools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines.market import reprice
from studies.transfer.crossmarket.travel import cells, shift, sizing, stat, tensor

DAYS = pd.bdate_range("2012-01-02", "2017-12-29")  # daily bars, Monday to Friday
CUTS = {
    "build": pd.Timestamp("2012-03-15"),
    "oos1": pd.Timestamp("2016-01-01"),
    "end": pd.Timestamp("2018-01-01"),
}  # build opens mid-year: 2012 is split
PARAMS = {"Amount": 1000, "ATRPeriod": 20, "ATRMult": 4}
SEED, MARKETS, STRATEGIES, RUNS = 20261007, 11, 300, 200


def calendar(unit: str = "year", step: str = "week") -> pd.DataFrame:
    """The cells of the synthetic span."""
    return cells.table(DAYS[0], DAYS[-1], CUTS, unit, step)


def costs(point_value: float, spread: float) -> reprice.Costs:
    """A card's costs: spread and slippage in price, a percent swap, no commission."""
    return {
        "point_value": point_value,
        "tick_size": 0.01,
        "spread": spread,
        "slippage": spread / 5,
        "commission_method": "PercentageBased",
        "commission": 0.0,
        "swap_long": -3.0,
        "swap_short": -1.0,
        "triple": 2,
        "rollover": 23,
        "tick_step": None,
    }


def flat(index: pd.DatetimeIndex = DAYS) -> pd.DataFrame:
    """Bars that never move: open 100, range 1, so the ATR is exactly 1."""
    return pd.DataFrame(
        {"Open": 100.0, "High": 100.5, "Low": 99.5, "Close": 100.0}, index=index
    )


def frame(opens: list, closes: list, kind: str = "Buy") -> pd.DataFrame:
    """Trades as SQX exports them, as far as travel reads them."""
    return pd.DataFrame(
        {
            "Open time": pd.to_datetime(opens),
            "Close time": pd.to_datetime(closes),
            "Type": kind,
        }
    )


@functools.cache
def noise() -> dict[str, dict]:
    """11 markets with no edge: a drift, a common factor, and costs worth 0.1 R a trade."""
    rng, out = np.random.default_rng(1), {}
    common = rng.normal(0, 0.006, len(DAYS))
    for j in range(MARKETS):
        open_ = (
            100.0
            * (j + 1)
            * np.exp(np.cumsum(0.0003 + common + rng.normal(0, 0.008, len(DAYS))))
        )
        close = np.append(open_[1:], open_[-1])
        wick = np.abs(rng.normal(0, 0.004, len(DAYS))) * open_
        bars = pd.DataFrame(
            {
                "Open": open_,
                "High": np.maximum(open_, close) + wick,
                "Low": np.minimum(open_, close) - wick,
                "Close": close,
            },
            index=DAYS,
        )
        out[f"M{j}"] = tensor.market(
            bars, costs((1.0, 10.0, 0.063)[j % 3], 0.5 * (j + 1)), PARAMS, calendar()
        )
    return out


def random_strategy(number: int, per_market: int = 40) -> dict[str, pd.DataFrame]:
    """Entries on bars drawn blind to the prices, holds of 1 to 8 bars, one side per strategy —
    and the SAME stamps in every market, as a logic that fires on a shared move would: a null
    that shifted each market on its own would be too narrow here (measured: sd of z 2.1)."""
    rng = np.random.default_rng([7, number])
    entry = np.sort(rng.choice(len(DAYS) - 9, per_market, replace=False))
    mine = frame(
        DAYS[entry],
        DAYS[entry + rng.integers(1, 9, per_market)],
        "Buy" if number % 2 else "Sell",
    )
    return {name: mine for name in noise()}


@functools.cache
def battery() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """z_conj, its p and the real total in R of every random strategy, over the whole span."""
    cal, shifts = calendar(), shift.draws(calendar(), SEED, RUNS)
    got = [
        stat.joint(tensor.build(random_strategy(s), noise(), cal, shifts, "week"))
        for s in range(STRATEGIES)
    ]
    return tuple(np.array([g[k] for g in got]) for k in ("z", "p", "real"))


def test_null_z_is_centred() -> None:
    """No edge: mean z_conj within 3 standard errors of 0, though the costs make them all lose."""
    z, _, real = battery()
    assert abs(z.mean()) < 3 * z.std(ddof=1) / np.sqrt(len(z)), z.mean()
    assert real.mean() < -20, real.mean()


def test_null_z_has_unit_spread() -> None:
    """No edge: the standard deviation of z_conj is 1 +- 0.1."""
    z = battery()[0]
    assert abs(z.std(ddof=1) - 1) < 0.1, z.std(ddof=1)


def test_null_rejection_rate_is_nominal() -> None:
    """No edge: z >= 1.65 and p <= 0.05 reject 5 % and z >= 2.33 1 %, within 3 binomial sd."""
    z, p, _ = battery()
    for rate, nominal in (
        (np.mean(z >= 1.65), 0.05),
        (np.mean(p <= 0.05), 0.05),
        (np.mean(z >= 2.33), 0.01),
    ):
        assert abs(rate - nominal) < 3 * np.sqrt(nominal * (1 - nominal) / len(z)), (
            rate,
            nominal,
        )


def test_planted_drift_moves_z_by_hand() -> None:
    """Flat markets, no costs; one market rises 2 (half an R at 4 ATR of 1) in one week of 2014
    and one real trade holds exactly that week. Only shift 0 catches it: with f the share of
    runs whose 2014 shift is 0, z = (0.5 - 0.5 f) / (0.5 sqrt(f (1 - f) n / (n - 1)))."""
    cal, runs = calendar(), 5000
    risen = flat()
    week = (DAYS >= "2014-06-02") & (DAYS < "2014-06-09")
    risen[["Open", "High", "Low", "Close"]] += np.where(
        DAYS >= "2014-06-09", 2.0, 0.4 * np.cumsum(week) * week - 0.4 * week
    )[:, None]
    free = costs(2.0, 0.0) | {"swap_long": 0.0, "swap_short": 0.0}
    markets = {
        n: tensor.market(risen if n == "B" else flat(), free, PARAMS, cal)
        for n in "ABC"
    }
    other = frame(["2013-05-06", "2015-03-02"], ["2013-05-09", "2015-03-10"])
    trades = {
        "A": other,
        "C": other,
        "B": frame(["2014-06-02", "2015-08-03"], ["2014-06-09", "2015-08-05"]),
    }
    shifts = shift.draws(cal, SEED, runs)
    got = tensor.build(trades, markets, cal, shifts, "week")
    y2014 = int(np.flatnonzero(cal["start"] == "2014-01-01")[0])
    assert got["real"][1, y2014] == 0.5 and stat.total(got["real"]) == 0.5
    f = np.mean(shifts[:, y2014] == 0)
    by_hand = (0.5 - 0.5 * f) / (0.5 * np.sqrt(f * (1 - f) * runs / (runs - 1)))
    for chosen in ({}, {"markets": [1]}, {"cells": [y2014]}):
        assert abs(stat.joint(got, **chosen)["z"] - by_hand) < 1e-9, (chosen, by_hand)
    # sqrt(51) at f = 1/52; f is a count, so: the 52 shifts are uniform (chi-square, 51 df, 99.9 %)
    seen = np.bincount(shifts[:, y2014], minlength=52)
    assert ((seen - runs / 52) ** 2 / (runs / 52)).sum() < 87.97, seen
    assert np.isnan(
        stat.joint(got, markets=[0])["z"]
    )  # flat market: the runs do not vary


def test_zero_shift_reproduces_the_observed() -> None:
    """Every run at shift 0 is the real run; and the real run is the repricer on the real
    stamps at the doctrine's size, computed here straight from the bars."""
    cal, trades = calendar(), random_strategy(3)  # an odd one: long
    got = tensor.build(trades, noise(), cal, np.zeros((3, len(cal)), np.int64), "week")
    assert np.array_equal(
        got["null"], np.repeat(got["real"][None], 3, 0), equal_nan=True
    )
    for j, (name, mkt) in enumerate(noise().items()):
        bars, mine = mkt["bars"], trades[name]
        size = sizing.lots(
            sizing.entry_atr(bars, 20), mkt["costs"]["point_value"], PARAMS
        )
        net, _ = reprice.pnl(
            bars["Open"].loc[mine["Open time"]].to_numpy(),
            bars["Open"].loc[mine["Close time"]].to_numpy(),
            mine["Open time"].to_numpy(),
            mine["Close time"].to_numpy(),
            1.0,
            size[bars.index.get_indexer(mine["Open time"])],
            mkt["costs"],
        )
        assert abs(net.sum() / 1000 - stat.total(got["real"], markets=[j])) < 1e-9, name
        assert stat.total(got["trades"], markets=[j]) == len(mine)


def test_market_labels_do_not_matter() -> None:
    """The same markets renamed and in another order give the same z_conj."""
    cal, trades = calendar(), random_strategy(5)
    shifts = shift.draws(cal, SEED, 100)
    order = np.random.default_rng(0).permutation(MARKETS)
    renamed = {f"X{i}": f"M{j}" for i, j in enumerate(order)}
    a = stat.joint(tensor.build(trades, noise(), cal, shifts, "week"))
    again = ({x: source[m] for x, m in renamed.items()} for source in (trades, noise()))
    b = stat.joint(tensor.build(*again, cal, shifts, "week"))
    assert abs(a["z"] - b["z"]) < 1e-9 and a["p"] == b["p"], (a, b)


def test_amount_does_not_change_z() -> None:
    """1R of 7,000 instead of 1,000: the same z, up to the repricer's rounding to the cent."""
    cal, trades = calendar(), random_strategy(5)
    shifts = shift.draws(cal, SEED, 100)
    zs = []
    for amount in (1000, 7000):
        markets = {
            n: tensor.market(m["bars"], m["costs"], PARAMS | {"Amount": amount}, cal)
            for n, m in noise().items()
        }
        zs.append(stat.joint(tensor.build(trades, markets, cal, shifts, "week"))["z"])
    assert abs(zs[0] - zs[1]) < 1e-4, zs


def test_same_seed_same_output() -> None:
    """Same seed, identical tensor; another seed, other shifts."""
    cal, trades = calendar(), random_strategy(5)
    one, two = (
        tensor.build(trades, noise(), cal, shift.draws(cal, SEED, 50), "week")
        for _ in "ab"
    )
    assert all(
        np.array_equal(one[k], two[k], equal_nan=True)
        for k in ("real", "null", "trades")
    )
    assert not np.array_equal(
        shift.draws(cal, SEED, 50), shift.draws(cal, SEED + 1, 50)
    )
    assert np.array_equal(shift.draws(cal, SEED, 50), shift.draws(cal, SEED, 80)[:50])


def test_one_draw_moves_every_market_alike() -> None:
    """One run is one displacement everywhere: the same entries land on the same instants in a
    full market and in one whose history starts in 2014, by a whole number of weeks, rigidly
    inside the cell (every trade of 2015 by the run's shift, or by it less the 52 weeks of the
    wrap); 0..steps-1 all occur."""
    cal, shifts = calendar(), shift.draws(calendar(), SEED, 400)
    assert all(
        set(shifts[:, c]) == set(range(s)) for c, s in enumerate(cal["steps"]) if s < 60
    )
    late = DAYS[DAYS >= "2014-01-01"]
    stamps = pd.to_datetime(
        ["2015-01-05", "2015-03-11", "2015-03-13", "2015-12-30", "2016-07-07"]
    )
    moved = []
    for index in (DAYS, late):
        seconds = index.to_numpy("datetime64[s]").astype(np.int64)
        entry = index.get_indexer(stamps)
        cell = (
            np.searchsorted(cal["start"].to_numpy(), stamps.to_numpy(), side="right")
            - 1
        )
        moved.append(seconds[shift.entries(seconds, entry, cell, cal, shifts, "week")])
    assert np.array_equal(moved[0], moved[1])
    weeks = (moved[0] - stamps.to_numpy("datetime64[s]").astype(np.int64)) / (7 * 86400)
    assert np.array_equal(weeks, np.round(weeks))
    y2015 = int(np.flatnonzero(cal["start"] == "2015-01-01")[0])
    k = shifts[:, [y2015]]  # 2015 has 52 Mondays, Wednesdays and Fridays
    assert ((weeks[:, :4] == k) | (weeks[:, :4] == k - 52)).all()
    assert (weeks[:, :4] != 0).any(1).mean() > 0.9
    stayed = pd.DatetimeIndex(moved[0].astype("datetime64[s]").ravel())
    assert set(stayed.year[np.tile(np.arange(5) < 4, 400)]) == {2015}


def test_units_and_frontiers() -> None:
    """A year is split at the main's build start; no shift crosses V1/V2; `semester` adds 1 July
    and `day` moves by business days, shift 0 staying put."""
    cal = calendar()
    assert list(cal["window"]) == ["V0", "V1", "V1", "V1", "V1", "V2", "V2"]
    assert cal["start"][1] == CUTS["build"] and list(cal["steps"]) == [
        10,
        41,
        52,
        52,
        52,
        52,
        52,
    ]
    assert pd.Timestamp("2014-07-01") in set(calendar("semester")["start"])
    days = calendar("year", "day")
    seconds = DAYS.to_numpy("datetime64[s]").astype(np.int64)
    entry = np.arange(60, 1500, 7)
    cell = (
        np.searchsorted(days["start"].to_numpy(), DAYS[entry].to_numpy(), side="right")
        - 1
    )
    still = shift.entries(
        seconds, entry, cell, days, np.zeros((1, len(days)), np.int64), "day"
    )
    assert np.array_equal(still[0], entry)
    moved = shift.entries(
        seconds, entry, cell, days, shift.draws(days, SEED, 50), "day"
    )
    landed = (
        np.searchsorted(
            days["start"].to_numpy(), DAYS[moved.ravel()].to_numpy(), side="right"
        )
        - 1
    )
    assert np.array_equal(landed, np.tile(cell, 50))


def test_a_missing_year_is_not_zero() -> None:
    """A market with no bars in 2014 has NaN there — real, every run, the count, its z and its
    p — never 0; a market with bars and no trade there has a true 0; z_conj still reads."""
    cal = calendar()
    y2014 = int(np.flatnonzero(cal["start"] == "2014-01-01")[0])
    holed = DAYS[DAYS.year != 2014]
    walk = noise()["M0"]["bars"]
    markets = {
        "whole": noise()["M0"],
        "idle": noise()["M1"],
        "holed": tensor.market(walk.loc[holed], noise()["M0"]["costs"], PARAMS, cal),
    }
    busy = random_strategy(11)["M0"]
    year = busy["Close time"].dt.year
    trades = {
        "whole": busy,
        "holed": busy[year != 2014],
        "idle": busy[~year.isin([2013, 2014, 2015])],
    }
    got = tensor.build(trades, markets, cal, shift.draws(cal, SEED, 100), "week")
    assert np.isnan(got["real"][2, y2014]) and np.isnan(got["trades"][2, y2014])
    assert np.isnan(got["null"][:, 2, y2014]).all()
    gone = stat.joint(got, markets=[2], cells=[y2014])
    assert all(np.isnan(gone[k]) for k in ("z", "p", "real", "mean", "sd")), gone
    assert got["real"][1, y2014] == 0.0 and got["trades"][1, y2014] == 0.0
    assert (got["null"][:, 1, y2014] == 0.0).all()
    assert (
        np.isfinite(got["null"][:, [0, 1]]).all() and np.isnan(got["null"]).sum() == 100
    )
    assert np.isnan(stat.total(got["real"], cells=[y2014], markets=[2]))
    assert stat.total(got["trades"], cells=[y2014]) == got["trades"][0, y2014]
    assert np.isfinite(stat.joint(got)["z"]) and np.isfinite(
        stat.joint(got, cells=[y2014])["z"]
    )
    assert stat.total(got["real"]) == np.nansum(got["real"])
