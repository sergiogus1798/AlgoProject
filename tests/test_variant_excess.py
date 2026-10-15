"""The shared excess: per trade it is the repricer minus the drift term, per year its sum over the
window's years, and day by day it adds back to the per-trade sum under every drift variant."""

import numpy as np
import pandas as pd
import pytest

from engines.market import reprice
from engines.variants import excess
from studies.screening.analysis import tradelevel

SPAN = ("2020-01-01", "2021-12-31")
FREE = {
    "point_value": 1.0,
    "tick_size": 0.01,
    "spread": 0.0,
    "slippage": 0.0,
    "commission_method": "SizeBased",
    "rounds": True,
    "commission": 0.0,
    "swap_long": 0.0,
    "swap_short": 0.0,
    "triple": 2,
    "rollover": 0,
}
DEAR = FREE | {
    "point_value": 10.0,
    "spread": 0.03,
    "slippage": 0.01,
    "commission": 0.7,
    "swap_long": -2.5,
    "swap_short": 1.5,
}
GATE = {"window": "year", "variant": "d"}  # studies/screening/gate/config.yaml, `drift`


def walk(seed: int = 0) -> pd.DataFrame:
    """Hourly bars, December 2019 to January 2022: a random walk in whole cents, drifting up."""
    index = pd.date_range("2019-12-01", "2022-01-31 23:00", freq="h")
    rng = np.random.default_rng(seed)
    close = (
        500.0
        + (
            rng.integers(-30, 32, len(index)) * (1 + (np.arange(len(index)) // 60) % 3)
        ).cumsum()
        / 100
    )
    opened = np.r_[500.0, close[:-1]]
    return pd.DataFrame(
        {
            "Open": opened,
            "High": np.maximum(opened, close) + 0.5,
            "Low": np.minimum(opened, close) - 0.5,
            "Close": close,
        },
        index=index,
    )


def batch(
    market: pd.DataFrame, variants: int = 6, each: int = 80, seed: int = 1
) -> pd.DataFrame:
    """Random trades inside SPAN: longs and shorts, holds of 0 to 400 bars, a third stopped out."""
    rng = np.random.default_rng(seed)
    inside = np.arange(len(market))[market.index.slice_indexer(*SPAN)]
    n = variants * each
    enter = rng.choice(inside[:-401], n)
    leave = enter + rng.choice([0, 1, 2, 7, 30, 120, 400], n)
    stopped = (rng.random(n) < 1 / 3) | (leave == enter)  # a hold of no bars is a stop
    sell = rng.random(n) < 0.4
    # a long's stop fills below the bar's open, a short's above it: both inside the bar's range
    stop = market["Open"].to_numpy()[leave] + np.where(sell, 0.25, -0.25)
    return pd.DataFrame(
        {
            "variant_id": [f"M000V{v:04d}" for v in rng.integers(0, variants, n)],
            "Type": np.where(sell, "Sell", "Buy"),
            "Size": rng.choice([0.1, 0.5, 1.3], n),
            "Open time": market.index[enter],
            "Close time": market.index[leave],
            "Close type": np.where(stopped, "SL", "Exit Signal"),
            "Close price": np.where(stopped, stop, market["Open"].to_numpy()[leave]),
        }
    )


def test_per_trade_is_the_repricer_minus_the_drift_term() -> None:
    """Row by row what step 14 composes by hand, and its `totals` regrouped from it."""
    market, trades = walk(), batch(walk())
    got = excess.per_trade(trades, market, DEAR, SPAN, GATE)
    priced = reprice.real(trades.assign(identity=trades["variant_id"]), market, DEAR)
    term, _ = tradelevel.drift_term(
        trades, market, SPAN, "year", "d", DEAR["point_value"]
    )
    assert got.index.equals(trades.index) and got["variant_id"].equals(
        trades["variant_id"]
    )
    assert np.array_equal(got["profit"], priced["pnl"]) and np.array_equal(
        got["drift"], term
    )
    assert np.array_equal(got["excess"], priced["pnl"] - term)
    assert got["drift"].abs().sum() > 0 and (got["cost"] != 0).all()


def test_a_known_market_gives_the_hand_count() -> None:
    """Opens 100 + S·j + A·(j odd), flat ATR: the drift is S per bar, the excess ±A or nothing."""
    s, a = 0.01, 1.0
    index = pd.date_range("2019-12-01", "2021-01-31 23:00", freq="h")
    opened = 100 + s * np.arange(len(index)) + a * (np.arange(len(index)) % 2)
    market = pd.DataFrame(
        {"Open": opened, "High": opened + 10, "Low": opened - 10, "Close": opened},
        index=index,
    )
    first = market.index.get_loc(pd.Timestamp("2020-03-02"))  # an even bar
    at, hold = first + np.array([0, 501, 1000, 1500]), np.array([1, 1, 2, 3])
    trades = pd.DataFrame(
        {
            "variant_id": ["x", "x", "y", "y"],
            "Type": "Buy",
            "Size": 1.0,
            "Open time": index[at],
            "Close time": index[at + hold],
        }
    )
    window = ("2020-01-01", "2020-12-31")
    got = excess.per_trade(trades, market, FREE, window, GATE)
    assert got["excess"].round(9).tolist() == [a, -a, 0.0, a]
    assert got["drift"].round(9).tolist() == [s, s, 2 * s, 3 * s]
    per_year = excess.per_year(got, window)
    assert per_year.round(9).to_dict() == {"x": 0.0, "y": round(a / (366 / 365.25), 9)}


@pytest.mark.parametrize("variant", sorted(tradelevel.VARIANTS))
@pytest.mark.parametrize("costs", [FREE, DEAR], ids=["free", "dear"])
def test_the_days_add_back_to_the_trades(variant: str, costs: dict) -> None:
    """Σ_t d[i, t] == Σ_j excess_j for every variant of the batch, far inside a cent."""
    market, trades = walk(), batch(walk())
    drift = {"window": "year", "variant": variant}
    per = excess.per_trade(trades, market, costs, SPAN, drift)
    days = excess.daily(trades, market, costs, SPAN, drift)
    want = per.groupby("variant_id")["excess"].sum()
    assert days.index.tolist() == pd.unique(trades["variant_id"]).tolist()
    assert days.columns.equals(pd.date_range(*SPAN, freq="D"))
    assert (days.sum(axis=1) - want.reindex(days.index)).abs().max() < 1e-6
    assert (
        days.abs().sum(axis=1).gt(want.abs().reindex(days.index)).all()
    )  # not one lump


def test_a_day_books_its_own_move_and_its_share_of_the_drift() -> None:
    """A long held 72 bars over a +5.00 jump: the jump's day carries it, not the exit's."""
    index = pd.date_range("2019-12-01", "2020-12-31 23:00", freq="h")
    jump = index.get_loc(pd.Timestamp("2020-06-10 05:00"))
    opened = 100.0 + 5.0 * (np.arange(len(index)) > jump)
    market = pd.DataFrame(
        {"Open": opened, "High": opened + 1, "Low": opened - 1, "Close": opened},
        index=index,
    )
    trades = pd.DataFrame(
        {
            "variant_id": ["x"],
            "Type": ["Buy"],
            "Size": [2.0],
            "Open time": [pd.Timestamp("2020-06-09 12:00")],
            "Close time": [pd.Timestamp("2020-06-12 12:00")],
        }
    )
    window = ("2020-01-01", "2020-12-31")
    term = excess.per_trade(trades, market, FREE, window, GATE)["drift"].item()
    got = excess.daily(trades, market, FREE, window, GATE).loc["x"]
    assert term != 0 and got[got != 0].index.strftime("%m-%d").tolist() == [
        "06-09",
        "06-10",
        "06-11",
        "06-12",
    ]
    share = np.array([12, 24, 24, 12]) * term / 72  # bars held on each of the days
    assert np.allclose(got[got != 0], np.array([0, 10.0, 0, 0]) - share)


def test_the_drift_can_come_from_other_bars() -> None:
    """`drift_span` is the pool of the drift term; a year it leaves out has no drift under d."""
    market, trades = walk(), batch(walk())
    early = ("2020-01-01", "2020-12-31")
    blind = {"window": "year", "variant": "c"}
    got = excess.per_trade(trades, market, DEAR, SPAN, blind, drift_span=early)
    term, _ = tradelevel.drift_term(
        trades, market, early, "year", "c", DEAR["point_value"]
    )
    own = excess.per_trade(trades, market, DEAR, SPAN, blind)
    assert np.array_equal(got["drift"], term) and not np.allclose(
        got["drift"], own["drift"]
    )
    assert np.array_equal(got["profit"], own["profit"])
    days = excess.daily(trades, market, DEAR, SPAN, blind, drift_span=early)
    assert np.allclose(
        days.sum(axis=1), got.groupby("variant_id")["excess"].sum()[days.index]
    )
    with pytest.raises(AssertionError, match="2021"), np.errstate(invalid="ignore"):
        excess.per_trade(trades, market, DEAR, SPAN, GATE, drift_span=early)


def test_a_trade_outside_the_window_is_refused() -> None:
    """A day matrix that dropped a trade would break the sum without saying so."""
    market, trades = walk(), batch(walk())
    with pytest.raises(AssertionError, match="outside"):
        excess.daily(
            trades, market, FREE, ("2020-01-01", "2020-12-31"), GATE, drift_span=SPAN
        )
