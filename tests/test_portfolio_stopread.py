#!/usr/bin/env python3
"""«Reloj parado»: the funded search's stage A moves when the step-24 stop in the .sqx moves."""

import itertools
import os
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

import portfolio.common.construct.funded as funded
import portfolio.common.construct.inputs.risk as risk
from portfolio.common.construct.equity import universe
from portfolio.common.construct.inputs import config, pool
from portfolio.common.construct.search import stagea, stagea_data
from portfolio.funded.rules import catalog
from sqx.variants.build import rewrite, stoploss
from test_portfolio_search import _grafted_sqx

FAILURES = []
POOL, PLAN = "Test_nikkei_ref", "hantec:express:10000:USD"
PAIRS = [f"pairs.{k}=0.90" for k in config.PAIR_THRESHOLDS]     # the test pool's relaxation


def check(name: str, ok: bool) -> None:
    """Print one line per case; remember the failures."""
    print(f"{'OK   ' if ok else 'FALLO'}  {name}")
    if not ok:
        FAILURES.append(name)


def _cfg(grid: list[float]) -> dict:
    """Stage A's knobs on one risk grid; the cap is a test value set where it never binds."""
    return {"funded": {"risk_grid": grid, "horizon_days": 20, "min_lot": 0.01, "open_risk_cap": 100.0}}


def test_synthetic() -> None:
    """One member, the same trades, its stop X read as 2.5 and as 5.0 off two .sqx files."""
    real_dir = risk.archive_read.archive_dir
    with tempfile.TemporaryDirectory() as tmp:
        _grafted_sqx(Path(tmp), 2.5, "STOP")
        _grafted_sqx(Path(tmp), 5.0, "STOP_X2")
        risk.archive_read.archive_dir = lambda: Path(tmp)
        try:
            factors, excluded = funded.size_members(["STOP", "STOP_X2"])
        finally:
            risk.archive_read.archive_dir = real_dir
    check("the X of each file is the one read (2.5 and 5.0), nobody excluded",
          not excluded and factors["STOP"]["x"] == 2.5 and factors["STOP_X2"]["x"] == 5.0)
    check("twice the stop distance = half the P&L per unit of risk",
          np.isclose(factors["STOP_X2"]["factor"], factors["STOP"]["factor"] / 2))

    days = pd.bdate_range("2021-01-04", periods=120)
    blocks = pd.date_range(days[0], days[-1] + pd.Timedelta(hours=23, minutes=55), freq="5min")
    flat = np.zeros(len(blocks), np.float32)
    frame = pd.DataFrame({"day": days, "identity": "m", "float_end": 0.0, "opened": 1,
                          "closed": np.random.default_rng(3).normal(400, 1500, len(days))})
    world = {"days": {"test": frame}, "m5": {"test": {
        "block_days": blocks.normalize().to_numpy(dtype="int64"), "low": {"m": flat}, "high": {"m": flat}}}}
    stage = {"stage": "phase1", "target": 0.05, "daily_loss": 0.9, "max_loss": 0.9,
             "max_loss_mode": "static", "daily_basis": "balance", "min_days": 0,
             "min_days_kind": "trading", "profitable_pct": None, "consistency": 0.0,
             "consistency_kind": None, "time_limit": 0}
    plan = {"size": 10000.0, "stages": [stage], "flags": []}
    combo = np.array([[0]], dtype=np.int32)

    def scored(member: str, grid: list[float]) -> np.ndarray:
        """Stage A of the one member sized with `member`'s stop, per level of `grid`."""
        data = stagea_data.prepare(world, "test", ["m"], {"build": (days[0], days[-1])},
                                   {"m": factors[member]["factor"]}, {"m": factors[member]["min_size"]})
        return stagea.evaluate(data, combo, plan, _cfg(grid))[0]

    grid = [0.002, 0.004, 0.008]
    near, far = scored("STOP", grid), scored("STOP_X2", grid)
    check("at the same risk per trade P(pass) changes with the stop", not np.allclose(near, far)
          and 0 < near.min() and near.max() < 1)
    check("the stop twice as far at twice the risk is the same account: identical P(pass)",
          np.array_equal(near, scored("STOP_X2", [2 * r for r in grid])))
    print(f"       X=2.5 {near.round(3).tolist()} · X=5.0 {far.round(3).tolist()} (riesgos {grid})")


def _displaced(load: object, tmp: Path, times: float) -> object:
    """`archive_read.load` whose frozen .sqx carries `StopLossCoef1` multiplied by `times`."""
    def loaded(identity: str, version: str | None = None) -> dict:
        """The archived strategy, its .sqx swapped for the displaced copy."""
        got = load(identity, version)
        out = tmp / f"{identity}.sqx"
        with zipfile.ZipFile(got["sqx"]) as src, zipfile.ZipFile(out, "w") as dst:
            for name in src.namelist():
                blob = src.read(name)
                if name == rewrite.PORTFOLIO:
                    text = blob.decode("utf-8")
                    x = float(rewrite.values(text)[stoploss.VARIABLE])
                    blob = rewrite.set_values(text, {stoploss.VARIABLE: x * times}).encode("utf-8")
                dst.writestr(name, blob)
        return {**got, "sqx": out}
    return loaded


def test_real_pool() -> None:
    """The archived Nikkei pool, sized off its own .sqx and off copies with the stop twice as far."""
    cfg = config.load(PAIRS + ["funded.open_risk_cap=1.0"])
    data = universe.load(universe.build(POOL, cfg))
    kept = data["manifest"]["members"]["kept"]
    plan = catalog.plan(PLAN)
    real_load = risk.archive_read.load
    near, _ = funded.size_members(kept)
    with tempfile.TemporaryDirectory() as tmp:
        risk.archive_read.load = _displaced(real_load, Path(tmp), 2.0)
        try:
            far, _ = funded.size_members(kept)
        finally:
            risk.archive_read.load = real_load
    check("every member's X doubles with the file's", all(np.isclose(far[i]["x"], 2 * near[i]["x"]) for i in kept))

    sets = [c for k in (1, 2, 3) for c in itertools.combinations(range(len(kept)), k)]
    combos = np.array([list(c) + [-1] * (3 - len(c)) for c in sets], dtype=np.int32)
    grid = cfg["funded"]["risk_grid"]

    def scored(sized: dict, levels: list[float]) -> np.ndarray:
        """Stage A of every single, pair and trio, the members sized as `sized` says."""
        prepared = stagea_data.prepare(data, plan["firm"], kept, data["manifest"]["calendar"],
                                       {i: sized[i]["factor"] for i in kept},
                                       {i: sized[i]["min_size"] for i in kept})
        return stagea.evaluate(prepared, combos, plan, {**cfg, "funded": {**cfg["funded"], "risk_grid": levels}})

    a, b = scored(near, grid), scored(far, grid)
    (pa, ra), (pb, rb) = stagea.best(a, grid), stagea.best(b, grid)
    alive = pa > 0                          # a combination that never passes inside the grid cannot move
    check("same risk grid, stop twice as far: P(pass) moves in every combination that can pass",
          (np.abs(a - b) > 1e-3).any(axis=1)[alive].all() and alive.sum() > 100)
    check("its best P(pass) inside the grid falls (the grid tops out at 1 %) and its best level never falls",
          (pb < pa)[alive].all() and (rb >= ra)[pb > 0].all())
    half = scored(near, [r / 2 for r in grid])
    # the M5 floating is float32: halving the factor moves a path's last bits, a few start days flip
    check("stop twice as far at risk r = the real stop at r/2 (to 1 point of P)", np.nanmax(np.abs(b - half)) < 0.01)
    top = int(np.nanargmax(pa))
    print(f"       {len(sets)} carteras · la mejor con el stop real: P {pa[top]:.3f} a r {ra[top]:.1%}; "
          f"la misma con el stop ×2: P {pb[top]:.3f} a r {rb[top]:.1%}; mediana de |ΔP| al mismo riesgo "
          f"{np.nanmedian(np.abs(a - b)):.3f}")


def main() -> None:
    """The synthetic case always; the archived pool only under the portfolio test root."""
    test_synthetic()
    if os.environ.get("ALGO_DATA_ROOT"):
        test_real_pool()
    else:
        print("OMITIDA la parte real: sólo corre con ALGO_DATA_ROOT en la raíz de prueba "
              "(portfolio/testroot), donde está el pool Test_nikkei_ref")
    print(f"\n{'TODO OK' if not FAILURES else 'FALLOS: ' + ', '.join(FAILURES)}")
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
