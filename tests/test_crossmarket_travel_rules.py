#!/usr/bin/env python3
"""Known-answer tests of crossmarket/travel's rules P2-P9 and §7.1 (encargo 46, part C's gate): a toy
tensor whose every number is worked out by hand below — z_conj, the V2 restriction, leave-one-market-out,
breadth with the +1 correction, tau_half, N_peor, beta / z_beta / e_end with years pooled — and the
columns of the output."""

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.transfer.crossmarket.travel import (
    frequency,
    rules,
    run,
    shift,
    stat,
    tensor,
    validity,
)
from test_crossmarket_travel import PARAMS, RUNS, SEED, calendar, noise, random_strategy

CFG = {
    "min_trades_market": 30,
    "worse_z": -1.65,
    "degradation": {"min_trades_year": 30, "min_years": 4},
}
YEARS = pd.to_datetime([f"{y}-01-01" for y in range(2012, 2019)])
CAL = pd.DataFrame(
    {"start": YEARS, "window": ["V0", "V1", "V1", "V1", "V2", "V2", "after"]}
)
SD = math.sqrt(4 / 3)  # sd (ddof 1) of a market's four random totals +-1, +-1


def toy() -> dict:
    """Three markets, six cells in the span and one `after` full of numbers that must not count.

    Random run r gives market j the same u[r, j] in every cell, so every total below is a
    multiple of it; u has mean 0 and sd SD in each market.
    """
    real = np.array(
        [[6, 6, 6, 6, 0, 0, 1000], [1, 3, 1, 3, 1, 3, 1000], [-1] * 6 + [1000]], float
    )
    u = np.array([[1, 1, 1], [-1, 1, -1], [1, -1, -1], [-1, -1, 1]], float)
    null = np.repeat(u[:, :, None], 7, 2)
    null[:, :, 6] = 0
    trades = np.array([[40] * 6 + [99], [40] * 6 + [99], [2] * 6 + [99]], float)
    return {"markets": ["A", "B", "C"], "real": real, "null": null, "trades": trades}


def test_joint_and_windows() -> None:
    """Joint and windows."""
    got = rules.evaluate(toy(), CAL, CFG)["verdict"]
    # real 24 + 12 - 6 = 30; the random totals are 6 x (3, -1, -1, -1) = 18, -6, -6, -6: sd 12
    assert got["z_conj"] == pytest.approx(30 / 12)
    assert got["p_conj"] == pytest.approx(1 / 5)  # no run reaches 30: (1 + 0) / (4 + 1)
    # V2 = cells 4, 5: real 0+0, 1+3, -1-1 = 2; random totals 2 x (3, -1, -1, -1): sd 4
    assert got["z_conj_v2"] == pytest.approx(2 / 4)
    assert got["z_conj_v0"] == pytest.approx(6 / 2)  # cell 0: 6 + 1 - 1 against sd 2
    assert got["z_conj_v1"] == pytest.approx(
        22 / 6
    )  # cells 1-3: 18 + 7 - 3 against sd 6
    assert got["z_conj_v0v2"] == pytest.approx(
        8 / 6
    )  # cells 0, 4, 5 (V1 out): real 8; sd 6
    assert got["trades"] == 40 * 6 * 2 + 2 * 6  # the `after` cell's 99 is left out


def test_leave_one_market_out() -> None:
    """Leave one market out."""
    got = rules.evaluate(toy(), CAL, CFG)["verdict"]
    # without A: real 12 - 6 = 6, random 6 x (2, 0, -2, 0): sd sqrt(96); without B 18 and without C 36
    # over the same sd, so the weakest is the list without A
    assert got["z_minus_market"] == pytest.approx(6 / math.sqrt(96))
    assert got["minus_market"] == "A"


def test_breadth_with_the_plus_one() -> None:
    """Breadth with the plus one."""
    got = rules.evaluate(toy(), CAL, CFG)["verdict"]
    # every market's random totals are 6, -6, 6, -6 type: median 0. The real run is above it in A and
    # B, not in C: C_real = 2. The runs read as real: 3, 1, 1, 1 markets above. One run reaches 2.
    assert got["breadth_count"] == 2
    assert got["p_breadth"] == pytest.approx((1 + 1) / (4 + 1))


def test_tau_half_is_the_ceil_half_th_largest() -> None:
    """Tau half is the ceil half th largest."""
    got = rules.evaluate(toy(), CAL, CFG, e_principal=0.1)["verdict"]
    # e = real total / trades: A 24/240 = 0.1, B 12/240 = 0.05, C has 12 trades < 30 -> -inf.
    # M = 3, ceil(3/2) = 2: the second largest of (1, 0.5, -inf)
    assert got["tau_half"] == pytest.approx(0.5)
    four = rules.tau_half(
        np.array([0.1, 0.05, 0.02, 0.01]), np.array([100] * 4), 0.1, 30
    )
    assert four == pytest.approx(0.5)  # M = 4: the 2nd of (1, .5, .2, .1)
    assert (
        rules.tau_half(np.array([0.1, np.nan, np.nan]), np.array([100, 0, 0]), 0.1, 30)
        == -np.inf
    )


def test_tau_half_without_e_principal_is_empty() -> None:
    """Tau half without e principal is empty."""
    assert np.isnan(rules.evaluate(toy(), CAL, CFG)["verdict"]["tau_half"])
    assert np.isnan(rules.evaluate(toy(), CAL, CFG)["verdict"]["e_principal"])
    for bad in (0.0, -0.1, np.nan):
        assert np.isnan(
            rules.tau_half(np.array([0.1, 0.1]), np.array([50, 50]), bad, 30)
        )


def test_markets_against() -> None:
    """Markets against."""
    # a market under the minimum is never counted, one at or below the line is
    z, n = (
        np.array([-2.0, -3.0, -1.7, 0.0, -1.65, np.nan]),
        np.array([100, 10, 100, 100, 100, 100]),
    )
    assert rules.worse(z, n, 30, -1.65) == 3
    got = rules.evaluate(toy(), CAL, CFG)["verdict"]
    assert got["worse"] == 0 and got["worse_fraction"] == 0  # z_C = -6 / (6 SD) = -0.87
    rows = rules.per_market(toy(), CAL["window"].ne("after").to_numpy())
    assert rows["z"].tolist() == pytest.approx(
        [24 / (6 * SD), 12 / (6 * SD), -6 / (6 * SD)]
    )
    assert rows["e"].iloc[0] == pytest.approx(0.1) and rows["trades"].tolist() == [
        240,
        240,
        12,
    ]


def test_absent_market_counts_against_and_is_not_zero() -> None:
    """Absent market counts against and is not zero."""
    one = toy()
    one["real"][2], one["null"][:, 2], one["trades"][2] = 0, 0, 0  # C never traded
    got = rules.evaluate(one, CAL, CFG, e_principal=0.1)
    assert got["verdict"]["breadth_count"] == 2  # 0 is not above a median of 0
    assert np.isnan(got["markets"]["z"].iloc[2]) and np.isnan(
        got["markets"]["e"].iloc[2]
    )
    assert got["verdict"]["worse"] == 0 and got["verdict"]["tau_half"] == pytest.approx(
        0.5
    )


def test_no_data_is_nan_never_zero() -> None:
    """No data is nan never zero."""
    one = toy()
    one["real"][:, 0], one["null"][:, :, 0], one["trades"][:, 0] = (
        np.nan,
        np.nan,
        np.nan,
    )  # no bars in V0
    got = rules.evaluate(one, CAL, CFG)
    assert np.isnan(got["verdict"]["z_conj_v0"])
    assert np.isfinite(got["verdict"]["z_conj"]) and np.isfinite(
        got["verdict"]["z_conj_v1"]
    )
    assert [y for g in got["d_y"] for y in g["years"]] == [
        2013,
        2014,
        2015,
        2016,
        2017,
    ]  # year 2012 skipped
    gone = toy()
    gone["real"][1], gone["null"][:, 1], gone["trades"][1] = (
        np.nan,
        np.nan,
        np.nan,
    )  # market B has none
    assert np.isnan(rules.per_market(gone, np.ones(7, bool))["z"].iloc[1])
    rows = rules.per_market(gone, np.ones(7, bool))
    assert (
        np.isnan(rows["e"].iloc[1])
        and np.isnan(rows["trades"].iloc[1])
        and np.isfinite(rows["z"].iloc[0])
    )


def test_degradation_beta_z_beta_e_end_and_pooling() -> None:
    """Degradation beta z beta e end and pooling."""
    # one market, one year per cell, trades 10, 10, 30, 40, 50, 60: 2012-14 pool (10+10+30 = 50 >= 30),
    # the other three stand alone. Group years (offset from 2012, trades-weighted): 1.4, 3, 4, 5.
    # n = 50, 40, 50, 60; t-bar = 3.45; centred = -2.05, -.45, .55, 1.55; Sxx = 377.5
    cal = pd.DataFrame({"start": YEARS[:6], "window": "V1"})
    real = np.array([[1, 1, 1, 2, 3, 2]], float)
    run1 = np.ones((1, 6))
    null = np.stack([np.zeros((1, 6)), run1, -run1])  # mean 0 in every cell
    one = {
        "markets": ["A"],
        "real": real,
        "null": null,
        "trades": np.array([[10, 10, 30, 40, 50, 60]], float),
    }
    got = rules.degradation(one, cal, np.ones(6, bool), CFG["degradation"])
    # group totals 3, 2, 3, 2: beta = sum(c T) / Sxx = (-6.15 - .9 + 1.65 + 3.1) / 377.5
    assert got["beta"] == pytest.approx(-2.3 / 377.5)
    # each random run's slope is sum(c T_b) / Sxx with T_b = 3, 1, 1, 1 times 0, +1, -1 -> 0, -4.5/377.5, +4.5/377.5
    assert got["z_beta"] == pytest.approx(-2.3 / 4.5)
    mean = 10 / 200  # sum T / sum n
    end = mean + (-2.3 / 377.5) * (5 - 3.45)  # last year 2017 = offset 5
    assert got["e_end"] == pytest.approx(end) and got["e_end_ratio"] == pytest.approx(
        end / mean
    )
    assert [g["years"] for g in got["d_y"]] == [
        [2012, 2013, 2014],
        [2015],
        [2016],
        [2017],
    ]
    assert [g["trades"] for g in got["d_y"]] == [50, 40, 50, 60]
    assert got["d_y"][1]["d"] == pytest.approx(2 / 40)
    few = {**one, "trades": np.full((1, 6), 10.0)}  # two groups of 30: under min_years
    out = rules.degradation(few, cal, np.ones(6, bool), CFG["degradation"])
    assert (
        all(np.isnan(out[k]) for k in ("beta", "z_beta", "e_end", "e_end_ratio"))
        and out["d_y"] == []
    )


def test_the_columns_are_the_contract() -> None:
    """The columns are the contract."""
    verdict = [
        "strategy",
        "markets",
        "markets_valid",
        "invalid_fraction",
        "fixed_distance",
        "freq_off",
        "freq_off_fraction",
        "z_conj",
        "p_conj",
        "z_conj_v2",
        "z_conj_v0",
        "z_conj_v1",
        "z_conj_v0v2",
        "z_minus_market",
        "minus_market",
        "p_breadth",
        "breadth_count",
        "tau_half",
        "e_principal",
        "worse",
        "worse_fraction",
        "z_beta",
        "e_end",
        "beta",
        "e_end_ratio",
        "net_t_pooled",
        "trades",
    ]
    assert run.VERDICT == verdict
    assert run.MARKETS == [
        "strategy",
        "market",
        "z",
        "p",
        "e",
        "trades",
        "z_freq",
        "valid",
        "invalid_reason",
    ]
    got = rules.evaluate(toy(), CAL, CFG)
    added = {
        "strategy",
        "markets",
        "markets_valid",
        "invalid_fraction",
        "fixed_distance",
        "freq_off",
        "freq_off_fraction",
        "net_t_pooled",
    }
    assert (
        set(got["verdict"]) | added == set(verdict) and not set(got["verdict"]) & added
    )
    assert set(got["markets"].columns) | {
        "strategy",
        "z_freq",
        "valid",
        "invalid_reason",
    } == set(run.MARKETS)


def test_runner_refuses_a_folder_with_a_result(tmp_path: Path) -> None:
    """Runner refuses a folder with a result."""
    (tmp_path / "verdict.csv").write_text("x")
    with pytest.raises(FileExistsError):
        run._free(tmp_path, "P", "D", "2026-10-07")
    run._free(tmp_path / "new", "P", "D", "2026-10-07")


def test_frequency_is_nan_without_trades_and_centred() -> None:
    """Frequency is nan without trades and centred."""
    cuts = {
        "build": pd.Timestamp("2012-01-01"),
        "oos1": pd.Timestamp("2016-01-01"),
        "end": pd.Timestamp("2018-01-01"),
    }
    main = pd.DataFrame(
        {
            "strategy": ["a"] * 60 + ["b"] * 60 + ["c"] * 60,
            "Open time": list(pd.date_range("2012-01-01", periods=60, freq="30D")) * 3,
        }
    )
    counts = pd.DataFrame({"M": [120, 120, 0]}, index=["a", "b", "c"])
    z = frequency.z_freq(
        counts, pd.Series({"M": 4.0}), main, cuts, {"phi_min": 1.5, "phi_max": 3.5}
    )
    assert np.isnan(z.loc["c", "M"]) and z.loc["a", "M"] == pytest.approx(
        z.loc["b", "M"]
    )
    assert z.loc["a", "M"] == pytest.approx(0.0)  # a and b are the population's median


def test_validity_flags_the_card_and_the_prices() -> None:
    """Validity flags the card and the prices."""
    rng = np.random.default_rng(3)
    index = pd.date_range("2020-01-01", periods=400, freq="D")
    open_ = 100 + np.cumsum(rng.normal(0, 1, 400))
    bars = pd.DataFrame(
        {"Open": open_, "High": open_ + 1.2, "Low": open_ - 1.2, "Close": open_ + 0.1},
        index=index,
    )
    at = np.arange(5, 395, 7)
    size = rng.uniform(0.5, 2, at.size)
    trades = pd.DataFrame(
        {
            "Type": "Buy",
            "Open time": index[at],
            "Close time": index[at + 3],
            "Open price": open_[at],
            "Close price": open_[at + 3],
            "Size": size,
            "Profit/Loss": (open_[at + 3] - open_[at]) * size * 10.0,
        }
    )
    card = {"point_value": 10.0}
    args = (0.02, 0.02, 0.25, 20)
    good = validity.check("X", trades, bars, card, *args)
    assert good["valid"] and abs(good["point_value_gap"]) < 1e-9
    wrong = validity.check("X", trades, bars, {"point_value": 11.0}, *args)
    assert not wrong["valid"] and "point_value" in wrong["invalid_reason"]
    off = validity.check(
        "X",
        trades.assign(
            **{"Open price": open_[at] + 30, "Close price": open_[at + 3] + 30}
        ),
        bars,
        card,
        *args,
    )
    assert not off["valid"] and "fill_mismatch" in off["invalid_reason"]


def holed_markets(limit: float | None) -> dict[str, dict]:
    """The 11 noise markets, four of them with a multi-month hole in a different year; with a
    `limit` the validity probe leaves out the cells the holes make unusable."""
    cal, shifts, out = calendar(), shift.draws(calendar(), SEED, RUNS), {}
    for j, (name, mkt) in enumerate(noise().items()):
        bars = mkt["bars"]
        if j < 4:
            year = 2013 + j % 3
            bars = bars[
                ~((bars.index >= f"{year}-02-01") & (bars.index < f"{year}-09-01"))
            ]
        out[name] = tensor.market(bars, mkt["costs"], PARAMS, cal)
        if limit is not None:
            tensor.exclude(out[name], cal, shifts, "week", limit)
    return out


def test_a_hole_excludes_its_market_cell_and_only_that() -> None:
    """A seven-month hole in one year of one market: that (market, cell) is out (NaN, never 0)
    in the real run, every random run and the count; every other pair of every market stays."""
    cal, markets = calendar(), holed_markets(0.20)
    gone = {
        (name, int(i))
        for name, m in markets.items()
        for i in np.flatnonzero(~m["data"])
    }
    year = lambda y: int(np.flatnonzero(cal["start"] == f"{y}-01-01")[0])  # noqa: E731
    assert gone == {
        ("M0", year(2013)),
        ("M1", year(2014)),
        ("M2", year(2015)),
        ("M3", year(2013)),
    }
    assert (markets["M5"]["share"] < 0.05).all() and markets["M0"]["share"][
        year(2013)
    ] > 0.3
    got = tensor.build(
        {n: random_strategy(1)[n] for n in markets},
        markets,
        cal,
        shift.draws(cal, SEED, 50),
        "week",
    )
    assert (
        np.isnan(got["real"][0, year(2013)])
        and np.isnan(got["null"][:, 0, year(2013)]).all()
    )
    assert np.isnan(got["trades"][0, year(2013)])
    assert (
        np.isfinite(got["null"][:, 0, year(2014)]).all()
        and np.isfinite(got["real"][5]).all()
    )


def test_no_edge_on_markets_with_holes_is_centred_after_the_exclusion() -> None:
    """No edge, markets with holes: with the exclusion mean z_conj is within 3 se of 0. Without it
    is only printed (+0.073 +- 0.088, the same): this synthetic (daily Mon-Fri bars, one clean
    block hole) does NOT reproduce the real feeds' off-centre +0.44; the test above guards the mechanism."""
    cal, shifts, means = calendar(), shift.draws(calendar(), SEED, RUNS), {}
    for limit in (0.20, None):
        markets = holed_markets(limit)
        z = np.array(
            [
                stat.joint(
                    tensor.build(random_strategy(s), markets, cal, shifts, "week")
                )["z"]
                for s in range(150)
            ]
        )
        means[limit] = (z.mean(), z.std(ddof=1) / np.sqrt(len(z)))
    assert abs(means[0.20][0]) < 3 * means[0.20][1], means
