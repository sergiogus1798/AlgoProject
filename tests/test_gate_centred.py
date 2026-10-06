#!/usr/bin/env python3
"""R5 and R5d of the gate (level 1b, centred): the same trading rate reads zero, a population
under the minimum is not centred, a population that falls as one keeps what exceeds the cap,
an excess with no trend has no slope, the projected excess uses the centred slope at half
oos1, a strategy of both sides is a population apart, and the fallen keep their facts."""

import sys
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.screening.analysis import centred  # noqa: E402
from studies.screening.gate import level1b_centred  # noqa: E402

CFG = yaml.safe_load((Path(level1b_centred.__file__).with_name("config.yaml"))
                     .read_text(encoding="utf-8"))
MARKET = {"windows": {"IS": ("2010-01-01", "2018-01-01"), "OOS": ("2018-01-01", "2022-01-01")},
          "years": {"IS": 8.0, "OOS": 4.0}}
BUILD = 320            # 40 a year over the 8 years of the build
NOISE = np.tile([1.0, -1.0, -1.0, 1.0], 40)     # reads the same backwards: no slope of its own


def harvest(strategies: int, per_year: int, excess: Callable = lambda years: 0 * years) -> dict:
    """A population of identical longs: 40 trades a year in the build, `per_year` in oos1.

    Args:
        excess: Years to the end of oos1 (negative) → each oos1 trade's excess before NOISE.
    """
    names = [f"s{i}" for i in range(strategies)]
    opened = pd.date_range("2010-01-05", "2017-12-20", periods=BUILD)
    closed = pd.date_range("2018-01-10", "2021-12-20", periods=4 * per_year)
    years = np.asarray((closed - pd.Timestamp("2022-01-01")) / pd.Timedelta(days=centred.YEAR))
    trades = pd.DataFrame({"identity": np.repeat(names, BUILD), "sample": "IS",
                           "Open time": np.tile(opened, strategies)})
    oos = pd.DataFrame({"identity": np.repeat(names, len(closed)),
                        "close_time": np.tile(closed, strategies), "side": 1.0,
                        "excess": np.tile(excess(years) + NOISE[:len(closed)], strategies)})
    return {"trades": trades, "oos": oos, "market": MARKET}


def facts(data: dict) -> pd.Series:
    """The level's three facts, the same for every strategy of a harvest()."""
    out = level1b_centred.run(data, pd.Index(data["oos"]["identity"].unique()), CFG)
    assert np.allclose(out, out.iloc[0])
    return out.iloc[0]


def test_same_rate_reads_zero() -> None:
    """The same trading rate in both windows reads zero."""
    assert facts(harvest(5, 40))["z_frec"] == pytest.approx(0, abs=1e-9)
    assert facts(harvest(40, 40))["z_frec"] == pytest.approx(0, abs=1e-9)


def test_under_the_minimum_no_centring() -> None:
    """29 strategies that all trade 60 % less: nothing is subtracted. The yearly counts are
    even, so phi sits on its floor and the error is sqrt(phi_min x (1/320 + 1/64))."""
    se = np.sqrt(CFG["frequency"]["phi_min"] * (1 / BUILD + 1 / 64))
    assert facts(harvest(CFG["centring"]["min_strategies"] - 1, 16))["z_frec"] == \
        pytest.approx(np.log(0.4) / se)


def test_a_population_that_falls_keeps_the_excess_over_the_cap() -> None:
    """At the minimum the centre exists, and it stops at -cap_log_rate (-0.35), not at ln 0.4."""
    data = harvest(CFG["centring"]["min_strategies"], 16)
    log = pd.Series(np.log(0.4), index=data["oos"]["identity"].unique())
    middle = centred.centre(log, pd.Series(1.0, index=log.index), 30, 0.35)
    assert (middle == -0.35).all()
    se = np.sqrt(CFG["frequency"]["phi_min"] * (1 / BUILD + 1 / 64))
    assert facts(data)["z_frec"] == pytest.approx((np.log(0.4) + 0.35) / se)


def test_the_centre_is_per_population_and_uncapped_without_a_cap() -> None:
    """The centre is per population and uncapped when no cap is given."""
    values = pd.Series([1.0] * 30 + [5.0] * 30 + [9.0] * 29)
    group = pd.Series([1] * 30 + [-1] * 30 + [0] * 29)
    assert centred.centre(values, group, 30, None).tolist() == [1.0] * 30 + [5.0] * 30 + [0.0] * 29
    assert centred.centre(values, group, 30, 2.0).tolist() == [1.0] * 30 + [2.0] * 30 + [0.0] * 29


def test_dispersion_is_variance_over_mean_and_ignores_a_part_year() -> None:
    """The dossier's example: 30, 45, 38, 52, 35, 41, 33, 55 → 1.96. A ninth year a quarter
    long that holds a quarter of a year's trades leaves the rate unchanged, and so adds nothing."""
    counts = pd.DataFrame([[30, 45, 38, 52, 35, 41, 33, 55]])
    whole = pd.Series(1.0, index=range(8))
    assert centred.dispersion(counts, whole, 0, 99)[0] == pytest.approx(80.41 / 41.125, abs=1e-3)
    assert centred.dispersion(counts, whole, 2.5, 99)[0] == 2.5
    longer = pd.concat([whole, pd.Series([0.25], index=[8])])
    part = centred.dispersion(counts.assign(**{"8": 329 / 32}), longer, 0, 99)[0]
    assert part == pytest.approx(80.41 / 41.125 * 7 / 8, abs=1e-3)
    span = centred.calendar_exposure(pd.Timestamp("2010-10-01"), pd.Timestamp("2012-01-01"))
    assert span.index.tolist() == [2010, 2011, 2012]
    assert span.tolist() == pytest.approx([92 / 365.25, 365 / 365.25, 0.0])


def test_no_trend_no_slope() -> None:
    """A constant excess of 7 under noise with no slope: t_b = 0 and e_fin keeps the 7."""
    out = facts(harvest(3, 40, lambda years: 7 + 0 * years))
    assert out["t_b"] == pytest.approx(0, abs=1e-9)
    assert out["e_fin"] == pytest.approx(7)


def test_a_planted_slope_is_recovered_and_the_common_one_is_subtracted() -> None:
    """Excess = 5 - 30 x years to the end: b = -30 a year around a mean of 5 + 30 x the mean
    years left. Alone it is a decay (se = sd of NOISE / sqrt(sum of squared time), widened by
    the residuals' AR(1)) and e_fin = mean - 30 x 4 / 2; in a population that all decays alike
    the slope is the market's: t_b = 0 and e_fin is the mean."""
    data = harvest(3, 40, lambda years: 5 - 30 * years)
    fit = centred.slope(data["oos"], "excess", (data["oos"]["close_time"] - pd.Timestamp("2022-01-01"))
                        / pd.Timedelta(days=centred.YEAR)).iloc[0]
    mean = data["oos"]["excess"].mean()
    assert fit["b"] == pytest.approx(-30) and fit["mean"] == pytest.approx(mean)
    assert mean == pytest.approx(5 + 30 * 2.004, abs=0.1)    # the trades centre 2.004 years from the end
    years = np.linspace(0, (pd.Timestamp("2021-12-20") - pd.Timestamp("2018-01-10")).days / 365.25, 160)
    rho = (NOISE[1:] * NOISE[:-1]).sum() / 160
    plain = np.sqrt(160 / 158 / ((years - years.mean()) ** 2).sum())
    assert rho == pytest.approx(0, abs=0.01) and fit["se"] == pytest.approx(plain, rel=0.02)
    alone = facts(data)
    assert alone["t_b"] == pytest.approx(-30 / fit["se"]) and alone["t_b"] < -1.65
    assert alone["e_fin"] == pytest.approx(mean - 30 * MARKET["years"]["OOS"] / 2)
    crowd = facts(harvest(CFG["centring"]["min_strategies"], 40, lambda years: 5 - 30 * years))
    assert crowd["t_b"] == pytest.approx(0, abs=1e-6) and crowd["e_fin"] == pytest.approx(mean)


def test_both_sides_is_a_population_apart() -> None:
    """30 longs and one strategy that also sells, all trading 60 % less: the longs are centred,
    the one of both sides is alone in its population and is not."""
    data = harvest(CFG["centring"]["min_strategies"] + 1, 16)
    mixed = data["oos"]["identity"] == "s30"
    data["oos"].loc[mixed, "side"] = np.tile([1.0, 1.0, 1.0, -1.0], 16)    # mostly long
    out = level1b_centred.run(data, pd.Index(["s0"]), CFG)["z_frec"]
    se = np.sqrt(CFG["frequency"]["phi_min"] * (1 / BUILD + 1 / 64))
    assert out["s30"] == pytest.approx(np.log(0.4) / se)
    assert out.drop("s30").to_numpy() == pytest.approx((np.log(0.4) + 0.35) / se)


def test_the_fallen_keep_their_facts() -> None:
    """Only s1 is alive: the three strategies of the table come back, each with its facts."""
    out = level1b_centred.run(harvest(3, 40, lambda years: 7 + 0 * years), pd.Index(["s1"]), CFG)
    assert sorted(out.index) == ["s0", "s1", "s2"] and out.notna().all().all()
    assert list(out.columns) == list(level1b_centred.FACTS)


def test_too_few_trades_leave_the_facts_empty() -> None:
    """Two trades fit a line exactly: no error to read the slope against. No build trade: no rate."""
    data = harvest(1, 40)
    data["oos"] = data["oos"].head(2)
    data["trades"] = data["trades"].head(0)
    out = level1b_centred.run(data, pd.Index(["s0", "absent"]), CFG)
    assert out.loc["s0", ["z_frec", "t_b"]].isna().all() and out.loc["absent"].isna().all()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
