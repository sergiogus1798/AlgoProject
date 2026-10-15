#!/usr/bin/env python3
"""R3 of the gate (level 1a): a trader with no timing has no excess under the drift term that
fits how it trades, a window under a quarter is refused, and the skewness-kurtosis t reduces
to its closed form."""

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines.market.calibrate import atr  # noqa: E402
from studies.screening.analysis import tradelevel  # noqa: E402
from studies.screening.gate import level1a  # noqa: E402

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
    "triple": 4,
    "rollover": 23,
}


def bars(calm: tuple[int, int], wild: tuple[int, int], seed: int = 0) -> pd.DataFrame:
    """Hourly bars, December 2019 to mid January 2022, each open the close before, prices in whole cents.

    Args:
        calm, wild: Mean move in cents per bar of the calm and of the wild bars (blocks of 40
            bars, a range of 0.10 and of 1.50), one figure for 2020 and one for 2021 on.
    """
    index = pd.date_range("2019-12-20", "2022-01-15", freq="1h")
    rng = np.random.default_rng(seed)
    quiet = (np.arange(len(index)) // 40) % 2 == 0
    late = (index.year > 2020).astype(int)
    cents = np.where(quiet, np.array(calm)[late], np.array(wild)[late]) + rng.integers(
        -3, 4, len(index)
    )
    close = 500.0 + cents.cumsum() / 100
    open_ = np.r_[500.0, close[:-1]]
    reach = np.where(quiet, 0.05, 0.75)
    return pd.DataFrame(
        {
            "Open": open_,
            "High": np.maximum(open_, close) + reach,
            "Low": np.minimum(open_, close) - reach,
            "Close": close,
        },
        index=index,
    )


def held(
    frame: pd.DataFrame, cuts: np.ndarray, side: str = "Buy", size: float = 1.0
) -> pd.DataFrame:
    """Back-to-back trades between consecutive bar positions: always in the market."""
    return pd.DataFrame(
        {
            "identity": "x",
            "Type": side,
            "Open time": frame.index[cuts[:-1]],
            "Close time": frame.index[cuts[1:]],
            "Size": size,
            "sample": "OOS",
        }
    )


def always_in(frame: pd.DataFrame, last: str = SPAN[1], seed: int = 1) -> np.ndarray:
    """Bar positions cutting [2020, last] into holds that end at every quarter start."""
    inside = np.arange(len(frame))[frame.index.slice_indexer(SPAN[0], last)]
    starts = inside[np.r_[True, np.diff(frame.index[inside].quarter) != 0]]
    some = np.random.default_rng(seed).choice(inside, 300, replace=False)
    return np.unique(np.r_[starts, some, inside[-1] + 1])


def sized_by_atr(frame: pd.DataFrame, last: str, side: str) -> pd.DataFrame:
    """A one-bar trade on every bar of [2020, last], sized 1 / ATR as the doctrine sizes."""
    inside = np.arange(len(frame))[frame.index.slice_indexer(SPAN[0], last)]
    size = 1.0 / np.r_[np.nan, atr(frame)[:-1]][inside]
    keep = np.isfinite(size)
    return pd.DataFrame(
        {
            "identity": "x",
            "Type": side,
            "Open time": frame.index[inside[keep]],
            "Close time": frame.index[inside[keep] + 1],
            "Size": size[keep],
            "sample": "OOS",
        }
    )


def gross(trades: pd.DataFrame, frame: pd.DataFrame) -> np.ndarray:
    """Each trade's P/L open to open at no cost, point value 1."""
    opened = frame["Open"]
    sign = np.where(trades["Type"] == "Sell", -1.0, 1.0)
    return (
        sign
        * trades["Size"].to_numpy()
        * (
            opened[trades["Close time"]].to_numpy()
            - opened[trades["Open time"]].to_numpy()
        )
    )


def excess(
    trades: pd.DataFrame, frame: pd.DataFrame, window: str, variant: str
) -> np.ndarray:
    """Gross P/L minus the drift term of one variant."""
    return (
        gross(trades, frame)
        - tradelevel.drift_term(trades, frame, SPAN, window, variant, 1.0)[0]
    )


def gate(
    trades: pd.DataFrame, frame: pd.DataFrame, costs: dict, **drift: object
) -> tuple:
    """level1a.run on one harvest: (its facts, the table it wrote)."""
    cfg = {"drift": {"window": "year", "variant": "b", "se_skew_kurt": True, **drift}}
    with tempfile.TemporaryDirectory() as out:
        data = {
            "trades": trades,
            "bars": frame,
            "costs": costs,
            "out": Path(out),
            "market": {"windows": {"OOS": SPAN}},
        }
        facts = level1a.run(data, pd.Index(trades["identity"].unique()), cfg)
        written = pd.read_parquet(Path(out) / "operaciones.parquet")
    pd.testing.assert_frame_equal(written, data["oos"])
    return facts, written


def test_always_long_and_always_in_has_no_excess_with_any_window() -> None:
    """Constant size, never out: all it made is the market's own move, so the excess adds up
    to zero — over the whole of oos1 with today's term (a), and inside every calendar window
    with the per-window one (b), whichever window. A short the same."""
    frame = bars(calm=(4, 4), wild=(4, 4))
    cuts = always_in(frame)
    for side in ("Buy", "Sell"):
        trades = held(frame, cuts, side)
        assert abs(gross(trades, frame).sum()) > 500  # it did make (or lose) money
        for window in tradelevel.WINDOWS:
            _, table = gate(trades, frame, FREE, window=window, variant="a")
            assert abs(table["excess"].sum()) < 1e-6, (side, window)
            _, table = gate(trades, frame, FREE, window=window, variant="b")
            assert table.groupby("window")["excess"].sum().abs().max() < 1e-6, (
                side,
                window,
            )
            assert table["window"].nunique() == 24 // tradelevel.WINDOWS[window][0]


def test_a_window_under_a_quarter_is_refused() -> None:
    """`month` (or anything that is not year, semester or quarter) stops the level, whatever
    the variant: near a trade's own hold the window's drift is the trade's move."""
    frame = bars(calm=(4, 4), wild=(4, 4))
    trades = held(frame, always_in(frame))
    for variant in tradelevel.VARIANTS:
        for window in ("month", "week", "oos1"):
            try:
                gate(trades, frame, FREE, window=window, variant=variant)
            except AssertionError as refused:
                assert "nothing shorter" in str(refused)
            else:
                raise AssertionError(f"{window} was accepted")


def test_variant_a_is_todays_term() -> None:
    """(a) is `drift` on `mean_move` over the whole of oos1, the gate's term to the bit."""
    frame = bars(calm=(6, 1), wild=(-2, 3))
    trades = held(frame, always_in(frame), size=1.7)
    today = tradelevel.drift(
        trades, frame, tradelevel.mean_move(frame, {"OOS": SPAN}), 1.0
    )
    assert np.array_equal(
        tradelevel.drift_term(trades, frame, SPAN, "year", "a", 1.0)[0], today
    )


def test_b_stops_paying_for_being_in_during_the_good_year() -> None:
    """2020 rises 6 cents a bar, 2021 one. A long that is always in during 2020 and never in
    2021 has no timing inside any year. (a) charges it the two-year mean move and leaves it
    exactly bars x (2020's move - the two years' move) of free excess; (b) leaves nothing."""
    frame = bars(calm=(6, 1), wild=(6, 1))
    trades = held(frame, always_in(frame, last="2020-12-31"))
    change = frame["Close"].diff()[SPAN[0] : SPAN[1]]
    free = len(change["2020"]) * (change["2020"].mean() - change.mean())
    assert free > 100
    assert abs(excess(trades, frame, "year", "a").sum() - free) < 1e-6
    assert abs(excess(trades, frame, "year", "b").sum()) < 1e-6


def test_c_takes_out_what_sizing_by_volatility_leaves_by_side() -> None:
    """Calm bars rise 2 cents and wild bars fall 2: the mean bar moves nothing, but a trader
    sized 1 / ATR is big when the market rises. Entering every bar it has no timing, yet (a)
    leaves the long a positive excess and the short the same one negative; (c), the blind
    trade of the same hold at the doctrine's size, leaves both at zero."""
    frame = bars(calm=(2, 2), wild=(-2, -2))
    for side, sign in (("Buy", 1.0), ("Sell", -1.0)):
        trades = sized_by_atr(frame, SPAN[1], side)
        biased = excess(trades, frame, "year", "a").sum()
        assert sign * biased > 100, side
        assert abs(excess(trades, frame, "year", "c").sum()) < 1e-6 * abs(biased), side


def test_d_is_the_only_one_right_when_both_happen() -> None:
    """2020: calm bars rise, wild bars fall. 2021: the other way round. A long sized 1 / ATR
    that enters every bar of 2020 and none of 2021 has no timing. (a) and (b) miss the size,
    (c) pools 2021's bars into the blind trade it is compared with; only (d) reads zero."""
    frame = bars(calm=(3, -1), wild=(-1, 3))
    trades = sized_by_atr(frame, "2020-12-31", "Buy")
    left = {v: abs(excess(trades, frame, "year", v).sum()) for v in tradelevel.VARIANTS}
    assert left["d"] < 1e-6 * min(left["a"], left["b"], left["c"])
    assert min(left["a"], left["b"], left["c"]) > 100


def test_skew_kurt_t_closed_form() -> None:
    """The specification (§5.4): t = s·√(n−1) / √(1 − γ3·s + (γ4−1)/4·s²). With γ3 = 0 the
    middle term vanishes and with γ4 = 3 the last is (3−1)/4·s² = s²/2, so
    t = s·√(n−1) / √(1 + s²/2) — the row's shorthand, the same thing. Its numerator is the
    usual t: with s = mean / sd over n, s·√(n−1) = mean / sd over (n−1) × √n."""
    s, n = np.array([0.02, 0.1814, 0.7]), np.array([40, 196, 1000])
    closed = s * np.sqrt(n - 1) / np.sqrt(1 + s * s / 2)
    assert np.allclose(tradelevel.skew_kurt_t(s, n, 0.0, 3.0), closed, rtol=1e-12)
    # the specification's own table (§5.6), strategy A: s = 0.1814, n = 196
    for skew, kurt, want in ((0.0, 3.0, 2.51), (-1.5, 8.0, 2.20), (1.5, 8.0, 2.86)):
        assert abs(tradelevel.skew_kurt_t(0.1814, 196, skew, kurt) - want) < 0.005


def test_t_skew_kurt_reads_the_columns_own_moments() -> None:
    """Per strategy: the plain t over the radicand of its own skewness and kurtosis, a loss
    tail lowering it and a gain tail raising it, and the AR(1) column cut as t() cuts its own."""
    rng = np.random.default_rng(5)
    tail = rng.exponential(1.0, 400) - 1.0  # skew +2, kurtosis 9
    frame = pd.concat(
        [
            pd.DataFrame({"identity": name, "x": 0.15 + sign * tail})
            for name, sign in (("gains", 1.0), ("losses", -1.0))
        ],
        ignore_index=True,
    )
    plain, got = tradelevel.t(frame, "x"), tradelevel.t_skew_kurt(frame, "x")
    assert got["iid"]["losses"] < plain["iid"]["losses"]
    assert got["iid"]["gains"] > plain["iid"]["gains"]
    assert np.allclose(got["ar1"] / got["iid"], plain["ar1"] / plain["iid"], rtol=1e-12)
    assert list(got.columns) == ["n", "iid", "ar1"]
    for name, rows in frame.groupby("identity"):
        x = rows["x"].to_numpy()
        z = (x - x.mean()) / x.std()
        want = plain["iid"][name] / np.sqrt(
            1
            - (z**3).mean() * x.mean() / x.std()
            + ((z**4).mean() - 1) / 4 * (x.mean() / x.std()) ** 2
        )
        assert abs(got["iid"][name] - want) < 1e-9


def test_the_level_reprices_and_judges_the_excess() -> None:
    """`pnl` and `cost` are the common repricer's (a declared spread is charged, and the two
    add up to the raw move), `excess` is `pnl - drift`, and the fact is the AR(1) t of that
    column — with the skewness-kurtosis standard error only when the config says so."""
    frame = bars(calm=(4, 4), wild=(4, 4))
    cuts = always_in(frame)
    both = pd.concat(
        [
            held(frame, cuts[::2]).assign(identity="b"),
            held(frame, cuts).assign(identity="a"),
        ],
        ignore_index=True,
    )
    costs = {**FREE, "spread": 0.30, "slippage": 0.10}
    for corrected, t in ((True, tradelevel.t_skew_kurt), (False, tradelevel.t)):
        facts, table = gate(both, frame, costs, se_skew_kurt=corrected)
        assert list(table.columns) == [
            "identity",
            "open_time",
            "close_time",
            "side",
            "lots",
            "pnl",
            "cost",
            "drift",
            "excess",
            "window",
            "stop",
        ]
        mine = table[table["identity"] == "a"]
        assert np.allclose(
            mine["pnl"] + mine["cost"], gross(held(frame, cuts), frame), atol=1e-9
        )
        assert np.allclose(
            mine["cost"], 0.50, atol=1e-9
        )  # spread + slippage in and out
        assert np.allclose(table["excess"], table["pnl"] - table["drift"], atol=1e-12)
        assert list(facts.columns) == ["drift_excess_t"] and set(facts.index) == {
            "a",
            "b",
        }
        assert np.allclose(
            facts["drift_excess_t"], t(table, "excess")["ar1"].reindex(facts.index)
        )
        assert (facts["drift_excess_t"] < 0).all()  # no timing, and it paid costs


def test_a_strategy_the_cascade_dropped_is_not_repriced() -> None:
    """Only the identities in `alive` reach the table (file and `data["oos"]`) and the facts:
    one that fell at level 0 has no row. With everyone alive, everyone is there."""
    frame = bars(calm=(4, 4), wild=(4, 4))
    cuts = always_in(frame)
    both = pd.concat(
        [
            held(frame, cuts[::2]).assign(identity="fell"),
            held(frame, cuts).assign(identity="alive"),
        ],
        ignore_index=True,
    )
    cfg = {"drift": {"window": "year", "variant": "b", "se_skew_kurt": True}}
    for alive in (["alive"], ["alive", "fell"]):
        with tempfile.TemporaryDirectory() as out:
            data = {
                "trades": both,
                "bars": frame,
                "costs": FREE,
                "out": Path(out),
                "market": {"windows": {"OOS": SPAN}},
            }
            facts = level1a.run(data, pd.Index(alive), cfg)
            written = pd.read_parquet(Path(out) / "operaciones.parquet")
        assert set(written["identity"]) == set(data["oos"]["identity"]) == set(alive)
        assert list(facts.index) == alive and facts["drift_excess_t"].notna().all()
        assert (written["identity"] == "alive").sum() == len(cuts) - 1


if __name__ == "__main__":
    for check in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        check()
        print("ok", check.__name__)
