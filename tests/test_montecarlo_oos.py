#!/usr/bin/env python3
"""Family E reads the out-of-sample trades alone (owner, 2026-09-29): a strategy whose IS is
great and whose OOS is flat must get the flat OOS reading, never the IS-inflated one that
mixing both sides in `core.significance.footprint()`/`psr()` used to produce."""

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from portfolio.common.monteCarlo import run as mc_run
from portfolio.common.monteCarlo.inputs import config as mc_config
from portfolio.common.monteCarlo.verdict import significance
from studies.breakage.mcRetest.measure import originals

SEED = 20260929


def stream(is_pnl: np.ndarray, oos_pnl: np.ndarray) -> dict:
    """A minimal stream contract (`inputs.stream.build()`'s shape) with a known IS/OOS split."""
    pnl = np.concatenate([is_pnl, oos_pnl])
    n = pnl.size
    open_ = pd.date_range("2020-01-01", periods=n, freq="12h").to_numpy()
    close = open_ + np.timedelta64(6, "h")
    sample = np.array(["IST"] * is_pnl.size + ["OOS1"] * oos_pnl.size)
    return {"name": "X", "frame": pd.DataFrame({"Profit/Loss": pnl}), "pnl": pnl,
            "r": pnl / 1000.0, "cost": np.zeros(n), "spread": np.full(n, 0.5),
            "mae": np.abs(pnl), "size": np.ones(n), "direction": np.ones(n),
            "open": open_, "close": close, "sample": sample}


def day() -> pd.DataFrame:
    """Flat-ish daily candles: near-zero drift and noise, spanning the whole stream."""
    rng = np.random.default_rng(SEED)
    n = 200
    close = 100.0 + np.cumsum(rng.normal(0, 0.3, n))
    return pd.DataFrame({"Close": close},
                        index=pd.date_range("2020-01-01", periods=n, freq="D"))


def test_family_e_reads_oos_not_is() -> None:
    """IS: 60 trades of +500 $ each (a huge, near-noiseless Sharpe). OOS: 40 trades of pure
    noise around zero (no edge at all). Family E must read the flat OOS side."""
    rng = np.random.default_rng(SEED)
    is_pnl = 500.0 + rng.normal(0, 5.0, 60)
    oos_pnl = rng.normal(0, 50.0, 40)
    source = stream(is_pnl, oos_pnl)
    cfg = mc_config.load(["global.n_sims=300", "global.chunk=300"])
    asset = {"point_value": 1.0}
    e = mc_run._family_e(source, day(), asset, cfg)
    assert e["n"] == oos_pnl.size, "Family E must count only the OOS trades"
    # What the pre-fix code computed: psr() on the whole IS+OOS stream.
    benchmark_all = significance.footprint(source, day(), asset)
    psr_all = significance.psr(source["pnl"], benchmark_all)
    assert psr_all["sharpe"] > 20 * e["sharpe"], (
        "the IS-inflated Sharpe should dwarf the honest OOS one")
    assert psr_all["psr"] > 0.999, (
        "the old, wrong computation over IS+OOS reads a near-certain edge from the IS alone")
    assert e["psr"] < 0.85, (
        "the honest OOS-only PSR must read far less confident than the IS-inflated one")


def test_family_e_warns_when_oos_too_thin() -> None:
    """Fewer OOS trades than `confidence.MEAN_PROVISIONAL`: NaN and a warning, never IS."""
    rng = np.random.default_rng(SEED)
    source = stream(500.0 + rng.normal(0, 5.0, 60), rng.normal(0, 50.0, 3))
    cfg = mc_config.load(["global.n_sims=300", "global.chunk=300"])
    e = mc_run._family_e(source, day(), {"point_value": 1.0}, cfg)
    assert e["psr"] != e["psr"], "too few OOS trades must read NaN, never a number from IS"
    assert e["warning"]


def test_mcretest_originals_keep_oos_only() -> None:
    """`measure.originals.read()` keeps only `sample == 'OOS'` rows of the harvest's own
    trade list -- a strategy whose harvest carries only an IS row comes back with none, and
    a strategy with both keeps only its OOS ones."""
    mixed = pd.DataFrame({
        "identity": ["h1", "h2", "h2"],
        "strategy": ["placeholder"] * 3,   # overwritten by read(), from `identities`
        "Type": ["Buy"] * 3, "Open price": [1.0, 1.0, 1.0], "Close price": [1.1, 1.2, 0.9],
        "Open time": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
        "Close time": pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-04"]),
        "Size": [1.0, 1.0, 1.0], "Profit/Loss": [10.0, 12.0, -9.0],
        "sample": ["IS", "IS", "OOS"]})
    real_newest = originals.newest_harvest
    with tempfile.TemporaryDirectory() as tmp:
        mixed.to_parquet(Path(tmp) / "trades.parquet")
        originals.newest_harvest = lambda project, databank: Path(tmp)
        try:
            got = originals.read("P", "Results", {"S1": "h1", "S2": "h2"}, 1.0)
        finally:
            originals.newest_harvest = real_newest
    assert set(got["strategy"]) == {"S2"}, "S1's only row is IS and must not come back"
    assert len(got) == 1, "S2's IS row must be dropped, its one OOS row kept"


if __name__ == "__main__":
    test_family_e_reads_oos_not_is()
    test_family_e_warns_when_oos_too_thin()
    test_mcretest_originals_keep_oos_only()
    print("ok")
