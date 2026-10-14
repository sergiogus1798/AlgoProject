#!/usr/bin/env python3
"""crossmarket/travel judge_on (encargo 46 G): costs in R fall with the entry ATR, so a no-edge strategy
entering on high ATR reads off-centre on net and centred on gross; `net` is the old reading, `e` stays net."""

import functools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.transfer.crossmarket.travel import rules, run, shift, sizing, stat, tensor
from tests.test_crossmarket_travel import DAYS, PARAMS, SEED, calendar, costs, frame

MARKETS, STRATEGIES, RUNS = 4, 120, 200


@functools.cache
def regimes() -> dict[str, dict]:
    """Markets with no edge and a volatility that comes in long regimes, shared by all; real costs."""
    rng = np.random.default_rng(3)
    vol = 0.004 * np.exp(
        np.repeat(rng.normal(0, 0.6, len(DAYS) // 40 + 1), 40)[: len(DAYS)]
    )
    out = {}
    for j in range(MARKETS):
        open_ = 100.0 * np.exp(np.cumsum(rng.normal(0, 1, len(DAYS)) * vol))
        close = np.append(open_[1:], open_[-1])
        wick = np.abs(rng.normal(0, 0.5, len(DAYS))) * vol * open_
        bars = pd.DataFrame(
            {
                "Open": open_,
                "High": np.maximum(open_, close) + wick,
                "Low": np.minimum(open_, close) - wick,
                "Close": close,
            },
            index=DAYS,
        )
        out[f"M{j}"] = tensor.market(bars, costs(1.0, 0.5), PARAMS, calendar())
    return out


def high_atr_strategy(number: int) -> dict[str, pd.DataFrame]:
    """Entries drawn blind to direction among the top third of bars by ATR; holds of 1 to 8 bars."""
    rng = np.random.default_rng([11, number])
    atr = sizing.entry_atr(regimes()["M0"]["bars"], PARAMS["ATRPeriod"])
    top = np.flatnonzero(np.nan_to_num(atr, nan=0) >= np.nanquantile(atr, 2 / 3))
    top = top[top < len(DAYS) - 9]
    entry = np.sort(rng.choice(top, 40, replace=False))
    mine = frame(
        DAYS[entry],
        DAYS[entry + rng.integers(1, 9, 40)],
        "Buy" if number % 2 else "Sell",
    )
    return {name: mine for name in regimes()}


@functools.cache
def z_conj(judge: str) -> np.ndarray:
    """z_conj of every strategy over the whole span, read on `judge`."""
    cal, shifts = calendar(), shift.draws(calendar(), SEED, RUNS)
    return np.array(
        [
            stat.joint(
                tensor.build(
                    high_atr_strategy(s), regimes(), cal, shifts, "week", judge
                )
            )["z"]
            for s in range(STRATEGIES)
        ]
    )


def se(z: np.ndarray) -> float:
    """Standard error of the mean of z."""
    return z.std(ddof=1) / np.sqrt(len(z))


def test_gross_is_centred_where_net_is_not() -> None:
    """High-ATR entries, no edge: gross within 3 se of 0; net is off-centre upwards (cost in R is smaller)."""
    gross, net = z_conj("gross"), z_conj("net")
    assert abs(gross.mean()) < 3 * se(gross), gross.mean()
    assert net.mean() > 3 * se(net) and net.mean() > gross.mean() + 0.3, (
        net.mean(),
        gross.mean(),
    )


def test_e_and_net_arrays_stay_net_whatever_judge_says() -> None:
    """judge net == the old tensor; judge gross keeps real_net/null_net equal to it, and `e` is unchanged."""
    cal, shifts = calendar(), shift.draws(calendar(), SEED, 50)
    mine = high_atr_strategy(1)
    net = tensor.build(mine, regimes(), cal, shifts, "week")
    gross = tensor.build(mine, regimes(), cal, shifts, "week", "gross")
    assert np.array_equal(net["real"], net["real_net"], equal_nan=True)
    assert np.array_equal(gross["real_net"], net["real"], equal_nan=True)
    assert np.array_equal(gross["null_net"], net["null"], equal_nan=True)
    assert np.nansum(gross["real"] - gross["real_net"]) > 0  # the cost added back
    mask = rules.windows(cal)["all"]
    assert np.allclose(
        rules.per_market(gross, mask)["e"], rules.per_market(net, mask)["e"]
    )
    assert not np.allclose(
        rules.per_market(gross, mask)["z"], rules.per_market(net, mask)["z"]
    )


def test_e_principal_is_the_main_e_on_v2() -> None:
    """P7's denominator is `per_market`'s e of the main over V2, not over the whole span."""
    cal, t = calendar(), {"shift_step": "week", "judge_on": "gross"}
    shifts, mine, home = (
        shift.draws(cal, SEED, 50),
        high_atr_strategy(1)["M0"],
        ("M0", regimes()["M0"]),
    )
    whole = tensor.build({"M0": mine}, {"M0": home[1]}, cal, shifts, "week", "gross")
    got = run._e_principal(mine, home, cal, shifts, t)
    assert (
        np.isfinite(got)
        and got == rules.per_market(whole, rules.windows(cal)["V2"])["e"].iloc[0]
    )
    assert got != rules.per_market(whole, rules.windows(cal)["all"])["e"].iloc[0]
    assert np.isnan(run._e_principal(mine, ("M0", None), cal, shifts, t))
