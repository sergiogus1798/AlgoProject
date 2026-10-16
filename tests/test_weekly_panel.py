"""The weekly excess panel on three trades worked out by hand, and the trade-list fingerprint."""

import numpy as np
import pandas as pd
import pytest

from engines.variants import fingerprint
from engines.weekly import panel

WINDOW = ("2020-01-01", "2020-12-31")
# 1 of spread + 2 x slippage and 2 of commission per lot, no swap: every trade is charged 3 x lots
COSTS = {
    "point_value": 1.0,
    "tick_size": 0.01,
    "spread": 0.5,
    "slippage": 0.25,
    "commission_method": "SizeBased",
    "rounds": True,
    "commission": 2.0,
    "swap_long": 0.0,
    "swap_short": 0.0,
    "triple": 2,
    "rollover": 0,
}


def market() -> pd.DataFrame:
    """Hourly bars, weekends included, rising exactly 1.0 per bar: the drift of h bars is h."""
    index = pd.date_range("2019-12-01", "2021-01-31 23:00", freq="h")
    opened = 100.0 + np.arange(len(index))
    return pd.DataFrame(
        {
            "Open": opened,
            "High": opened + 1.5,
            "Low": opened - 0.5,
            "Close": opened + 1.0,
        },
        index=index,
    )


def three() -> pd.DataFrame:
    """A long inside one week, a short held over a weekend, a long of another variant in December."""
    return pd.DataFrame(
        {
            "variant_id": ["v1", "v1", "v2"],
            "Type": ["Buy", "Sell", "Buy"],
            "Size": [1.0, 2.0, 0.5],
            "Open time": pd.to_datetime(
                ["2020-01-06 10:00", "2020-01-10 12:00", "2020-12-29 00:00"]
            ),
            "Close time": pd.to_datetime(
                ["2020-01-08 10:00", "2020-01-13 09:00", "2020-12-31 00:00"]
            ),
        }
    )


@pytest.mark.parametrize("variant", ["b", "d"])
def test_three_trades_by_hand(variant: str) -> None:
    """Profit, drift, net, gross, the week each lands in and the totals per year, all known."""
    trades = three()
    per = panel.per_trade(
        trades, market(), COSTS, WINDOW, {"window": "year", "variant": variant}
    )
    held, side, lots = (
        np.array([48, 69, 48]),
        np.array([1, -1, 1]),
        trades["Size"].to_numpy(),
    )
    assert np.allclose(per["profit"], side * lots * held - 3 * lots)
    assert np.allclose(per["drift"], side * lots * held)
    assert np.allclose(per["net"], -3 * lots) and np.allclose(per["gross"], 0)
    got = panel.weekly(per, WINDOW, units=["v1", "v2", "v3"])
    net, gross = got["net"], got["gross"]
    assert net.shape == gross.shape == (53, 3) and net.index.equals(gross.index)
    assert net.index[0] == pd.Timestamp("2019-12-30") and net.index[-1] == pd.Timestamp(
        "2020-12-28"
    )
    assert (net.index.dayofweek == 0).all()
    want = pd.DataFrame(0.0, index=net.index, columns=net.columns)
    want.loc["2020-01-06", "v1"] = -3.0
    want.loc[
        "2020-01-13", "v1"
    ] = -6.0  # open over the weekend: whole in its closing week
    want.loc["2020-12-28", "v2"] = -1.5
    assert np.allclose(net, want) and np.allclose(gross - net, -want)
    years = 365 / 365.25  # core.metrics.years: elapsed days, no +1
    assert np.allclose(panel.per_year(net, WINDOW), np.array([-9.0, -1.5, 0.0]) / years)
    assert np.allclose(panel.per_year(gross, WINDOW), 0.0)
    assert panel.straddle(per["open"], per["close"]) == pytest.approx(1 / 3)


def test_panel_refuses_a_trade_outside_the_window() -> None:
    """A close outside the window is the caller's mistake, never a silent drop."""
    per = pd.DataFrame(
        {
            "variant_id": ["a"],
            "close": pd.to_datetime(["2021-01-04"]),
            "net": [1.0],
            "gross": [1.0],
        }
    )
    with pytest.raises(AssertionError):
        panel.weekly(per, WINDOW)


def test_gap_to_sqx_counts_the_units_off() -> None:
    """Sum of the repriced P/L against SQX's NetProfit, with the tolerance given."""
    per = panel.per_trade(
        three(), market(), COSTS, WINDOW, {"window": "year", "variant": "b"}
    )
    sqx = pd.Series({"v1": -99.0, "v2": 23.0, "v3": 0.0})
    share, off = panel.sqx_gap(per, sqx, tolerance=0.1)
    assert share == pytest.approx(1 / 3) and off.to_dict() == {"v2": -0.5}
    assert panel.sqx_gap(per, sqx, tolerance=1.0)[0] == 0
    assert panel.sqx_gap(per, sqx, relative=0.05)[0] == 0
    # the allowance is the LARGER of floor and share, not their sum: 0.5 off on 23 needs 2.2 %
    assert panel.sqx_gap(per, sqx, tolerance=0.1, relative=0.01)[0] == pytest.approx(
        1 / 3
    )
    assert panel.sqx_gap(per, sqx, tolerance=0.1, relative=0.03)[0] == 0


def test_straddle_counts_only_monday_and_tuesday_closes_after_a_weekend() -> None:
    """Fri -> Mon and Thu -> Tue count; Fri -> Wed, Mon -> Tue and Mon -> Fri do not."""
    opened = pd.to_datetime(
        ["2020-01-10", "2020-01-09", "2020-01-10", "2020-01-13", "2020-01-13"]
    )
    closed = pd.to_datetime(
        ["2020-01-13", "2020-01-14", "2020-01-15", "2020-01-14", "2020-01-17"]
    )
    assert panel.straddle(opened, closed) == pytest.approx(2 / 5)


def lists() -> pd.DataFrame:
    """Mother M, an exact copy C, and D: as many trades and the same total, other trades."""

    def one(name: str, exits: list[str], results: list[float]) -> pd.DataFrame:
        """Two long trades of one variant."""
        return pd.DataFrame(
            {
                "variant_id": name,
                "Type": "Buy",
                "Size": 1.0,
                "Open price": [10.0, 20.0],
                "Open time": pd.to_datetime(["2020-01-06", "2020-01-08"]),
                "Close time": pd.to_datetime(exits),
                "Close price": [11.0, 21.0],
                "Profit/Loss": results,
            }
        )

    same = (["2020-01-07", "2020-01-09"], [5.0, 7.0])
    return pd.concat(
        [
            one("C", *same),
            one("D", ["2020-01-07", "2020-01-10"], [7.0, 5.0]),
            one("M", *same),
        ],
        ignore_index=True,
    )


def test_fingerprint_tells_equal_totals_from_equal_trades() -> None:
    """Same count and total but other trades: not duplicates. Identical lists: one stays, the mother."""
    trades = lists()
    assert (
        trades.groupby("variant_id")["Profit/Loss"]
        .agg(["size", "sum"])
        .nunique()
        .eq(1)
        .all()
    )
    got = fingerprint.prints(trades)
    assert got["C"] == got["M"] != got["D"]
    assert got.equals(
        fingerprint.prints(trades.sample(frac=1, random_state=0)).reindex(got.index)
    )
    kept, share = fingerprint.keep(got, first=["M"])
    assert list(kept) == ["D", "M"] and share == pytest.approx(1 / 3)
    assert list(fingerprint.keep(got)[0]) == ["C", "D"]
