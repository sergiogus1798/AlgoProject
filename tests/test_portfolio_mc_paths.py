#!/usr/bin/env python3
"""Known-answer tests of the Monte Carlo path generators (F3): D, T1, T2 and the trade units."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from portfolio.common.construct.equity import blocks, days as eq_days, matrix  # noqa: E402
from portfolio.common.construct.equity import paths as eq_paths  # noqa: E402
from portfolio.common.construct.mc import judge, paths, units  # noqa: E402

FIGURES = ("closed", "float_end", "low", "high", "opened")


def make_bars(rng: np.random.Generator, start: str, end: str) -> pd.DataFrame:
    """M1 bars of a random walk on weekdays, a wick each side of the close."""
    idx = pd.date_range(start, end, freq="1min", inclusive="left")
    idx = idx[idx.dayofweek < 5]
    close = 100 + np.cumsum(rng.normal(0, 0.01, len(idx)))
    wick = np.abs(rng.normal(0, 0.01, len(idx)))
    return pd.DataFrame({"High": close + wick, "Low": close - wick, "Close": close}, index=idx)


def make_trades(rng: np.random.Generator, bars: pd.DataFrame, edge: float,
                hold: tuple[int, int] = (30, 2400), gap: tuple[int, int] = (0, 3000)) -> pd.DataFrame:
    """One position at a time over the whole of `bars`: random side, holding time and pause."""
    t, close = bars.index.to_numpy(), bars["Close"].to_numpy()
    pos, rows = int(rng.integers(10, 500)), []
    while pos < len(t) - hold[1] - 10:
        c = pos + int(rng.integers(*hold))
        side = 1 if rng.random() < 0.5 else -1
        rows.append({"Type": "Buy" if side > 0 else "Sell", "Open time": t[pos], "Close time": t[c],
                     "Open price": close[pos], "Close price": close[c - 1], "Size": 1.0,
                     "Close type": "Exit Signal", "sample": "", "Profit/Loss": side * (close[c - 1] - close[pos]) * 100 + edge})
        pos = c + int(rng.integers(*gap))
    return pd.DataFrame(rows)


def bar_world(seed: int, n_members: int, start: str, end: str, edge: float = 0.0,
              zone: str = "UTC", clones: bool = False) -> dict:
    """A synthetic pool built with the engine's own functions: bars, trades, universe tables.

    Returns:
        `sources`, `bars`, `factors`, `min_size`, `identities` and a `universe` shaped like
        `equity.store.load()` for one firm, "test". `clones` gives every member the same trades.
    """
    rng = np.random.default_rng(seed)
    bars = {f: make_bars(rng, start, end) for f in ("FA", "FB")}
    grid = blocks.grid(pd.Timestamp(start), pd.Timestamp(end), 5)
    sources, tables, low, high, daily = {}, [], {}, {}, {}
    shared = make_trades(rng, bars["FA"], edge)
    for i in range(n_members):
        feed = "FA" if clones or i % 2 == 0 else "FB"
        trades = shared if clones else make_trades(rng, bars[feed], edge)
        name = f"m{i:02d}"
        sources[name] = {"trades": trades, "feed": feed, "timeframe": "M30", "clock": "UTC", "point_value": 100.0, "symbol": "XAUUSD"}
        path = eq_paths.minute_path(trades, bars[feed], 100.0)
        table = eq_days.server_days(path, "UTC", zone)
        daily[name] = eq_days.daily_pnl(table)
        got = blocks.blocks(path, "UTC", zone, grid)
        low[name], high[name] = got["low"], got["high"]
        tables.append(table.reset_index(names="day").assign(identity=name))
    span = (pd.Timestamp(start), pd.Timestamp(end))
    frame = matrix.stack(daily, {m: span for m in sources})
    universe = {"days": {"test": pd.concat(tables, ignore_index=True)},
                "m5": {"test": {"block_days": blocks.block_days(grid, zone), "low": low,
                                "high": high}},
                "daily": frame, "monthly": matrix.monthly(frame)}
    return {"sources": sources, "bars": bars, "universe": universe, "firm": "test",
            "identities": list(sources), "min_size": {m: 1.0 for m in sources},
            "factors": {m: 1.0 / 30.0 for m in sources}}    # a unit of risk: a typical trade's move


def lenient_plan(target: float, max_loss: float, phases: int = 1, daily_loss: float = 0.9) -> dict:
    """A plan whose only binding rules are the ones the test sets."""
    stages = [{"stage": f"phase{j + 1}", "target": target, "daily_loss": daily_loss,
               "max_loss": max_loss, "max_loss_mode": "static", "daily_basis": "balance",
               "min_days": 0, "min_days_kind": "trading", "profitable_pct": None,
               "consistency": 0.0, "consistency_kind": None, "time_limit": 0, "news_ok": True,
               "weekend_ok": True} for j in range(phases)]
    return {"plan_key": "test:x:10000:USD", "firm": "test", "family": "x", "size": 10000.0,
            "price": 0, "price_ccy": "USD", "stages": stages, "flags": []}


def _days(closed: np.ndarray) -> dict:
    """A day table with no floating: the day's low and high are its own closed P&L or zero."""
    return {"closed": closed.astype(float), "float_end": np.zeros(len(closed)),
            "low": np.minimum(closed, 0.0), "high": np.maximum(closed, 0.0),
            "opened": np.ones(len(closed), dtype=np.int64)}


def _member(pnl: np.ndarray, per_day: int = 4) -> dict:
    """A hand-built unit dict: one trade a day, opened in block 0 and closed in the same block."""
    n = len(pnl)
    flat = pnl.astype(np.float32)
    return {"low": np.minimum(flat, 0), "high": np.maximum(flat, 0), "level": flat,
            "off": np.arange(n + 1, dtype=np.int64), "pnl": pnl.astype(float),
            "open_day": np.arange(n, dtype=np.int32), "open_slot": np.zeros(n, dtype=np.int32),
            "gaps": np.full(n - 1, per_day, dtype=np.int64), "n_overlap": 0, "per_day": per_day,
            "n_days": n}


def _max_drawdown(got: dict) -> np.ndarray:
    """Each path's deepest fall of its end-of-day equity from its running high."""
    equity = np.cumsum(got["closed"], axis=1) + got["float_end"]
    return (np.maximum.accumulate(np.maximum(equity, 0), axis=1) - equity).max(axis=1)


def test_constant_series_is_reproduced() -> None:
    """A block bootstrap of a constant day table is that table, whatever the block length."""
    days = {"closed": np.full(300, 7.0), "float_end": np.zeros(300), "low": np.full(300, -2.0),
            "high": np.full(300, 3.0), "opened": np.full(300, 2)}
    for mean, key in ((m, k) for m in (1, 5, 40) for k in FIGURES):
        got = paths.daily_blocks(days, 60, 50, mean, np.random.default_rng(1))
        assert got[key].shape == (50, 60) and (got[key] == days[key][0]).all(), (mean, key)
    assert got["opened"].dtype == np.int32 and got["closed"].dtype == np.float64


def test_mean_block_length() -> None:
    """The stationary bootstrap's blocks average the requested length."""
    for mean in (5, 20):
        idx = paths.indices(5000, 4000, 300, mean, np.random.default_rng(2))
        seams = (np.diff(idx, axis=1) != 1) & ~((idx[:, :-1] == 4999) & (idx[:, 1:] == 0))
        got = idx.size / (seams.sum() + len(idx))
        assert abs(got - mean) / mean < 0.05, (mean, got)


def test_daily_blocks_keep_each_days_mark_to_market() -> None:
    """Equity moves by the drawn days' own MTM P&L, and no floating outlives its block."""
    rng = np.random.default_rng(3)
    days = _days(rng.normal(0, 1, 400))
    days["float_end"] = np.where(rng.random(400) < 0.5, rng.normal(0, 3, 400), 0.0)
    history = np.round(days["closed"] + np.diff(days["float_end"], prepend=0.0), 9)
    got = paths.daily_blocks(days, 80, 200, 6, rng)
    moved = np.round(got["closed"] + np.diff(got["float_end"], prepend=0.0, axis=1), 9)
    assert np.isin(moved, history).all()
    single = paths.daily_blocks(days, 80, 200, 1, rng)
    # every day its own block: settled at once, but for two neighbours drawn in a row by chance
    assert (single["float_end"][:, :-1] != 0).mean() < 0.01 < (got["float_end"] != 0).mean()


def test_iid_days_match_gamblers_ruin() -> None:
    """Independent +1/-1 days: P(reach +4 before -6) is 6/10, and D with blocks of 1 reads it."""
    rng = np.random.default_rng(4)
    days = _days(rng.permutation(np.repeat([1.0, -1.0], 1000)))
    plan = lenient_plan(target=3.5 / 100, max_loss=5.5 / 100)       # at risk 100: +4 passes, -6 breaks
    got = paths.daily_blocks(days, 400, 20000, 1, rng)
    read = judge.figures(judge.outcomes(got, plan, np.array([[100.0]])), 1)
    assert abs(read["p_pass"][0] - 0.6) < 0.015 and abs(read["fail_max_loss"][0] - 0.4) < 0.015, read
    assert read["p_open"][0] < 0.001 and abs(read["p_pass"][0] + read["p_fail"][0] + read["p_open"][0] - 1) < 1e-12


def test_t1_single_trade_type_is_computable() -> None:
    """One member, every trade +1 a day apart: each day closes +1 and the pass day is known."""
    member = _member(np.ones(50))
    got = paths.trade_bootstrap([member], 30, 500, np.random.default_rng(5))
    assert set(np.unique(got["closed"][:, 1:])) == {1.0} and set(np.unique(got["closed"][:, 0])) <= {0.0, 1.0}
    assert (got["float_end"] == 0).all() and (got["low"] == 0).all() and (got["high"] <= 1).all()
    assert (got["opened"] == (got["closed"] > 0)).all()
    read = judge.figures(judge.outcomes(got, lenient_plan(0.05, 0.9), np.array([[100.0]])), 1)
    assert read["p_pass"][0] == 1.0 and read["t_median"][0] in (5.0, 6.0)   # 500 at 100 a day


def test_t1_destroys_comovement_t2_and_d_keep() -> None:
    """Five clones lose together: T2 and D keep it, T1 draws them apart and reads less drawdown."""
    rng = np.random.default_rng(6)
    pnl = rng.normal(0, 1, 600)
    members = [_member(pnl) for _ in range(5)]
    joint = _days(5 * pnl)
    t1 = _max_drawdown(paths.trade_bootstrap(members, 60, 3000, rng)).mean()
    t2 = _max_drawdown(paths.trade_blocks(members, 60, 3000, 10, rng)).mean()
    d = _max_drawdown(paths.daily_blocks(joint, 60, 3000, 10, rng)).mean()
    assert t1 < 0.6 * t2 and t1 < 0.6 * d, (t1, t2, d)             # sqrt(5) apart in theory
    assert abs(t2 - d) / d < 0.08, (t2, d)


def test_shorter_blocks_read_loss_clusters_as_less_risky() -> None:
    """Planted runs of losing days: the drawdown read grows with the block length."""
    rng = np.random.default_rng(7)
    closed = rng.normal(0.4, 1.0, 1500)
    for at in range(100, 1500, 150):
        closed[at:at + 12] = -2.0
    read = [_max_drawdown(paths.daily_blocks(_days(closed), 120, 4000, m, rng)).mean() for m in (1, 5, 40)]
    assert read[0] < read[1] < read[2], read
    short, long = (_max_drawdown(paths.trade_blocks([_member(closed)], 120, 4000, mean, rng)).mean()
                   for mean in (1, 40))
    assert short < long, (short, long)


def test_reproducible_under_a_seed() -> None:
    """The same generator state gives the same paths, threads or not."""
    pnl = np.random.default_rng(8).normal(0, 1, 300)
    members = [_member(pnl), _member(pnl[::-1].copy())]
    for draw in (lambda r: paths.daily_blocks(_days(pnl), 40, 300, 7, r),
                 lambda r: paths.trade_bootstrap(members, 40, 300, r),
                 lambda r: paths.trade_blocks(members, 40, 300, 7, r)):
        a, b, other = (draw(np.random.default_rng(seed)) for seed in (11, 11, 12))
        assert all((a[k] == b[k]).all() for k in FIGURES) and not (a["closed"] == other["closed"]).all()


def test_units_replayed_are_the_day_table() -> None:
    """Whole trades laid where they really were rebuild the member's server days (contract D)."""
    world = bar_world(21, 2, "2021-01-04", "2021-07-01")
    table = world["universe"]["days"]["test"]
    index = np.sort(table["day"].unique()).astype("datetime64[ns]").astype("int64")
    for name, s in world["sources"].items():
        bars = world["bars"][s["feed"]]
        where = units.slots(bars.index.to_numpy(), "UTC", "UTC", index, 5)
        unit = units.units(s["trades"], bars, where, 100.0, 1.0)
        assert len(unit["pnl"]) == len(s["trades"]) and unit["n_overlap"] == 0
        got = paths.history([unit])
        rows = table[table["identity"] == name].set_index("day").reindex(pd.DatetimeIndex(index))
        floating = rows["float_end"].ffill().fillna(0.0).to_numpy()
        assert np.abs(got["closed"] - rows["closed"].fillna(0).to_numpy()).max() < 1e-9
        assert (got["opened"] == rows["opened"].fillna(0).to_numpy()).all()
        assert np.abs(got["float_end"] - floating).max() < 1e-3
        assert max(np.abs(got[k] - rows[k].fillna(0).to_numpy()).max() for k in ("low", "high")) < 1e-3
        assert abs(unit["pnl"].sum() - s["trades"]["Profit/Loss"].sum()) < 1e-9
        assert (unit["gaps"] >= 0).all() and len(unit["gaps"]) == len(unit["pnl"]) - 1
        half = bars.loc[:"2021-04-02"]              # bars that end on a day of the calendar
        where = units.slots(half.index.to_numpy(), "UTC", "UTC", index[index <= half.index[-1].value], 5)
        whole = (s["trades"]["Close time"] <= half.index[-1]).sum()
        assert len(units.units(s["trades"], half, where, 100.0, 1.0)["pnl"]) == whole   # later trades: out


def test_t2_windows_are_slices_of_history() -> None:
    """With one window as long as the path, each path's trades opened are a run of real days."""
    rng = np.random.default_rng(9)
    member = _member(rng.normal(0, 1, 200))
    member["open_day"] = np.sort(rng.integers(0, 200, 200)).astype(np.int32)
    real = np.bincount(member["open_day"], minlength=200)
    got = paths.trade_blocks([member], 30, 200, 10**9, rng)["opened"]
    ring = np.concatenate([real, real[:30]])
    assert all(row.astype(np.int64).tobytes() in {ring[o:o + 30].tobytes() for o in range(200)} for row in got)


def main() -> None:
    """Run every case; an assertion stops it."""
    for name, case in [(n, c) for n, c in globals().items() if n.startswith("test_")]:
        case()
        print(f"OK   {name}")
    print("test_portfolio_mc_paths: ok")


if __name__ == "__main__":
    main()
