#!/usr/bin/env python3
"""Known answers for level 1b's one-pass facts: R5c, R8, R9b."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.screening.analysis import onepass, tradelevel
from studies.screening.gate import level1b_onepass

CFG = {
    "drift": {"se_skew_kurt": False},
    "cost_stress": {"k": 1.25},
    "concentration": {"drop_trades": 3, "drop_period": "quarter"},
    "mae": {"percentile": 95},
}


def table(n: int = 40, seed: int = 1) -> pd.DataFrame:
    """A per-trade table of one identity."""
    rng = np.random.default_rng(seed)
    pnl = rng.normal(10, 50, n)
    return pd.DataFrame(
        {
            "identity": "a",
            "open_time": pd.date_range("2020-01-01", periods=n, freq="10D"),
            "pnl": pnl,
            "cost": 4.0,
            "excess": pnl - 1.0,
        }
    )


def test_k_one_is_r3_t() -> None:
    """With k = 1 the cost-stressed t is R3's own."""
    oos = table()
    assert np.allclose(
        onepass.t_cost(oos, 1.0, tradelevel.t), tradelevel.t(oos, "excess")["ar1"]
    )
    assert (
        onepass.t_cost(oos, 1.25, tradelevel.t)["a"]
        < tradelevel.t(oos, "excess")["ar1"]["a"]
    )


def test_edge_is_gross_over_cost() -> None:
    """The edge is the gross mean over the cost."""
    oos = table().assign(pnl=6.0, cost=2.0)
    assert onepass.edge_mean(oos)["a"] == 4.0


def test_drop_from_constant_series_keeps_the_mean() -> None:
    """Dropping from a constant series keeps its mean."""
    oos = table(60).assign(excess=5.0)
    oos["excess"] += np.random.default_rng(2).normal(
        0, 1e-9, 60
    )  # t needs a nonzero sd
    t = onepass.t_without(oos, tradelevel.t, 3, "quarter")
    assert (t > 1e3).all().all()  # the mean is still 5 over a ~0 sd


def test_best_trades_are_removed() -> None:
    """The best trades are removed before t."""
    oos = table(30).assign(excess=np.random.default_rng(3).normal(1, 1, 30))
    oos.loc[0, "excess"] = 1e6
    oos.loc[1:2, "excess"] = 5e5
    rest = tradelevel.t(oos.iloc[3:], "excess")["ar1"]["a"]
    assert (
        onepass.t_without(oos, tradelevel.t, 3, "quarter")["t_sin_3_mejores"]["a"]
        == rest
    )


def test_mae_all_equal_is_that_value() -> None:
    """With every MAE equal the percentile is that value."""
    tr = pd.DataFrame({"identity": ["a"] * 20, "MAE ($)": -150.0})
    assert onepass.mae_pct(tr, 100.0, 95)["a"] == 1.5


def test_level_shape_and_empty() -> None:
    """The level's columns, one known value and the empty harvest."""
    oos = table()
    tr = pd.DataFrame(
        {"identity": "a", "sample": "OOS", "MAE ($)": -50.0}, index=oos.index
    )
    out = level1b_onepass.run(
        {"oos": oos, "trades": tr, "market": {"risk": 100.0}}, pd.Index(["a", "b"]), CFG
    )
    assert (
        list(out.columns) == list(level1b_onepass.FACTS)
        and out.loc["a", "mae_p95_r"] == 0.5
    )
    assert out.loc["b"].isna().all()
    assert level1b_onepass.run({}, pd.Index(["a"]), CFG).isna().all().all()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
