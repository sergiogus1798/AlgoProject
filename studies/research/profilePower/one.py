"""One replication: a directionless copy of a cell, an edge planted in it, the profile's test."""

import time
import zlib
from typing import Any, cast, TypedDict

import numpy as np
import pandas as pd

from studies.research.marketProfile import one as profile_one, series
from studies.research.profilePower import inputs, plant

SIDE = {"long": 0, "short": 1}


def reach(cut: float, draws: int) -> int:
    """The most null draws that may equal or beat the real statistic for p to reach `cut`."""
    return int(np.floor(cut * (draws + 1) + 1e-9)) - 1


def trades(x: dict, cal: dict, pcfg: dict, spec: dict, direction: str) -> tuple:
    """The measure's (statistic, entry bars, exit bars) on a series, in one direction."""
    row = profile_one.evaluate(profile_one.framed(x, cal, pcfg), cal, [spec])[SIDE[direction]]
    return row[2], row[3], row[4]


class Earned(TypedDict):
    """A measure's trades on a series: count, effect in round-trip costs, years, years with the sign."""

    n_trades: int
    multiple: float
    years: int
    years_with_sign: int


def earned(x: dict, cost: np.ndarray, year: np.ndarray, sign: int, entry: np.ndarray,
           leave: np.ndarray) -> Earned:
    """What the measure's trades earned on a series, in round-trip costs, and per year.

    The numbers marketProfile.one.money gives, read in logs: a planted series can drift far
    from the real price, and a mean in price units would then weigh its last trades only.
    """
    pnl = sign * (x["o"][leave] - x["o"][entry])
    yearly = pd.Series(pnl).groupby(year[entry]).mean()
    return {"n_trades": int(entry.size), "multiple": pnl.mean() / cost[entry].mean(),
            "years": int(yearly.size), "years_with_sign": int((yearly.to_numpy() > 0).sum())}


def tested(x: dict, cal: dict, pcfg: dict, spec: dict, direction: str, judge: dict,
           block: int, rng: np.random.Generator) -> dict[str, Any]:
    """The profile's own test of one measure on one series, stopped once the cut is out of reach.

    Args:
        x: The series under test (series.logs).
        cal: Its calendar.
        pcfg: The profile's config.
        spec: The measure's row of the profile's `measures`.
        direction: "long" or "short".
        judge: The `judge` section: `cut`, `chunk`.
        block: Bars per block of the null.
        rng: Generator.

    Returns:
        `exceed` (null draws at or above the real statistic), `drawn`, `p_first` (the p after
        the first chunk alone), and the first chunk's `null_mean` and `null_sd`. The draws
        come from marketProfile.one.against_null, a chunk per call on one generator: the same
        series as one call of `nulls.draws`, and a replication that stops early has already
        more exceedances than the cut allows at the full count.
    """
    draws, most = pcfg["nulls"]["draws"], reach(judge["cut"], pcfg["nulls"]["draws"])
    part = {**pcfg, "measures": [spec], "nulls": {**pcfg["nulls"], "draws": judge["chunk"]}}
    exceed, drawn = 0, 0
    first: dict | None = None
    while drawn < draws and exceed <= most:
        real, sims = profile_one.against_null(x, cal, part, block, rng)
        k = SIDE[direction]
        exceed += int((sims[:, k] >= real[k][2]).sum())
        drawn += judge["chunk"]
        first = first or {"p_first": (1 + exceed) / (drawn + 1), "stat": real[k][2],
                          "null_mean": sims[:, k].mean(), "null_sd": sims[:, k].std(ddof=1),
                          "entry": real[k][3], "leave": real[k][4]}
    return {**cast("dict", first), "exceed": exceed, "drawn": drawn, "draws": draws}


def run(key: tuple, bars: pd.DataFrame, asset: dict, cfg: dict) -> dict[str, Any]:
    """One planted edge, tested.

    Args:
        key: (symbol, timeframe, measure, direction, effect in costs, replication).
        bars: The cell's build-segment bars (inputs.bars).
        asset: What core.assetdata.load() returned.
        cfg: The parsed config.

    Returns:
        One row: the key, the family, what `tested` returns, and what the measure's trades
        earned on the planted series (earned) — the numbers the profile's other three
        filters read, at the base's costs. The directionless base depends on the cell and the
        replication alone, so every measure and effect is planted in the same copies.
    """
    started = time.time()
    symbol, timeframe, measure, direction, effect, rep = key
    pcfg = cfg["profile"]
    spec = next(s for s in pcfg["measures"] if s["name"] == measure)
    seed = [cfg["run"]["seed"], zlib.crc32(f"{symbol}/{timeframe}".encode()), rep]
    x, cal = series.logs(bars), series.calendar(bars.index, timeframe, pcfg)
    base = series.flipped(x, np.random.default_rng(seed))
    rng = np.random.default_rng(seed + [zlib.crc32(f"{measure}/{direction}/{effect}".encode())])
    _, entry, leave = trades(base, cal, pcfg, spec, direction)
    sign = 1 if direction == "long" else -1
    cost = inputs.cost_log(asset, base["o"])
    grown = plant.planted(base, entry, leave, sign, effect, cost, cfg["plant"]["how"], rng)
    got = tested(grown, cal, pcfg, spec, direction, cfg["judge"],
                 pcfg["nulls"]["block"][timeframe], rng)
    paid = earned(grown, cost, cast("Any", bars.index).year.to_numpy(), sign, got.pop("entry"),
                  got.pop("leave"))
    years = (bars.index[-1] - bars.index[0]).days / 365.25
    return {"symbol": symbol, "timeframe": timeframe, "family": spec["family"],
            "measure": measure, "direction": direction, "effect_planted": effect, "rep": rep,
            "how": cfg["plant"]["how"], **got, **paid,
            "trades_per_year": (paid["n_trades"] or 0) / years, "wall_s": time.time() - started}
