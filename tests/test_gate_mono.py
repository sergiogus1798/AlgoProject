"""Known answers of the gate's monkey (level 3c): a draw scores z ~ 0, foresight scores high,
a seed replays bit for bit, and every drawn trade pays the declared spread and slippage."""

import numpy as np
import pandas as pd

from engines.market.feed.scale import WEEK
from engines.nulls import windowed
from studies.screening.analysis import tradelevel
from studies.screening.gate import level3c

SPAN = ("2020-01-01", "2021-12-31")
COSTS = {
    "point_value": 2.0,
    "tick_size": 0.01,
    "spread": 0.05,
    "slippage": 0.01,
    "commission_method": "SizeBased",
    "commission": 0.0,
    "swap_long": 0.0,
    "swap_short": 0.0,
    "triple": 4,
    "rollover": 23,
}
TRADES, DRAWS = 150, 400


def bars(flat: bool = False) -> pd.DataFrame:
    """Three years of hourly bars on a random walk, or with a constant open.

    Args:
        flat: Every open the same price; the ranges still move, so the ATR is usable.
    """
    rng = np.random.default_rng(1)
    index = pd.date_range("2019-07-01", "2022-06-30", freq="h")
    opened = (
        np.full(len(index), 100.0)
        if flat
        else 100 + np.cumsum(rng.normal(0, 0.1, len(index)))
    )
    wide = rng.uniform(0.05, 0.4, len(index))
    return pd.DataFrame(
        {"Open": opened, "High": opened + wide, "Low": opened - wide, "Close": opened},
        index=index,
    )


def shared(frame: pd.DataFrame) -> dict:
    """The grid level 3c builds: oos1 is SPAN, the windows are calendar years."""
    inside = np.arange(len(frame))[frame.index.slice_indexer(*SPAN)]
    return windowed.grid(
        frame, inside, tradelevel.calendar(frame.index[inside], "year")
    )


def seed_trades(grid: dict, rng: np.random.Generator) -> dict:
    """Arbitrary long trades inside the sample, to draw strategies from."""
    entry = np.sort(rng.choice(grid["eligible"][:-50], TRADES, replace=False))
    return windowed.located(
        grid,
        entry,
        entry + rng.integers(1, 40, TRADES),
        rng.uniform(0.1, 1.0, TRADES),
        np.ones(TRADES),
        tradelevel.calendar(grid["time"][entry], "year"),
    )


def table(grid: dict, mine: dict, identity: str) -> pd.DataFrame:
    """One strategy's rows of the per-trade table, as level 1a writes them."""
    real = {
        "entries": mine["entry"][None],
        "holds": mine["hold"][None],
        "sizes": mine["size"][None],
    }
    pnl = windowed.price(grid, mine, real, COSTS)[0][0]
    opened = grid["time"][mine["entry"]]
    return pd.DataFrame(
        {
            "identity": identity,
            "open_time": opened,
            "close_time": grid["time"][mine["entry"] + mine["hold"]],
            "side": mine["side"],
            "lots": mine["size"],
            "pnl": pnl,
            "window": tradelevel.calendar(opened, "year"),
        }
    )


def as_strategy(grid: dict, mine: dict, drawn: dict) -> dict:
    """The first monkey of a draw, located as if it were a real strategy."""
    entry = drawn["entries"][0]
    return windowed.located(
        grid,
        entry,
        entry + drawn["holds"][0],
        drawn["sizes"][0],
        mine["side"],
        tradelevel.calendar(grid["time"][entry], "year"),
    )


def gate(frame: pd.DataFrame, oos: pd.DataFrame, seed: int | None) -> pd.DataFrame:
    """Level 3c over a per-trade table."""
    data = {
        "bars": frame,
        "market": {"windows": {"OOS": SPAN}},
        "costs": COSTS,
        "oos": oos,
    }
    cfg = {"monkey": {"draws": DRAWS, "seed": seed}, "drift": {"window": "year"}}
    return level3c.run(data, pd.Index(oos["identity"].unique()), cfg)


def test_a_draw_scores_zero_on_average() -> None:
    """A strategy that IS a monkey has z ~ N(0, 1) over seeds: mean near 0, spread near 1."""
    frame = bars()
    grid = shared(frame)
    base = seed_trades(grid, np.random.default_rng(2))
    scores = []
    for seed in range(40):
        rng = np.random.default_rng([3, seed])
        mine = as_strategy(grid, base, windowed.draw(grid, base, "timing", 1, rng))
        seen = table(grid, mine, "s")["pnl"].mean()
        scores.append(
            windowed.z(seen, windowed.means(grid, mine, COSTS, "timing", DRAWS, rng))
        )
    spot, spread = np.mean(scores), np.std(scores)
    assert abs(spot) < 0.5 and 0.6 < spread < 1.4, (spot, spread)


def test_foresight_scores_high() -> None:
    """Entering at the bars with the best move ahead beats every monkey by many deviations."""
    frame = bars()
    grid = shared(frame)
    ok, opened, hold = grid["eligible"][:-50], frame["Open"].to_numpy(), 5
    entry = np.sort(ok[np.argsort(opened[ok + hold] - opened[ok])[-TRADES:]])
    mine = windowed.located(
        grid,
        entry,
        entry + hold,
        np.full(TRADES, 0.5),
        np.ones(TRADES),
        tradelevel.calendar(grid["time"][entry], "year"),
    )
    got = gate(frame, table(grid, mine, "seer"), 5)
    assert got.loc["seer", "z_mono"] > 5 and got.loc["seer", "mono_p"] == 1 / (
        DRAWS + 1
    )
    assert got.loc["seer", "z_mono"] == got.loc["seer", "z_mono_timing"]
    assert list(got.columns) == list(level3c.FACTS) and got.notna().all(axis=None)


def test_a_seed_replays_bit_for_bit() -> None:
    """Same root, same z whatever else is in the batch; another root, other monkeys; a null
    seed is drawn fresh, returned as `mono_seed`, and replays the run when given back."""
    frame = bars()
    grid = shared(frame)
    rng = np.random.default_rng(4)
    oos = pd.concat(
        [table(grid, seed_trades(grid, rng), name) for name in ("a", "b", "c")]
    )
    first = gate(frame, oos, 11)
    pd.testing.assert_frame_equal(first, gate(frame, oos, 11), check_exact=True)
    pd.testing.assert_frame_equal(
        first.loc[["b"]], gate(frame, oos[oos["identity"] == "b"], 11), check_exact=True
    )
    assert not first["z_mono"].equals(gate(frame, oos, 12)["z_mono"])
    assert first["z_mono"].nunique() == 3 and (first["mono_seed"] == 11).all()
    fresh = gate(frame, oos, None)
    root = fresh["mono_seed"].iloc[0]
    assert root == int(root) and 0 <= root < 2**32
    assert root != gate(frame, oos, None)["mono_seed"].iloc[0]
    pd.testing.assert_frame_equal(fresh, gate(frame, oos, int(root)), check_exact=True)


def test_the_block_size_moves_no_monkey() -> None:
    """Pricing in small blocks gives the very draws one block gives."""
    grid = shared(bars())
    mine = seed_trades(grid, np.random.default_rng(6))
    whole = {
        rung: windowed.means(grid, mine, COSTS, rung, 50, np.random.default_rng(7))
        for rung in windowed.REDRAWS
    }
    spare, windowed.BLOCK = windowed.BLOCK, 7 * TRADES
    try:
        for rung, expected in whole.items():
            assert np.array_equal(
                expected,
                windowed.means(grid, mine, COSTS, rung, 50, np.random.default_rng(7)),
            )
    finally:
        windowed.BLOCK = spare


def test_every_draw_pays_spread_and_slippage_and_stays_in_its_window() -> None:
    """On a flat market a drawn trade's P/L is exactly minus its declared cost; its entry is
    in the real trade's calendar window, its exit inside the sample, its size c / ATR."""
    grid = shared(bars(flat=True))
    mine = seed_trades(grid, np.random.default_rng(8))
    for rung, (redraw, flat) in windowed.REDRAWS.items():
        drawn = windowed.draw(grid, mine, rung, 30, np.random.default_rng(9))
        pnl, cost = windowed.price(grid, mine, drawn, COSTS)
        charged = (
            COSTS["point_value"]
            * drawn["sizes"]
            * (COSTS["spread"] + 2 * COSTS["slippage"])
        )
        assert np.allclose(cost, charged) and (cost > 0).all()
        assert np.array_equal(pnl, -np.round(cost, 2))
        assert (
            (drawn["entries"] >= mine["lo"]) & (drawn["entries"] <= mine["hi"])
        ).all()
        assert (drawn["entries"] + drawn["holds"] <= grid["last"]).all()
        assert redraw or (drawn["holds"] == mine["hold"]).all()
        risk = drawn["sizes"] * (1.0 if flat else grid["atr"][drawn["entries"]])
        assert np.allclose(risk, risk.flat[0])


def hours_of(grid: dict, entries: np.ndarray) -> np.ndarray:
    """Clock hour of the bar each entry sits on."""
    return grid["hour"][entries]


def test_monkeys_enter_only_in_the_strategys_own_hours_with_its_counts() -> None:
    """A strategy that enters only at 15:00 gives monkeys that enter only at 15:00, trade for
    trade; one with entries at two hours keeps both counts in every monkey."""
    grid = shared(bars())
    rng = np.random.default_rng(10)
    at = lambda h: grid["eligible"][grid["hour"][grid["eligible"]] == h][:-50]  # noqa: E731
    for counts in ({15: 60}, {9: 40, 15: 25}):
        entry = np.sort(
            np.concatenate(
                [rng.choice(at(h), n, replace=False) for h, n in counts.items()]
            )
        )
        mine = windowed.located(
            grid,
            entry,
            entry + 5,
            np.full(len(entry), 0.5),
            np.ones(len(entry)),
            tradelevel.calendar(grid["time"][entry], "year"),
        )
        for rung in windowed.REDRAWS:
            drawn = windowed.draw(grid, mine, rung, 50, np.random.default_rng(11))
            for h, n in counts.items():
                assert (
                    (hours_of(grid, drawn["entries"]) == h).sum(axis=1) == n
                ).all(), (rung, h)
            assert set(np.unique(hours_of(grid, drawn["entries"]))) == set(counts)


def test_the_session_mask_is_respected() -> None:
    """With the feed's session given, no monkey lands on a bar outside it (here Saturday and
    Sunday, and the 15:00 hour of every day, are out; the strategy trades at 14:00)."""
    frame = bars()
    inside = np.arange(len(frame))[frame.index.slice_indexer(*SPAN)]
    minute = (np.arange(WEEK) % 1440) // 60
    week = (np.arange(WEEK) // 1440 < 5) & (minute != 15)
    grid = windowed.grid(
        frame, inside, tradelevel.calendar(frame.index[inside], "year"), week
    )
    assert not (grid["hour"][grid["eligible"]] == 15).any()
    ok = grid["by_hour"][14][:-50]
    entry = np.sort(np.random.default_rng(12).choice(ok, 50, replace=False))
    mine = windowed.located(
        grid,
        entry,
        entry + 3,
        np.ones(50),
        np.ones(50),
        tradelevel.calendar(grid["time"][entry], "year"),
    )
    drawn = windowed.draw(grid, mine, "timing", 40, np.random.default_rng(13))
    days = frame.index.dayofweek.to_numpy()[drawn["entries"]]
    assert (days < 5).all() and (hours_of(grid, drawn["entries"]) == 14).all()
