"""One cell — an asset on a timeframe: every measure on the real bars and on its null draws."""

import json
import time
import zlib

import numpy as np
import pandas as pd

from studies.research.marketProfile import context, higher, inputs, series
from studies.research.marketProfile.measure import REGISTRY, SYMMETRIC


def evaluate(d: dict, cal: dict, specs: list[dict]) -> list[tuple]:
    """Every measure on one series: once when it has no direction, else long and short.

    Args:
        d: What framed() returned.
        cal: What series.calendar() returned.
        specs: The `measures` rows of the config.

    Returns:
        (name, direction, statistic, entry, exit, detail) in a fixed order, so the real
        series and each null draw line up column by column.
    """
    up = higher.mirror(d)
    out = []
    for spec in specs:
        fn = REGISTRY[spec["fn"]]
        if spec["fn"] in SYMMETRIC:
            out.append((spec["name"], "both", *fn(d, cal, **spec["args"])))
        else:
            out.append((spec["name"], "long", *fn(d, cal, **spec["args"])))
            out.append((spec["name"], "short", *fn(up, cal, **spec["args"])))
    return out


def framed(x: dict, cal: dict, cfg: dict) -> dict:
    """A log series with everything a measure reads: the shared indicators and the wider frame."""
    return higher.context(series.derive(x, cfg["derive"]), cal, cfg["higher"])


def money(bars: pd.DataFrame, asset: dict, direction: str, entry: np.ndarray,
          leave: np.ndarray) -> dict:
    """What a measure's trades earned on the real bars, in price units, against their cost.

    Returns:
        Trades, mean gross effect and mean cost per trade, their ratio, and the mean effect
        of each build year — what the cost filter and the stability filter read.
    """
    if entry is None or entry.size == 0:
        return {"n_trades": 0 if entry is not None else None}
    opens = bars["Open"].to_numpy()
    sign = 1 if direction == "long" else -1
    pnl = sign * (opens[leave] - opens[entry])
    paid = inputs.cost(asset, opens[entry])
    yearly = pd.Series(pnl).groupby(bars.index.year[entry]).mean()
    return {"n_trades": int(entry.size), "effect": pnl.mean(), "cost": paid.mean(),
            "multiple": pnl.mean() / paid.mean(), "years": int(yearly.size),
            "years_with_sign": int((yearly > 0).sum()),
            "per_year": json.dumps({int(y): float(v) for y, v in yearly.items()})}


def against_null(x: dict, cal: dict, cfg: dict, block: int,
                 rng: np.random.Generator) -> tuple[list[tuple], np.ndarray]:
    """Every measure on a series and on its block-resampled draws.

    Args:
        x: What series.logs() returned.
        cal: Its calendar.
        cfg: The parsed config.
        block: Bars per block.
        rng: Generator.

    Returns:
        (what evaluate() returns for the series, the statistics of the draws — one row per
        draw, one column per measure and direction).
    """
    nulls, specs = cfg["nulls"], cfg["measures"]
    real = evaluate(framed(x, cal, cfg), cal, specs)
    g = series.gaps(x)
    sims = np.empty((nulls["draws"], len(real)))
    for b in range(nulls["draws"]):
        drawn = series.draw(g, x["o"][0], nulls["model"], block, rng)
        sims[b] = [r[2] for r in evaluate(framed(drawn, cal, cfg), cal, specs)]
    return real, sims


def pvalues(real: list[tuple], sims: np.ndarray) -> np.ndarray:
    """The share of null draws at or above each real statistic, the real one counted in."""
    stats = np.array([r[2] for r in real])
    return (1 + (sims >= stats).sum(axis=0)) / (sims.shape[0] + 1)


def overlap(real: list[tuple], family: dict, n: int) -> list[dict]:
    """How much the families fire on the same bars, per direction.

    Args:
        real: What evaluate() returned for the real series.
        family: Measure name to family.
        n: Bars in the series.

    Returns:
        One row per direction and pair of families: the correlation between "some measure of
        this family enters on this bar" and the same for the other family.
    """
    rows = []
    for direction in ("long", "short"):
        fired = {}
        for name, d, _, entry, _, _ in real:
            if d == direction and entry is not None:
                fired.setdefault(family[name], np.zeros(n))[entry] = 1.0
        names = list(fired)
        with np.errstate(divide="ignore", invalid="ignore"):
            corr = np.corrcoef([fired[f] for f in names])
        rows += [{"direction": direction, "family_a": a, "family_b": b, "phi": corr[i, j]}
                 for i, a in enumerate(names) for j, b in enumerate(names) if i < j]
    return rows


def run(symbol: str, timeframe: str, bars: pd.DataFrame, asset: dict, cfg: dict) -> dict:
    """The profile of one asset on one timeframe.

    Args:
        symbol: Asset name.
        timeframe: A key of series.MINUTES.
        bars: Its build-segment bars at that timeframe (inputs.bars).
        asset: What core.assetdata.load() returned.
        cfg: The parsed config.

    Returns:
        {"rows": one dict per measure and direction — statistic, null mean and spread, z, p,
        trades, effect, cost, stability, detail, `tag` (what the measure adds to the original
        set) and `needs_clock` —, "context": the cell's context block,
        "overlap": what overlap() returns, "wall_s": seconds}. A measure with fewer trades than `min_trades` is not tested: p 1.
    """
    started = time.time()
    family = {s["name"]: s["family"] for s in cfg["measures"]}
    spec = {s["name"]: s for s in cfg["measures"]}
    block = cfg["nulls"]["block"][timeframe]
    rng = np.random.default_rng([cfg["nulls"]["seed"],
                                 zlib.crc32(f"{symbol}/{timeframe}".encode())])
    real, sims = against_null(series.logs(bars), series.calendar(bars.index, timeframe, cfg),
                              cfg, block, rng)
    p = pvalues(real, sims)
    years = (bars.index[-1] - bars.index[0]).days / 365.25
    rows = []
    for k, (name, direction, stat, entry, leave, detail) in enumerate(real):
        spread = sims[:, k].std(ddof=1)
        paid = money(bars, asset, direction, entry, leave)
        tested = entry is None or entry.size >= cfg["filters"]["min_trades"]
        rows.append({
            "symbol": symbol, "timeframe": timeframe, "direction": direction,
            "family": family[name], "measure": name, "tag": spec[name].get("tag", "base"),
            "lit": spec[name].get("lit", ""),
            "needs_clock": bool(spec[name].get("clock", False)), "stat": stat,
            "null_mean": sims[:, k].mean(), "null_sd": spread,
            "z": (stat - sims[:, k].mean()) / spread if spread > 0 else 0.0,
            "p": p[k] if tested else 1.0, **paid,
            "trades_per_year": (paid["n_trades"] or 0) / years,
            "detail": json.dumps(detail, default=float)})
    return {"rows": rows, "context": {"symbol": symbol, "timeframe": timeframe,
                                      "bars": len(bars), "block": block,
                                      **context.block(bars, asset)},
            "overlap": [{"symbol": symbol, "timeframe": timeframe, **o}
                        for o in overlap(real, family, len(bars))],
            "wall_s": time.time() - started}
