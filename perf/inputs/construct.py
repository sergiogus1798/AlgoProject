"""The portfolio engine's work the catalogue times: one universe member, a close-to-close panel, the pairs table, a rank search, stage B, the verdict's null, the bank table."""

import numpy as np
import pandas as pd

from core import assetdata, barstore
from core.archive.read import listing
from core.paths import bar_source, harvest_dir
from portfolio.common.construct import walkforward, weights
from portfolio.common.construct.equity import closecurve, universe
from portfolio.common.construct.inputs import config, source
from portfolio.common.construct.pairs import table
from portfolio.common.construct.search import objective, random_k, stageb
from portfolio.funded.rules import catalog
from portfolio.funded.sim import bank, monkey
from portfolio.funded.sim import inputs as bank_inputs
from portfolio.funded.sim import table as bank_table

SEED = 0   # the synthetic benchmark inputs are one fixed draw: timings compare run to run on the same data
PAIRS_POOL = 500   # strategies in the synthetic pool: 124,750 pairs, the plan's large case
RANK_BATCH = 30_000   # combinations a full GA scores: 300 x 100 generations
CLOSE_HARVEST = ("Test_Calib_USDJPY_H1_momentumL", "Results", "2026-10-02")
CLOSE_POOL = 64   # strategies of that harvest, 4 per worker: a whole population is ~3,700
STAGEB = {"members": 5, "days": 2610, "trades": 350, "blocks": 40, "plan": "ftmo:2step:10000:USD"}
BANK = {"n_paths": 10_000, "horizon": 504}   # the first real run's size (encargo 33, 2026-10-05)
# The owner's inputs are unset in the committed config: these only size the workload.
BANK_SETS = ["owner.eurusd=1.1", "owner.payout_cushion=0", "owner.tax_rate=0.2", "owner.payout_fee=0.02",
             "owner.p_payout_denied=0.05", "owner.p_firm_closes_year=0.1", "gaps.hantec_fee_refund=false",
             "gaps.hantec_endurance_payout_days=14", "gaps.hantec_express_floor_after_payout=stays",
             "gaps.ftmo_1step_floor_after_payout=stays"]


def universe_member(cfg: dict) -> dict:
    """One archived strategy through the universe (M1 path, days per clock, M5 blocks, reconciliation).

    Args:
        cfg: What perf's config.load() returned (unused: the engine reads its own).

    Returns:
        Trades processed, and the M1 file read.
    """
    first = listing()[0]
    s = source.load(first["identity"], first["version"])
    universe._processed({s["identity"]: s}, config.load())
    return {"scale": len(s["trades"]), "bytes_in": bar_source(s["feed"]).stat().st_size}


def close_curve(cfg: dict) -> dict:
    """The close-to-close daily panel of 64 strategies of one harvest over oos1, on 16 workers.

    Args:
        cfg: What perf's config.load() returned (unused).

    Returns:
        Strategies rebuilt, and the M1 file read. The harvest's `oos2_*` files are not opened.
    """
    trades = harvest_dir(*CLOSE_HARVEST) / "trades.parquet"
    ids = sorted(pd.read_parquet(trades, columns=["identity"])["identity"].unique())[:CLOSE_POOL]
    lo, hi = (pd.Timestamp(x, unit="ms") for x in assetdata.window(assetdata.load("USDJPY"), "oos1"))
    mine = pd.read_parquet(trades, filters=[("identity", "in", ids), ("sample", "==", "OOS")])
    bars = barstore.source("USDJPY_M1", ["High", "Low", "Close"])
    closecurve.panel(mine, bars[(bars.index >= lo) & (bars.index < hi)], *closecurve.measured(mine))
    return {"scale": len(ids), "bytes_in": bar_source("USDJPY_M1").stat().st_size}


def pairs_table(cfg: dict) -> dict:
    """Every pair measure over a 500-strategy synthetic pool on a 10-year build, on every core.

    Args:
        cfg: What perf's config.load() returned (unused).

    Returns:
        Pairs measured; nothing read from disk.
    """
    days = pd.bdate_range("2008-01-01", "2017-12-29")
    daily = pd.DataFrame(np.random.default_rng(SEED).normal(size=(len(days), PAIRS_POOL)), index=days,
                         columns=[f"S{k:03d}" for k in range(PAIRS_POOL)])
    got = table.table(daily, daily.groupby(daily.index.to_period("M")).sum(), config.load())
    return {"scale": int(len(got) // 11), "bytes_in": 0}


def rank_search(cfg: dict) -> dict:
    """A whole GA's worth of combinations of a 50-member pool scored by ranks on a 10-year build.

    Args:
        cfg: What perf's config.load() returned (unused).

    Returns:
        Combinations scored; nothing read from disk.
    """
    rng = np.random.default_rng(SEED)
    days = pd.bdate_range("2008-01-01", "2017-12-29")
    unit = 0.02 + rng.normal(size=(50, len(days)))
    members = rng.random((RANK_BATCH, 50)) < 0.15
    members[:, 0] = True
    engine = config.load()      # the committed knobs: equal weight, four shifted windows
    for start in range(0, RANK_BATCH, 300):
        measured = objective.measure(unit, days, members[start:start + 300], engine)
        objective.score(measured, measured)
    return {"scale": RANK_BATCH, "bytes_in": 0}


def verdict_null(cfg: dict) -> dict:
    """The real verdict's oos1 null: 10,000 random combinations of five of a 50-member pool on two years.

    Args:
        cfg: What perf's config.load() returned (unused).

    Returns:
        Draws measured and ranked; nothing read from disk.
    """
    rng = np.random.default_rng(SEED)
    days = pd.bdate_range("2020-01-01", "2021-12-31")
    unit = 0.02 + rng.normal(size=(50, len(days)))
    engine = config.load()      # the committed knobs: 10,000 draws, four shifted windows
    drawn = random_k.draw(~np.eye(50, dtype=bool), 5, engine["real"]["null_draws"],
                          engine["real"]["exhaustive_max"], rng)
    table = objective.worst(objective.measure(unit, days, drawn["members"], engine))
    every = {name: values[drawn["index"]] for name, values in table.items()}
    objective.rank_score(every, every)
    return {"scale": len(drawn["index"]), "bytes_in": 0}


def _trade_units(rng: np.random.Generator, per_day: int) -> dict:
    """One synthetic member as `mc.units.units()` returns it: 350 trades of ~40 M5 blocks in 10 years."""
    n, days = STAGEB["trades"], STAGEB["days"]
    length = rng.integers(STAGEB["blocks"] // 2, STAGEB["blocks"] * 2, n)
    off = np.concatenate([[0], np.cumsum(length)])
    level = np.concatenate([np.cumsum(rng.normal(0.02, 0.25, k)) for k in length]).astype(np.float32)
    opened = np.sort(rng.choice(days - 2, n, replace=False)).astype(np.int32)
    return {"low": level - 0.1, "high": level + 0.1, "level": level, "off": off,
            "pnl": level[off[1:] - 1].astype(float), "open_day": opened,
            "open_slot": rng.integers(0, per_day // 2, n).astype(np.int32),
            "gaps": np.diff(opened).astype(np.int64) * per_day, "n_overlap": 0,
            "per_day": per_day, "n_days": days}


def stage_b(cfg: dict) -> dict:
    """One 5-member combination through stage B: three Monte Carlos, every block length, every risk.

    The committed knobs (10,000 paths; the sweep of 5, 10, 20 and 40 days and the measured
    length) on a 10-year build with exact minutes, against FTMO's two-phase plan (100 risk
    settings). `open_risk_cap` is the owner's and unset: 1.0 here only sizes the workload.

    Args:
        cfg: What perf's config.load() returned (unused).

    Returns:
        Paths drawn and judged; nothing read from disk.
    """
    rng = np.random.default_rng(SEED)
    engine = config.load(["funded.open_risk_cap=1.0"])
    k, days, per_day = STAGEB["members"], STAGEB["days"], 1440 // engine["equity"]["block_minutes"]
    units = [_trade_units(rng, per_day) for _ in range(k)]
    closed = np.zeros((k, days))
    for row, unit in enumerate(units):
        np.add.at(closed[row], unit["open_day"], unit["pnl"])
    minutes = rng.normal(0, 0.2, (k, days * 1440)).astype(np.float32)
    data = {"days": np.arange(days), "closed": closed, "float_end": np.zeros((k, days)),
            "opened": (closed != 0).astype(np.int64), "low1": minutes - 0.2, "high1": minutes + 0.2,
            "minute_day": np.repeat(np.arange(days, dtype=np.int32), 1440), "units": units,
            "lot_unit": np.ones(k)}
    plan = catalog.plan(STAGEB["plan"])
    rows = stageb.evaluate(data, np.arange(k), plan, engine, stageb.risk_grid(plan, engine), rng)
    return {"scale": int(rows["flavour"].size // rows["setting"].nunique() * engine["stageb"]["n_paths"]),
            "bytes_in": 0}


def weights_wf(cfg: dict) -> dict:
    """The weight walk-forward's maths on a synthetic 5-member portfolio: 8 years to estimate, 4 to test.

    Every `weights.REGISTRY` method re-estimated each January (4 windows), 2,000 bootstrap
    resamples. `wf.confidence` is the owner's and unset: 0.95 here only sizes the workload.

    Args:
        cfg: What perf's config.load() returned (unused).

    Returns:
        Arms compared; nothing read from disk.
    """
    rng = np.random.default_rng(SEED)
    engine = config.load(["wf.confidence=0.95", "wf.step_years=1"])
    days = pd.bdate_range("2012-01-02", "2023-12-29")
    unit = pd.DataFrame(0.05 + rng.normal(size=(len(days), 5)) * [1, 1.5, 2, 2.5, 3], index=days)
    cuts = walkforward.folds(days, pd.Timestamp("2020-01-01"), 0, 1)
    table = walkforward.compare(walkforward.arms(unit, cuts, weights.REGISTRY, engine), engine, rng)
    return {"scale": len(table), "bytes_in": 0}


def funded_bank(cfg: dict) -> dict:
    """The whole bank table (encargo 33 §4) on a synthetic path set: every plan × add-on × risk × re-buy policy.

    Args:
        cfg: What perf's config.load() returned (unused).

    Returns:
        Configurations scored; nothing read from disk but the catalogue.
    """
    rng = np.random.default_rng(SEED)
    shape = (BANK["n_paths"], BANK["horizon"])
    closed = rng.normal(0.14, 1.0, shape) * (rng.random(shape) < 0.6)
    paths = {"closed": closed, "float_end": np.zeros(shape), "low": np.minimum(closed, 0.0) - 0.2,
             "high": np.maximum(closed, 0.0) + 0.2, "opened": (closed != 0).astype(np.int32)}
    engine = bank_inputs.load(BANK_SETS)
    variants, _, _ = bank_table.variants(engine)
    hazards = bank.hazards(*shape, engine["owner"]["p_payout_denied"],
                           engine["owner"]["p_firm_closes_year"], 252.0, rng)
    built = bank_table.build(paths, monkey.zero_edge(paths, engine["monkey"]["model"]),
                             {"unit_risk": 1.0, "days_per_year": 252.0}, engine, variants, hazards)
    return {"scale": len(built["search"]), "bytes_in": 0}
