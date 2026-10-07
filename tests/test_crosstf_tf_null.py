#!/usr/bin/env python3
"""Known-answer battery of crossTF/tf (encargo 47, part K): one synthetic price path with no edge
read on M15, M30, H1 and H4; 300 mothers entering blind with siblings that share their stamps —
z_delta and z_build centred, nominal rejection; a sibling identical to her mother; an edge planted
in the mother alone (fail) and in every timeframe (pass); the same seed, the same numbers."""

import functools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.barstore import AGG, RULE
from studies.transfer.crossTF import inputs as study_inputs
from studies.transfer.crossTF.tf import null, run, table

GRID = pd.date_range("2012-01-02", "2017-12-29 23:45", freq="15min")
GRID = GRID[GRID.dayofweek < 5]                                  # M15 bars, Monday to Friday
CUTS = {"build": pd.Timestamp("2012-03-15"), "oos1": pd.Timestamp("2016-01-01"),
        "end": pd.Timestamp("2018-01-01")}                       # build opens mid-year: 2012 is split
PARAMS = {"Amount": 1000, "ATRPeriod": 20, "ATRMult": 4}
COSTS = {"point_value": 1.0, "tick_size": 0.01, "spread": 0.02, "slippage": 0.004,
         "commission_method": "PercentageBased", "commission": 0.0, "swap_long": -3.0,
         "swap_short": -1.0, "triple": 2, "rollover": 23, "tick_step": None}
BOTH = {"build": COSTS, "oos1": COSTS}
TFS = ("M15", "M30", "H1", "H4")
MOTHERS, RUNS = 300, 300
CFG = study_inputs.config([])["tf"]
TF = CFG | {"runs": CFG["runs"] | {"draws": RUNS}}


def bars(bump: np.ndarray | None = None) -> dict[str, pd.DataFrame]:
    """One path with a drift and no edge, on every timeframe; `bump` adds a log return per M15 bar."""
    rng = np.random.default_rng(1)
    step = 0.000004 + rng.normal(0, 0.0007, len(GRID)) + (0 if bump is None else bump)
    close = 100.0 * np.exp(np.cumsum(step))
    open_ = np.append(100.0, close[:-1])
    wick = np.abs(rng.normal(0, 0.0003, len(GRID))) * open_
    m15 = pd.DataFrame({"Open": open_, "High": np.maximum(open_, close) + wick,
                        "Low": np.minimum(open_, close) - wick, "Close": close, "Volume": 1.0},
                       index=GRID)
    return {"M15": m15} | {tf: m15.resample(RULE[tf]).agg(AGG).dropna() for tf in TFS[1:]}


@functools.cache
def noise() -> dict[str, pd.DataFrame]:
    """The edgeless path."""
    return bars()


def trades(name: str, opens: pd.DatetimeIndex, hours: np.ndarray, kind: str) -> pd.DataFrame:
    """Trades as SQX exports them, as far as tf reads them."""
    return pd.DataFrame({"strategy": name, "Open time": opens,
                         "Close time": opens + pd.to_timedelta(hours, unit="h"), "Type": kind})


def family(number: int, per_year: int = 45) -> pd.DataFrame:
    """A mother on M30 entering blind to the prices, and a sibling on M15 and on H1 that enter
    on her stamps four times in five (on their own the fifth), one side per family."""
    rng = np.random.default_rng([47, number])
    hourly = GRID[(GRID.minute == 0) & (GRID >= CUTS["build"]) & (GRID < CUTS["end"] - pd.Timedelta(days=3))]
    count = per_year * 6
    hers = np.sort(rng.choice(len(hourly), count, replace=False))
    hold = rng.integers(1, 13, count).astype(float)
    kind = "Buy" if number % 2 else "Sell"
    out = [trades(f"S{number}", hourly[hers], hold, kind)]
    for tf in ("M15", "H1"):
        own = np.where(rng.random(count) < 0.8, hers, rng.choice(len(hourly), count))
        out.append(trades(f"S{number}_{tf}", hourly[np.sort(own)], hold, kind))
    return pd.concat(out, ignore_index=True)


def made(mothers: list[str], tfs: tuple[str, ...] = ("M15", "H1")) -> pd.DataFrame:
    """The fabrication's manifest of comparable siblings."""
    return pd.DataFrame([{"mother": m, "sibling": f"{m}_{tf}", "timeframe": tf, "ratio": 1.0,
                          "rounding_shift": 0.0, "clamped": 0.0, "unverified": 0.0}
                         for m in mothers for tf in tfs])


def read(got: pd.DataFrame, frames: dict, tfs: tuple[str, ...] = ("M15", "H1"), tf: dict = TF,
         build: bool = True) -> dict:
    """Both tables of a synthetic batch of M30 mothers."""
    mothers = sorted(n for n in got["strategy"].unique() if "_" not in n)
    return run.read(made(mothers, tfs), {"oos1": got, "build": got if build else None},
                    {k: frames[k] for k in ("M30", *tfs)}, BOTH, CUTS, PARAMS, tf, "M30", {})


@functools.cache
def battery(judge: str = "gross") -> pd.DataFrame:
    """The siblings table of the edgeless population."""
    got = pd.concat([family(i) for i in range(MOTHERS)], ignore_index=True)
    return read(got, noise(), tf=TF | {"runs": TF["runs"] | {"judge_on": judge}})["siblings"]


def test_null_is_centred_and_rejects_at_the_nominal_rate() -> None:
    """No edge: per sibling timeframe, z_delta and z_build have a mean within 2 standard errors
    of 0, and z >= 1.65 rejects 5 % within 3 binomial sd. If not, the null is wrong: stop."""
    for judge in ("gross", "net"):
        for tf, rows in battery(judge).groupby("timeframe"):
            for name in ("z_delta", "z_build"):
                z = rows[name].to_numpy()
                assert np.isfinite(z).all(), (judge, tf, name)
                assert abs(z.mean()) < 2 * z.std(ddof=1) / np.sqrt(len(z)), (judge, tf, name, z.mean())
                assert abs(np.mean(z >= 1.65) - .05) < 3 * np.sqrt(.05 * .95 / len(z)), (judge, tf, name)
                assert abs(z.std(ddof=1) - 1) < 0.15, (judge, tf, name, z.std(ddof=1))


def test_identical_sibling() -> None:
    """A sibling that IS her mother (same trades, same bars): z_delta 0, ret 1, overlap 1."""
    mine = family(1)
    twin = mine[mine["strategy"] == "S1"]
    got = pd.concat([twin, twin.assign(strategy="S1_H1")], ignore_index=True)
    frames = noise() | {"H1": noise()["M30"]}
    row = read(got, frames, ("H1",))["siblings"].iloc[0]
    assert row["z_delta"] == 0 and row["overlap_oos1"] == 1 and row["overlap_build"] == 1
    assert row["e_oos1"] == row["e_mother_oos1"] and row["n_oos1"] == row["n_mother_oos1"] > 30
    assert row["ret"] == 1 or row["t2a_why"] == "mother_e_not_positive"


@functools.cache
def planted() -> tuple[dict, pd.DataFrame]:
    """A path that rises for 2 hours after each signal and gives half back in the next 2; six
    mothers buy the rise on M30. `A*`: their siblings buy it too, on every timeframe. `P*`: their
    siblings buy the 2 hours after it, when it falls — the edge is the mother's alone."""
    rng = np.random.default_rng(5)
    slots = np.flatnonzero((GRID.hour % 4 == 0) & (GRID.minute == 0) & (GRID >= CUTS["build"])
                           & (GRID < CUTS["end"] - pd.Timedelta(days=3)))
    signal = np.sort(rng.choice(slots[::3], 12 * 35 * 6, replace=False)).reshape(-1, 12)
    bump = np.zeros(len(GRID))
    for k in range(8):
        bump[signal.ravel() + k] += 0.003
        bump[signal.ravel() + 8 + k] -= 0.0015
    got = []
    for j in range(12):
        name, at = ("A" if j < 6 else "P") + str(j), GRID[signal[:, j]]
        got.append(trades(name, at, 2.0, "Buy"))
        for tf in ("M15", "H1", "H4"):
            late = pd.Timedelta(hours=0 if j < 6 else 2)
            got.append(trades(f"{name}_{tf}", at + late, 4.0 if tf == "H4" else 2.0, "Buy"))
    return bars(bump), pd.concat(got, ignore_index=True)


def test_planted_edge() -> None:
    """Planted in every timeframe: pass. In the mother alone: an isolated peak in oos1 and in the
    build, fail, already at phase 1. The trade counts match, so T1 passes everywhere."""
    frames, got = planted()
    both = read(got, frames, ("M15", "H1", "H4"))
    state = both["mothers"].set_index("strategy")
    assert (state.loc[state.index.str.startswith("A"), ["t1", "t2a", "t2b", "t3", "phase1", "state"]]
            == "pass").all(axis=None), state
    alone = state[state.index.str.startswith("P")]
    assert (alone[["t2a", "t2b", "phase1", "state"]] == "fail").all(axis=None), alone
    assert (alone["t1"] == "pass").all()
    assert (alone["why"] == "isolated_peak_oos1;isolated_peak_build").all(), alone["why"]
    rows = both["siblings"]
    near = rows[rows["mother"].str.startswith("A") & (rows["role"] == "neighbour")]
    assert (near["ret"] >= 0.5).all() and (near["z_build"] >= 1.65).all() and (near["z_frec"] == 0).all()
    assert rows["ret_build_pct"].between(0, 1).all()


def test_phase_one_alone() -> None:
    """Without the build: T1 and T2b have no data, the state is phase 1's, never a pass."""
    frames, got = planted()
    both = read(got, frames, ("M15", "H1", "H4"), build=False)
    state = both["mothers"].set_index("strategy")
    assert (state.loc[state.index.str.startswith("A"), "phase1"] == "pass").all()
    assert (state.loc[state.index.str.startswith("A"), "state"] == "limbo").all()
    assert (state.loc[state.index.str.startswith("P"), "state"] == "fail").all()
    assert (both["siblings"][["t1_why", "t2b_why"]] == "no_build_data").all(axis=None)
    assert both["siblings"][["z_build", "z_frec", "n_build"]].isna().all(axis=None)


def test_same_seed_same_numbers() -> None:
    """The draw is the seed's: twice the same table; another seed, another z."""
    got = pd.concat([family(i) for i in range(3)], ignore_index=True)
    one, two = (read(got, noise())["siblings"] for _ in range(2))
    pd.testing.assert_frame_equal(one, two)
    other = read(got, noise(), tf=TF | {"runs": TF["runs"] | {"seed": 1}})["siblings"]
    assert not np.allclose(one["z_delta"], other["z_delta"])
    assert (read(got, noise())["mothers"][["seed", "draws"]] == [TF["runs"]["seed"], RUNS]).all(axis=None)


def test_calendar_never_crosses_a_window() -> None:
    """Every cell lies inside one window, and the build's first cell opens at its cut."""
    cal, shifts = null.calendar(GRID[0], GRID[-1], CUTS, TF["runs"])
    for start, end in table.windows(CUTS).values():
        inside = (cal["start"] >= start) & (cal["start"] < end)
        assert (cal.loc[inside, "end"] <= end).all()
    assert (cal["start"] == CUTS["build"]).any() and shifts.shape == (RUNS, len(cal))


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    for judge in ("gross", "net"):
        for tf, rows in battery(judge).groupby("timeframe"):
            for name in ("z_delta", "z_build"):
                z = rows[name].to_numpy()
                print(f"{judge} {tf} {name}: mean {z.mean():+.3f}  sd {z.std(ddof=1):.3f}  "
                      f"rejection at 5 % {np.mean(z >= 1.65):.3f}  (n {len(z)})")
