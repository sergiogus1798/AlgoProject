"""Encargo 66 §3.2 and §3.9: the gate's monkey read off a priced table with PCG64 in the kernel
gives the draws and the numbers of the code it replaced, bit for bit, and leaves the generator
where numpy would."""

import numpy as np
import pandas as pd
import pytest
from numba import njit

from core import fanout
from core.paths import DATA
from engines.market import reprice
from engines.market.feed.scale import WEEK
from engines.nulls import lookup, pcg, windowed
from studies.screening.analysis import resample, tradelevel

COSTS = {"point_value": 2.0, "tick_size": 0.01, "spread": 0.05, "slippage": 0.01,
         "commission_method": "SizeBased", "commission": 0.0, "swap_long": 0.0,
         "swap_short": 0.0, "triple": 4, "rollover": 23}
HARD = COSTS | {"commission_method": "PercentageBased", "commission": 0.003, "tick_step": 0.001,
                "swap_long": -7.5, "swap_short": 2.1}
REAL = DATA / "reports" / "Test_USATEC_H1_ruptura_leaseWeb" / "Results" / "2026-10-11" / "gate"
_TABLES = {}


def old_draw(shared: dict, mine: dict, rung: str, draws: int, rng: np.random.Generator) -> dict:
    """windowed.draw as it stood at 9ec2c34, verbatim, but for the 2026-10-13 layout (N12 B): the oracle."""
    redraw, flat = windowed.REDRAWS[rung]
    n, ok = mine["entry"].size, shared["eligible"]
    u = rng.random((draws, 2, n))    # one layout for the four rungs (N12 B)
    holds = (mine["hold"][(u[:, 1] * n).astype(np.int64)] if redraw
             else np.broadcast_to(mine["hold"], (draws, n)))
    holds = np.minimum(holds, shared["last"] - mine["lo"])
    entries = np.empty(holds.shape, np.int64)
    for hour in np.unique(mine["hour"]):
        cols = np.flatnonzero(mine["hour"] == hour)
        at_hour = shared["by_hour"].get(int(hour), ok)
        first = np.searchsorted(at_hour, mine["lo"][cols])
        room = np.searchsorted(at_hour, np.minimum(mine["hi"][cols], shared["last"] - holds[:, cols]),
                               side="right") - first
        pick = first + (u[:, 0, cols] * np.maximum(room, 1)).astype(np.int64)
        entries[:, cols] = at_hour[np.minimum(pick, at_hour.size - 1)]
    holds = np.minimum(entries + holds, shared["last"]) - entries
    sizes = (np.broadcast_to(mine["size"].mean(), entries.shape) if flat
             else np.median(mine["size"] * shared["atr"][mine["entry"]]) / shared["atr"][entries])
    return {"entries": entries, "holds": holds, "sizes": sizes}


def old_means(shared: dict, mine: dict, costs: dict, rung: str, draws: int,
              rng: np.random.Generator, block: int = 200_000) -> np.ndarray:
    """windowed.means as it stood at 9ec2c34, verbatim (price() inlined): the oracle."""
    block = max(1, block // mine["entry"].size)
    out = np.empty(draws)
    for done in range(0, draws, block):
        batch = min(block, draws - done)
        drawn = old_draw(shared, mine, rung, batch, rng)
        enter, leave = drawn["entries"], drawn["entries"] + drawn["holds"]
        out[done:done + batch] = reprice.pnl(
            reprice.fills(shared["bars"], enter), reprice.fills(shared["bars"], leave),
            shared["time"][enter], shared["time"][leave], mine["side"], drawn["sizes"],
            costs)[0].mean(axis=1)
    return out


def grid(window: str = "year", week: np.ndarray | None = None, flat: bool = False) -> dict:
    """Three years of hourly bars on a random walk (or one constant open), oos1 = 2020-2021."""
    rng = np.random.default_rng(1)
    index = pd.date_range("2019-07-01", "2022-06-30", freq="h")
    opened = np.full(len(index), 100.0) if flat else 100 + np.cumsum(rng.normal(0, 0.1, len(index)))
    wide = rng.uniform(0.05, 0.4, len(index))
    frame = pd.DataFrame({"Open": opened, "High": opened + wide, "Low": opened - wide,
                          "Close": opened}, index=index)
    inside = np.arange(len(frame))[frame.index.slice_indexer("2020-01-01", "2021-12-31")]
    return windowed.grid(frame, inside, tradelevel.calendar(frame.index[inside], window), week) | {
        "window": window}


def trades(shared: dict, entry: np.ndarray, hold: np.ndarray, side: float | np.ndarray = 1.0,
           seed: int = 3) -> dict:
    """Trades at `entry` held `hold` bars, lots uniform, located on the grid."""
    entry = np.asarray(entry)
    return windowed.located(shared, entry, entry + hold, np.random.default_rng(seed).uniform(
        0.1, 1.0, entry.size), np.broadcast_to(side, entry.shape),
        tradelevel.calendar(shared["time"][entry], shared["window"]))


def scattered(shared: dict, n: int, seed: int = 5, side: float | np.ndarray = 1.0) -> dict:
    """`n` trades at random eligible bars, holds of 1 to 39 bars."""
    rng = np.random.default_rng(seed)
    entry = np.sort(rng.choice(shared["eligible"][:-50], n, replace=n > shared["eligible"].size - 50))
    return trades(shared, entry, rng.integers(1, 40, n), side)


def cases() -> dict:
    """The adversarial worlds of the prototypes: name -> (grid, trades, costs)."""
    year, quarter = grid(), grid("quarter")
    rng = np.random.default_rng(8)
    ok, last = year["eligible"], year["last"]
    week = np.zeros(WEEK, bool)
    week[np.arange(WEEK) % 1440 < 600] = True
    masked = grid(week=week)
    hole = dict(year, by_hour=dict(year["by_hour"]))        # the last year loses hour 3
    at_three = year["by_hour"][3]
    hole["by_hour"][3] = at_three[at_three < max(low for low, _ in year["bounds"].values())]
    lone = dict(year, by_hour=dict(year["by_hour"]))        # hour 4 keeps one bar in all
    lone["by_hour"][4] = year["by_hour"][4][:1]
    tied = np.repeat(ok[[100, 100, 2000, 9000]], 10)
    return {
        "longs": (year, scattered(year, 150), COSTS),
        "shorts": (year, scattered(year, 150, side=-1.0), COSTS),
        "mixed sides": (year, scattered(year, 150, side=rng.choice([-1.0, 1.0], 150)), COSTS),
        "percent commission, swap in points": (
            year, scattered(year, 150, side=rng.choice([-1.0, 1.0], 150)), HARD),
        "ties: same bar, same hold, flat prices": (grid(flat=True), trades(year, tied, 5), COSTS),
        "single trade": (year, trades(year, ok[[777]], np.array([12])), COSTS),
        "first and last bar, hold 0, hold past the end": (
            year, trades(year, np.r_[ok[:3], ok[-3:], last, ok[500]],
                         np.r_[0, 1, 30000, 0, 2, 0, 0, 40000]), COSTS),
        "empty window at the trade's hour": (
            hole, trades(year, at_three[[5, -5, -40]], np.array([3, 7, 7])), COSTS),
        "hour with one eligible bar": (
            lone, trades(year, year["by_hour"][4][[0, 200, 600]], np.array([2, 9, 400])), COSTS),
        "session mask": (masked, scattered(masked, 120), COSTS),
        "quarterly windows": (quarter, scattered(quarter, 150), HARD),
        "n = 2896": (year, scattered(year, 2896), COSTS),
    }


@pytest.mark.parametrize("name", list(cases()))
def test_table_kernel_equals_the_old_means(name: str) -> None:
    """Every rung of every adversarial world: same means, and the generator in the same state."""
    shared, mine, costs = cases()[name]
    draws = 60 if mine["entry"].size > 1000 else 700
    for rung in windowed.REDRAWS:
        seen, new = np.random.default_rng([7, 1]), np.random.default_rng([7, 1])
        want = [old_means(shared, mine, costs, rung, d, seen) for d in (draws, 3)]
        got = [windowed.means(shared, mine, costs, rung, d, new) for d in (draws, 3)]
        assert all(np.array_equal(a, b) for a, b in zip(want, got)), (name, rung)
        assert seen.bit_generator.state == new.bit_generator.state, (name, rung)


def test_blocks_and_passes_move_no_monkey(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pricing 97 candidates at a time and filling 5 rows at a time gives the same vector."""
    shared, mine, costs = cases()["mixed sides"]
    want = {r: old_means(shared, mine, costs, r, 300, np.random.default_rng(2)) for r in windowed.REDRAWS}
    monkeypatch.setattr(windowed, "BLOCK", 97)
    monkeypatch.setattr(lookup, "PASS", 5 * mine["entry"].size)
    for rung, expected in want.items():
        assert np.array_equal(expected, windowed.means(shared, mine, costs, rung, 300,
                                                       np.random.default_rng(2)))


def test_an_hour_without_bars_is_a_clear_error() -> None:
    """A trade at an hour the grid never draws raised an IndexError from numpy; it still raises one, named."""
    shared, mine, costs = cases()["longs"]
    shared = dict(shared, by_hour=shared["by_hour"] | {int(mine["hour"][0]): np.empty(0, np.int64)})
    with pytest.raises(IndexError):
        old_means(shared, mine, costs, "timing", 5, np.random.default_rng(1))
    for call in (lambda: windowed.means(shared, mine, costs, "timing", 5, np.random.default_rng(1)),
                 lambda: windowed.draw(shared, mine, "free", 5, np.random.default_rng(1))):
        with pytest.raises(IndexError, match="no eligible bar at hour"):
            call()


@njit
def _uniforms(state: np.ndarray, one: np.ndarray, out: np.ndarray) -> None:
    """`out.size` uniforms off the compiled generator."""
    high, low = state[0], state[1]
    for i in range(out.size):
        high, low = pcg.step(high, low, one)
        out[i] = pcg.uniform(high, low)
    state[0], state[1] = high, low


@pytest.mark.parametrize("seed", [0, 7, [3, 99], 2**63 + 5])
def test_pcg_is_numpys_stream_and_state(seed: int | list) -> None:
    """Uniforms equal numpy's, and so does the generator's state after them."""
    for count in (1, 2, 1000, 12345):
        seen, new, jumped = (np.random.default_rng(seed) for _ in range(3))
        state, inc = pcg.load(new)
        out = np.empty(count)
        _uniforms(state, pcg.jump(inc, 1), out)
        pcg.store(new, state)
        jumped.bit_generator.advance(count)
        assert np.array_equal(seen.random(count), out)
        assert seen.bit_generator.state == new.bit_generator.state == jumped.bit_generator.state
        leap = pcg.step(*pcg.load(np.random.default_rng(seed))[0][:2], pcg.jump(inc, count))
        assert (int(leap[0]) << 64 | int(leap[1])) == seen.bit_generator.state["state"]["state"]


def _work(key: tuple) -> np.ndarray:
    """One strategy and rung in a forked worker: the table is the parent's, only read."""
    return lookup.means(_TABLES[key], 400, resample.stream(11, f"{key[0]}|{key[1]}"))


def test_workers_share_the_table_and_agree() -> None:
    """1, 2 and 4 forked workers reading the parent's tables give what one process gives."""
    worlds = cases()
    for name in ("longs", "mixed sides", "quarterly windows"):
        shared, mine, costs = worlds[name]
        for rung in windowed.REDRAWS:
            _TABLES[name, rung] = windowed.priced(shared, mine, costs, rung)
            _TABLES[name, rung]["value"].flags.writeable = False
    alone = {key: _work(key) for key in _TABLES}
    for workers in (1, 2, 4):
        got = dict(fanout.run(_work, {key: _TABLES[key]["value"].size for key in _TABLES}, workers))
        assert got.keys() == alone.keys()
        assert all(np.array_equal(alone[key], got[key]) for key in alone), workers


@pytest.mark.skipif(not (REAL / "operaciones.parquet").exists(), reason="no gate harvest on disk")
def test_real_trades_equal_the_old_means() -> None:
    """Strategies of a real harvest (USATEC H1, read only), every rung: array_equal."""
    from core.barstore import read as read_bars
    from studies.screening.gate import inputs
    oos = pd.read_parquet(REAL / "operaciones.parquet")
    bars, costs = read_bars("USATEC_M1", "H1"), reprice.costs("USATEC_M1", "oos1")
    inside = np.arange(len(bars))[bars.index.slice_indexer(*inputs.market("USATEC_M1")["windows"]["OOS"])]
    shared = windowed.grid(bars, inside, tradelevel.calendar(bars.index[inside], "year"))
    sizes = oos.groupby("identity").size().sort_values()
    for identity in sizes.index[[0, len(sizes) // 4, len(sizes) // 2, -2, -1]]:
        own = oos[oos["identity"] == identity]
        mine = windowed.located(shared, bars.index.get_indexer(own["open_time"]),
                                bars.index.get_indexer(own["close_time"]), own["lots"].to_numpy(float),
                                own["side"].to_numpy(float), own["window"].to_numpy())
        for rung in windowed.REDRAWS:
            seen, new = resample.stream(5, str(identity)), resample.stream(5, str(identity))
            assert np.array_equal(old_means(shared, mine, costs, rung, 1500, seen),
                                  windowed.means(shared, mine, costs, rung, 1500, new)), (identity, rung)
            assert seen.bit_generator.state == new.bit_generator.state
