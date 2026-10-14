"""One asset of a group: every measure on its bars and on the group's joint null draws."""

import time
import zlib
from typing import TypedDict

import numpy as np
import pandas as pd

from studies.research.marketProfile import one as profile_one, series

# The profile's measures whose statistic is a hit rate, not the t of the trades: the spread of
# their null is in other units and cannot widen an error in costs.
HIT = ("inside", "engulfing", "run")


class Run(TypedDict):
    """One asset's measure rows, its null statistics (float32) and the seconds it took."""

    rows: pd.DataFrame
    sims: np.ndarray
    wall_s: float


def run(
    symbol: str, group: str, timeframe: str, bars: pd.DataFrame, asset: dict, cfg: dict
) -> Run:
    """The asset's measures against a null whose draws are the group's.

    Args:
        symbol: Asset name.
        group: The group it is judged in.
        timeframe: A key of series.MINUTES.
        bars: Its bars on the group's shared instants (inputs.bars).
        asset: What core.assetdata.load() returned.
        cfg: The parsed config.

    Returns:
        {"rows": one row per measure and direction — the statistic, its null mean and
        spread, z, the asset's own p, the trades and their money (marketProfile.one.money),
        `se` (the error of the mean gain per trade, in costs, widened by the null's spread of a t),
        `tested` and the shared window —, "sims": the null statistics, draws x tests, float32, "wall_s"}.
        The generator is seeded by the group and the timeframe, not by the asset: with the
        same number of bars every asset of the group draws the same positions, so the null
        resamples them jointly in time and keeps their cross-correlation
        (marketProfile.one.against_null, unchanged).
    """
    started = time.time()
    pcfg = cfg["profile"]
    spec = {s["name"]: s for s in pcfg["measures"]}
    rng = np.random.default_rng(
        [cfg["run"]["seed"], zlib.crc32(f"{group}/{timeframe}".encode())]
    )
    real, sims = profile_one.against_null(
        series.logs(bars),
        series.calendar(bars.index, timeframe, pcfg),
        pcfg,
        pcfg["nulls"]["block"][timeframe],
        rng,
    )
    p = profile_one.pvalues(real, sims)
    opens = bars["Open"].to_numpy()
    years = (bars.index[-1] - bars.index[0]).days / 365.25
    rows = []
    for k, (name, direction, stat, entry, leave, _) in enumerate(real):
        centre, spread = sims[:, k].mean(), sims[:, k].std(ddof=1)
        paid = profile_one.money(bars, asset, direction, entry, leave)
        tested = entry is None or entry.size >= pcfg["filters"]["min_trades"]
        se = np.nan
        if entry is not None and tested:
            noise = (opens[leave] - opens[entry]).std(ddof=1) / np.sqrt(entry.size)
            se = (1.0 if spec[name]["fn"] in HIT else spread) * noise / paid["cost"]
        rows.append(
            {
                "group": group,
                "symbol": symbol,
                "timeframe": timeframe,
                "direction": direction,
                "family": spec[name]["family"],
                "measure": name,
                "stat": stat,
                "null_mean": centre,
                "null_sd": spread,
                "z": (stat - centre) / spread if spread > 0 and tested else 0.0,
                "p": p[k] if tested else 1.0,
                "tested": bool(tested and spread > 0),
                **paid,
                "se": se,
                "trades_per_year": (paid["n_trades"] or 0) / years,
            }
        )
    rows = pd.DataFrame(rows).assign(
        bars=len(bars), first_bar=str(bars.index[0]), last_bar=str(bars.index[-1])
    )
    return {
        "rows": rows,
        "sims": sims.astype(np.float32),
        "wall_s": time.time() - started,
    }
