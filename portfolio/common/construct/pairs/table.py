"""Long-form pairwise measure table over every pair of build columns, in parallel blocks of pairs."""

import itertools

import numpy as np
import pandas as pd

from core import fanout

from . import measures, rolling, stress

CHUNK_PAIRS = 500          # small blocks: many more blocks than cores keeps every core busy
_STATE: dict = {}          # set before the pool forks; workers read it without pickling
COLUMNS = ("i", "j", "measure", "value", "n_overlap_months")


def table(daily_build: pd.DataFrame, monthly_build: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Every measure of `pairs/` for every pair of columns, pair blocks spread over every core.

    Args:
        daily_build: Days x identities, build slice only, NaN outside a member's history.
        monthly_build: Months x identities, calendar-month sums of the same slice.
        cfg: The engine's config (`cfg["pairs"]`: tail_quantile, rolling_months, recent_months,
            stress_quantile).

    Returns:
        Long form, one row per (i, j, measure), i < j: `measure` one of pearson_monthly,
        pearson_daily, spearman_monthly, spearman_daily, co_loss, tail, rolling_pearson_whole,
        rolling_pearson_recent, rolling_spearman_whole, rolling_spearman_recent, stress.
        `value` signed; the rolling rows hold the max |rho|. `n_overlap_months` is the same for
        every row of a pair — months where both monthly series are finite.
    """
    identities = sorted(daily_build.columns)
    pairs = list(itertools.combinations(identities, 2))
    if not pairs:
        return pd.DataFrame(columns=COLUMNS)
    _STATE.update(
        pcfg=cfg["pairs"], pairs=pairs,
        stress=daily_build.index.isin(stress.stress_days(daily_build, cfg["pairs"]["stress_quantile"])),
        monthly={c: monthly_build[c].to_numpy(dtype=float) for c in identities},
        daily={c: daily_build[c].to_numpy(dtype=float) for c in identities})
    # Workers hold only a few MB (the matrices are shared by fork), so every core is used.
    starts = range(0, len(pairs), CHUNK_PAIRS)
    frames = [got for _, got in fanout.run(_chunk, {k: 1 for k in starts}, fanout.CORES)]
    _STATE.clear()
    return pd.concat(frames, ignore_index=True).sort_values(["i", "j"], kind="stable",
                                                            ignore_index=True)


def _chunk(start: int) -> pd.DataFrame:
    """One block of pairs, in a worker: every measure row of pairs[start : start + CHUNK_PAIRS]."""
    m, d, pcfg = _STATE["monthly"], _STATE["daily"], _STATE["pcfg"]
    rows = []
    for i, j in _STATE["pairs"][start:start + CHUNK_PAIRS]:
        rows.extend(_pair_rows(i, j, m[i], m[j], d[i], d[j], _STATE["stress"], pcfg))
    return pd.DataFrame(rows, columns=COLUMNS)


def _pair_rows(i: str, j: str, am: np.ndarray, bm: np.ndarray, ad: np.ndarray, bd: np.ndarray,
               stress_mask: np.ndarray, pcfg: dict) -> list[dict]:
    """Every measure row for one pair, monthly arrays `am`/`bm` and daily arrays `ad`/`bd`."""
    n_overlap = measures.overlap(am, bm)
    roll_pearson = rolling.rolling_max(am, bm, pcfg["rolling_months"], pcfg["recent_months"], "pearson")
    roll_spearman = rolling.rolling_max(am, bm, pcfg["rolling_months"], pcfg["recent_months"], "spearman")
    values = {
        "pearson_monthly": measures.pearson(am, bm, pcfg),
        "pearson_daily": measures.pearson(ad, bd, pcfg),
        "spearman_monthly": measures.spearman(am, bm, pcfg),
        "spearman_daily": measures.spearman(ad, bd, pcfg),
        "co_loss": measures.co_loss(am, bm, pcfg),
        "tail": measures.tail(am, bm, pcfg),
        "rolling_pearson_whole": roll_pearson["whole_abs"],
        "rolling_pearson_recent": roll_pearson["recent_abs"],
        "rolling_spearman_whole": roll_spearman["whole_abs"],
        "rolling_spearman_recent": roll_spearman["recent_abs"],
        "stress": stress.stress_corr(ad, bd, stress_mask),
    }
    return [{"i": i, "j": j, "measure": name, "value": value, "n_overlap_months": n_overlap}
            for name, value in values.items()]
