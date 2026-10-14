#!/usr/bin/env python3
"""seasonality on synthetic trades: an hour that carries the result is found after BH; spread trades find nothing."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.readings.seasonality import cells, many, null, one  # noqa: E402

CFG = {
    "shuffle": {"draws": 2000, "seed": 7},
    "verdict": {"min_trades": 30, "fdr_q": 0.05},
}


def trades(hot_hour: int | None, seed: int = 0, n: int = 1500) -> pd.DataFrame:
    """Three years of trades at random UTC hours; P&L noise, plus a payoff at `hot_hour`."""
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2020-01-01")
    opened = start + pd.to_timedelta(
        np.sort(rng.integers(0, 3 * 365 * 24, n)), unit="h"
    )
    pnl = rng.normal(-10.0, 100.0, n)
    if hot_hour is not None:
        pnl[opened.hour == hot_hour] += 300.0
    return pd.DataFrame(
        {
            "Open time": opened,
            "Close time": opened + pd.Timedelta(hours=2),
            "Profit/Loss": pnl,
            "Size": rng.choice([1.0, 2.0], n),
            "identity": f"s{seed}",
        }
    ).assign(**{"Profit/Loss": lambda f: f["Profit/Loss"] * f["Size"]})


def test_hot_hour_is_the_result() -> None:
    """Known answer: one hour pays, the rest loses -> fragil, resting on that hour."""
    placed = cells.place(trades(14), "UTC")
    got = one.run("x", placed, CFG)
    s = got["summary"]
    assert s["verdict"] == "fragil", s
    assert s["cell"].startswith("hora·") and "14h UTC" in s["cell"], s
    assert s["rest_pnl"] <= 0, s


def test_spread_trades_find_nothing() -> None:
    """Known answer: pure noise across the calendar -> repartido."""
    got = one.run("x", cells.place(trades(None, seed=3), "UTC"), CFG)
    assert got["summary"]["verdict"] == "repartido", got["summary"]


def test_one_hot_july_is_not_a_season() -> None:
    """A single July with a huge result is one block, not three Julys: the month null does not name it."""
    t = trades(None, seed=4)
    july = (t["Open time"].dt.year == 2021) & (t["Open time"].dt.month == 7)
    t.loc[july, "Profit/Loss"] += 400.0 * t.loc[july, "Size"]
    placed = cells.place(t, "UTC")
    values = placed["per_lot"].to_numpy()
    codes = placed["mes·apertura"].to_numpy() - 1
    by_block = null.relabel_blocks(
        values,
        placed["block·apertura"].to_numpy(),
        null.onehot(codes, 12),
        2000,
        np.random.default_rng(5),
    )
    assert by_block[6] > 0.05, by_block[6]
    # shuffling trades one by one would name it: that is the trap the block null avoids
    by_trade = null.within_strata(
        values,
        np.zeros(values.size),
        null.onehot(codes, 12),
        2000,
        np.random.default_rng(5),
    )
    assert by_trade[6] < 0.001, by_trade[6]


def test_thin_cells_are_shown_not_tested() -> None:
    """A cell under min_trades is listed as «sin datos suficientes» and joins no BH family."""
    got = one.run(
        "x",
        cells.place(trades(None, seed=5, n=200), "UTC"),
        CFG,
    )
    hours = next(t for t in got["tabs"] if t["name"] == "hora")
    table = next(b for b in hours["blocks"] if b["kind"] == "table")
    assert "sin datos suficientes" in [r[-1] for r in table["rows"]]


def test_eetus_is_new_york_plus_seven() -> None:
    """EETUS 16:00 in January is 14:00 UTC (NY 09:00 = UTC-5); a skipped hour is NaT."""
    got = cells.utc(
        pd.Series(pd.to_datetime(["2021-01-15 16:00", "2021-03-14 09:30"])), "EETUS"
    )
    assert got.iloc[0] == pd.Timestamp("2021-01-15 14:00") and pd.isna(got.iloc[1])


def test_population_counts_against_chance() -> None:
    """Two hot strategies and two noise ones: two found, the binomial says more than chance."""
    t = pd.concat([trades(14, 10), trades(9, 11), trades(None, 12), trades(None, 13)])
    names = pd.Series({f"s{i}": f"Strategy {i}" for i in (10, 11, 12, 13)})
    got = many.run(t, names, "UTC", CFG, [])
    s = got["population"]["summary"]
    assert s["found"] == 2 and s["p_block"] < 0.05, s
    assert set(got["panel"]["verdict"]) == {"fragil", "repartido"}


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
