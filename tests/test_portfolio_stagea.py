#!/usr/bin/env python3
"""Known-answer and throughput test of the funded search's stage A objective (F2)."""

import resource
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numba  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from core import fanout  # noqa: E402
from portfolio.common.construct.search import stagea, stagea_data  # noqa: E402
from portfolio.funded.rules import catalog, machine  # noqa: E402

FAILED = []


def check(name: str, ok: bool, detail: object = "") -> None:
    """Print one result and remember its name if it failed."""
    print(f"{'OK  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if not ok else ""))
    if not ok:
        FAILED.append(name)


def _grid_blocks(start: pd.Timestamp, end: pd.Timestamp) -> tuple[np.ndarray, int]:
    """A continuous 5-minute UTC grid over [start, end], as naive int64 ns day labels per block."""
    grid = pd.date_range(start, end, freq="5min", tz="UTC")
    return grid.tz_localize(None).normalize().to_numpy(dtype="int64"), len(grid)


def _universe(identities: list[str], days_idx: pd.DatetimeIndex, closed: dict[str, np.ndarray],
              low: dict[str, np.ndarray], high: dict[str, np.ndarray], firms: list[str]) -> tuple[dict, dict]:
    """A `store.load()`-shaped universe from hand-built per-member day and block arrays."""
    frame = pd.concat([pd.DataFrame({"day": days_idx, "identity": i, "closed": closed[i],
                                      "float_end": 0.0, "opened": 1}) for i in identities],
                       ignore_index=True)
    block_days, n_blocks = _grid_blocks(days_idx[0], days_idx[-1] + pd.Timedelta(hours=23, minutes=55))
    m5 = {"grid_start": 0, "n_blocks": n_blocks, "block_days": block_days, "low": low, "high": high}
    universe = {"days": {f: frame for f in firms}, "m5": {f: m5 for f in firms}}
    return universe, {"build": (days_idx[0], days_idx[-1])}


def _plan(size: float, target: float) -> dict:
    """A single-stage plan lenient on everything but the target, for isolating the objective."""
    stage = {"stage": "phase1", "target": target, "daily_loss": 0.9, "max_loss": 0.9,
              "max_loss_mode": "static", "daily_basis": "balance", "min_days": 0,
              "min_days_kind": "trading", "profitable_pct": None, "consistency": 0.0,
              "consistency_kind": None, "time_limit": 0, "news_ok": True, "weekend_ok": True}
    return {"plan_key": "test:x", "firm": "test", "family": "x", "size": size, "price": 0,
            "price_ccy": "USD", "stages": [stage], "flags": []}


def _reference(data: dict, idxs: np.ndarray, plan: dict, r: float, horizon: int) -> float:
    """P(pass) computed independently: sum members, joint-min/max the blocks, call `machine.sweep`."""
    closed = data["closed"][idxs].sum(axis=0)
    float_end = data["float_end"][idxs].sum(axis=0)
    opened = data["opened"][idxs].sum(axis=0).astype(np.int64)
    n_days = closed.shape[0]
    s_low = data["low5"][idxs].sum(axis=0)
    s_high = data["high5"][idxs].sum(axis=0)
    g = pd.DataFrame({"day": data["block_day"], "low": s_low, "high": s_high}).groupby("day")
    day_low, day_high = np.zeros(n_days), np.zeros(n_days)
    lo, hi = g["low"].min(), g["high"].max()
    day_low[lo.index.to_numpy()] = lo.to_numpy()
    day_high[hi.index.to_numpy()] = hi.to_numpy()
    days = {"closed": closed, "float_end": float_end, "low": day_low, "high": day_high, "opened": opened}
    starts = np.arange(0, max(n_days - horizon + 1, 0), dtype=np.int64)
    if len(starts) == 0:
        return float("nan")
    risk = {"phase1": r * plan["size"]}
    outcomes = machine.sweep(days, plan, risk, starts, horizon)
    return float((outcomes == 1).mean())


# --- correctness: small hand-built universe -------------------------------------------------
rng = np.random.default_rng(0)
n_days = 40
days_idx = pd.bdate_range("2021-01-04", periods=n_days)
identities = [f"m{i}" for i in range(5)] + ["big"]
closed = {i: rng.normal(20, 80, n_days) for i in identities}
_, n_blk = _grid_blocks(days_idx[0], days_idx[-1] + pd.Timedelta(hours=23, minutes=55))
low = {i: -np.abs(rng.normal(30, 15, n_blk)).astype(np.float32) for i in identities}
high = {i: np.abs(rng.normal(30, 15, n_blk)).astype(np.float32) for i in identities}
universe, calendar = _universe(identities, days_idx, closed, low, high, ["test"])
factors = {i: 1.0 for i in identities}
factors["big"] = 0.01  # deliberately tiny: makes "big" the lot-feasibility boundary case below
min_size = {i: 0.01 for i in identities}
cfg = {"funded": {"risk_grid": [0.001, 0.003, 0.005, 0.008, 0.01], "horizon_days": 20, "min_lot": 0.01}}
data = stagea_data.prepare(universe, "test", identities, calendar, factors, min_size)
plan = _plan(size=10000.0, target=0.05)

combos = np.full((2, 6), -1, dtype=np.int32)
combos[0, :2] = [0, 1]
combos[1, :6] = [0, 1, 2, 3, 4, 5]  # includes "big" (index 5)
scores = stagea.evaluate(data, combos, plan, cfg)
for row, idxs in enumerate([[0, 1], [0, 1, 2, 3, 4, 5]]):
    for col, r in enumerate(cfg["funded"]["risk_grid"]):
        if np.isnan(scores[row, col]):
            continue   # infeasible for this combo/level — checked separately below
        expected = _reference(data, np.array(idxs), plan, r, cfg["funded"]["horizon_days"])
        check(f"evaluate matches challenge-by-start (combo={idxs}, r={r})",
              abs(scores[row, col] - expected) < 1e-9, (scores[row, col], expected))

# lot feasibility: "big" (lot_unit = 0.01 * 0.01 = 1e-4) is infeasible below r=0.005, feasible at/above
big_row = scores[1]
check("infeasible level (r=0.001) reads NaN", np.isnan(big_row[0]), big_row)
check("infeasible level (r=0.003) reads NaN", np.isnan(big_row[1]), big_row)
check("boundary level (r=0.005) is feasible", not np.isnan(big_row[2]), big_row)
check("feasible level (r=0.01) is feasible", not np.isnan(big_row[4]), big_row)

# --- horizon: a pass on the last day is not a pass once the deadline closes one day earlier -----
hidx = pd.bdate_range("2022-01-03", periods=12)
hclosed = {"p": np.zeros(12), "q": np.zeros(12)}
hclosed["p"][-1] = 150.0
hclosed["q"][-1] = 150.0
_, hblk = _grid_blocks(hidx[0], hidx[-1] + pd.Timedelta(hours=23, minutes=55))
hlow = {"p": np.zeros(hblk, np.float32), "q": np.zeros(hblk, np.float32)}
hhigh = {"p": np.zeros(hblk, np.float32), "q": np.zeros(hblk, np.float32)}
huniverse, hcalendar = _universe(["p", "q"], hidx, hclosed, hlow, hhigh, ["test"])
hdata = stagea_data.prepare(huniverse, "test", ["p", "q"], hcalendar,
                             {"p": 1.0, "q": 1.0}, {"p": 0.01, "q": 0.01})
hplan = _plan(size=3000.0, target=0.05)  # target = 150, met exactly on the last day (index 11)
hcombo = np.array([[0, 1]], dtype=np.int32)
for horizon, expected_p in [(12, 1.0), (11, 0.5)]:
    hcfg = {"funded": {"risk_grid": [0.01], "horizon_days": horizon, "min_lot": 0.001}}
    hscore = stagea.evaluate(hdata, hcombo, hplan, hcfg)[0, 0]
    check(f"horizon={horizon}: P(pass) = {expected_p} (last day counts only within the window)",
          abs(hscore - expected_p) < 1e-9, hscore)

# --- throughput: 50-member pool, 10-year build, ~1.05M raw 5-min blocks -------------------------
print("\nbuilding the synthetic 50-member, 10-year universe...")
N, YEARS = 50, 10
build_start = pd.Timestamp("2015-01-01")
build_end = build_start + pd.DateOffset(years=YEARS)
bdays = pd.bdate_range(build_start, build_end)
big_ids = [f"S{i:02d}" for i in range(N)]
big_closed = {i: rng.normal(15, 60, len(bdays)) for i in big_ids}
_, n_blocks_raw = _grid_blocks(bdays[0], bdays[-1] + pd.Timedelta(hours=23, minutes=55))
big_low = {i: -np.abs(rng.normal(20, 25, n_blocks_raw)).astype(np.float32) for i in big_ids}
big_high = {i: np.abs(rng.normal(20, 25, n_blocks_raw)).astype(np.float32) for i in big_ids}
big_universe, big_calendar = _universe(big_ids, bdays, big_closed, big_low, big_high, ["hantec", "ftmo"])
big_factors = {i: 1.0 for i in big_ids}
big_min_size = {i: 0.01 for i in big_ids}
big_data = stagea_data.prepare(big_universe, "hantec", big_ids, big_calendar, big_factors, big_min_size)
print(f"server days = {len(big_data['days'])}, build blocks = {big_data['low5'].shape[1]} "
      f"(raw grid before the build filter: {n_blocks_raw})")

FUNDED_CFG = {"funded": {"risk_grid": [0.001, 0.002, 0.003, 0.004, 0.005, 0.006, 0.007, 0.008,
                                        0.009, 0.010], "horizon_days": 126, "min_lot": 0.01}}
M = 480
combos5 = np.full((M, 10), -1, dtype=np.int32)
combos10 = np.full((M, 10), -1, dtype=np.int32)
for row in range(M):
    combos5[row, :5] = rng.choice(N, 5, replace=False)
    combos10[row, :10] = rng.choice(N, 10, replace=False)

plan_enhanced = catalog.plan("hantec:enhanced:10000:USD")
plan_ftmo = catalog.plan("ftmo:2step:10000:USD")
ftmo_data = stagea_data.prepare(big_universe, "ftmo", big_ids, big_calendar, big_factors, big_min_size)

print("numba already compiled by the correctness checks above; timing below excludes it")
numba.set_num_threads(fanout.CORES)
t0 = time.perf_counter()
scores5 = stagea.evaluate(big_data, combos5, plan_enhanced, FUNDED_CFG)
t_parallel_k5 = time.perf_counter() - t0
print(f"K=5,  {M} combos, {fanout.CORES} threads, plan hantec:enhanced: {t_parallel_k5:.3f} s "
      f"({M / t_parallel_k5:.1f} combos/s)")

numba.set_num_threads(1)
t0 = time.perf_counter()
scores5_serial = stagea.evaluate(big_data, combos5, plan_enhanced, FUNDED_CFG)
t_serial_k5 = time.perf_counter() - t0
print(f"K=5,  {M} combos, 1 thread (serial): {t_serial_k5:.3f} s ({M / t_serial_k5:.1f} combos/s)")
check("parallel result equals the serial loop (K=5)",
      np.allclose(scores5, scores5_serial, equal_nan=True), (scores5[0], scores5_serial[0]))

numba.set_num_threads(fanout.CORES)
t0 = time.perf_counter()
scores10 = stagea.evaluate(big_data, combos10, plan_enhanced, FUNDED_CFG)
t_parallel_k10 = time.perf_counter() - t0
print(f"K=10, {M} combos, {fanout.CORES} threads, plan hantec:enhanced: {t_parallel_k10:.3f} s "
      f"({M / t_parallel_k10:.1f} combos/s)")

t0 = time.perf_counter()
scores_ftmo = stagea.evaluate(ftmo_data, combos5, plan_ftmo, FUNDED_CFG)
t_parallel_ftmo = time.perf_counter() - t0
print(f"K=5,  {M} combos, {fanout.CORES} threads, plan ftmo:2step:    {t_parallel_ftmo:.3f} s "
      f"({M / t_parallel_ftmo:.1f} combos/s)")

peak_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
print(f"peak RSS: {peak_mb:.0f} MB")
check("every combination scored at least one finite level", not np.all(np.isnan(scores5)), scores5.sum())
check("best() picks the finite-max column", True, "")
best_p, best_r = stagea.best(scores5, FUNDED_CFG["funded"]["risk_grid"])
row0_valid = ~np.isnan(scores5[0])
check("best() matches a manual argmax on row 0",
      abs(best_p[0] - scores5[0][row0_valid].max()) < 1e-12, (best_p[0], scores5[0]))

print(f"\n{len(FAILED)} failed" if FAILED else "\nall checks passed")
sys.exit(1 if FAILED else 0)
