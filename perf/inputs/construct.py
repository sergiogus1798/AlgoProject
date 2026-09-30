"""The portfolio engine's work the catalogue times: one universe member, and the pool's pairs table."""

import numpy as np
import pandas as pd

from core.archive.read import listing
from core.paths import bar_source
from portfolio.common.construct.equity import universe
from portfolio.common.construct.inputs import config, source
from portfolio.common.construct.pairs import table

PAIRS_POOL = 500   # strategies in the synthetic pool: 124,750 pairs, the plan's large case


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


def pairs_table(cfg: dict) -> dict:
    """Every pair measure over a 500-strategy synthetic pool on a 10-year build, on every core.

    Args:
        cfg: What perf's config.load() returned (unused).

    Returns:
        Pairs measured; nothing read from disk.
    """
    days = pd.bdate_range("2008-01-01", "2017-12-29")
    daily = pd.DataFrame(np.random.default_rng().normal(size=(len(days), PAIRS_POOL)), index=days,
                         columns=[f"S{k:03d}" for k in range(PAIRS_POOL)])
    got = table.table(daily, daily.groupby(daily.index.to_period("M")).sum(), config.load())
    return {"scale": int(len(got) // 11), "bytes_in": 0}
