"""The exit and parameter sweep of one cell: every entry at nearby parameters under every exit."""

import copy
import time
import zlib

import numpy as np
import pandas as pd

from studies.research.marketProfile import higher, one, series
from studies.research.marketProfile.measure.position import walk
from studies.research.marketProfile.measure.rules import _down, _first
from studies.research.marketProfile.measure.trades import tstat

# Every entry of the sweep on a closed bar, written for longs, with its one parameter p.
ENTRIES = {
    "extreme": lambda x, p: _first(x["c"] < x["sma"] - p * x["atr"]),
    "rsi_low": lambda x, p: x["rsi"] < p,
    "down_run": lambda x, p: _down(x, int(p)),
    "rsi_up100": lambda x, p: (x["rsi"] < p) & (x["d1_above"][100] > 0),
    "rsi_up200": lambda x, p: (x["rsi"] < p) & (x["d1_above"][200] > 0),
    "ibs_low": lambda x, p: x["d1_ibs"] < p,
    "channel": lambda x, p: _first(x["c"] > x["hi"][int(p)]),
    "channel_d": lambda x, p: _first(x["c"] > x["d1_hi"][int(p)]),
    "prev_day": lambda x, p: _first(x["c"] > x["d1_hi"][int(p)]),
    "big_bar": lambda x, p: (x["c"] - x["o"]) > p * x["atr1"],
    "band": lambda x, p: x["c"] > x["sma"] + p * x["sd"],
    "tsmom_d": lambda x, p: x["d1_mom"][int(p)] > 0,
    "pullback": lambda x, p: _first(x["c"] > x[f"sma{int(p)}" if p != 20 else "sma"])
    & (x["d1_mom"][60] > 0)}
# The exits by condition, per kind of entry: (name, the condition that closes the trade).
LEAVES = {"fade": [("mean20", lambda x: x["c"] > x["sma"]), ("mean5", lambda x: x["c"] > x["sma5"])],
          "follow": [("low20", lambda x: x["c"] < x["lo"][20]), ("under20", lambda x: x["c"] < x["sma"])]}


def frame_cfg(cfg: dict) -> dict:
    """The config whose frame carries the channels and D1 means the sweep's entries read."""
    out = copy.deepcopy(cfg)
    out["derive"]["channels"] = cfg["sweep"]["channels"]
    out["higher"]["channels"] = cfg["sweep"]["d1_channels"]
    out["higher"]["means"] = cfg["sweep"]["d1_means"]
    return out


def exits(spec: dict, knobs: dict, per_day: int) -> list[tuple]:
    """The exits one entry is tried under: (name, leave key or None, cap, trail, stop)."""
    hold = per_day if spec["hold"] == "day" else spec["hold"]
    out = [(f"hold{m:g}x", None, max(1, round(m * hold)), 0.0, 0.0) for m in knobs["holds"]]
    out += [(f"trail{w:g}", None, 0, w, 0.0) for w in knobs["trails"]]
    out += [(name, name, 0, 0.0, 0.0) for name, _ in LEAVES[spec["kind"]]]
    return out + [(f"stop{knobs['stop']:g}_hold2x", None, 2 * hold, 0.0, knobs["stop"])]


def evaluate(d: dict, cal: dict, knobs: dict) -> list[tuple]:
    """Every variant on one framed series, long and short.

    Returns:
        (entry, parameter, exit, direction, statistic, entry bars, exit bars) in a fixed order.
    """
    out = []
    none = np.zeros(d["c"].size, dtype=bool)
    for direction, x in (("long", d), ("short", higher.mirror(d))):
        with np.errstate(invalid="ignore"):
            leaves = {name: fn(x) for kind in LEAVES.values() for name, fn in kind}
            for name, spec in knobs["entries"].items():
                for p in spec["params"]:
                    signal = ENTRIES[name](x, p)
                    for label, leave, cap, trail, stop in exits(spec, knobs, cal["per_day"]):
                        entry, exit_ = walk(signal, leaves[leave] if leave else none, cap, trail,
                                            x["c"], x["atr1"], stop)
                        out.append((name, p, label, direction,
                                    tstat(x, entry, exit_, cal["least"]), entry, exit_))
    return out


def run(symbol: str, timeframe: str, bars: pd.DataFrame, asset: dict, cfg: dict) -> pd.DataFrame:
    """The sweep of one asset on one timeframe, against the same shuffled null as the map.

    Args:
        symbol: Asset name.
        timeframe: A key of series.MINUTES.
        bars: Its build-segment bars at that timeframe (inputs.bars).
        asset: What core.assetdata.load() returned.
        cfg: The parsed config; `sweep` holds the grid.

    Returns:
        One row per entry, parameter, exit and direction: the statistic, its null mean and
        spread, z, p, and the money of one.money() — trades, effect, cost, multiple, years.
    """
    started = time.time()
    knobs, wide = cfg["sweep"], frame_cfg(cfg)
    x, cal = series.logs(bars), series.calendar(bars.index, timeframe, cfg)
    rng = np.random.default_rng([cfg["nulls"]["seed"], 1, zlib.crc32(f"{symbol}/{timeframe}".encode())])
    real = evaluate(one.framed(x, cal, wide), cal, knobs)
    g = series.gaps(x)
    sims = np.empty((knobs["draws"], len(real)))
    for b in range(knobs["draws"]):
        drawn = series.draw(g, x["o"][0], cfg["nulls"]["model"], cfg["nulls"]["block"][timeframe], rng)
        sims[b] = [r[4] for r in evaluate(one.framed(drawn, cal, wide), cal, knobs)]
    stats = np.array([r[4] for r in real])
    p = (1 + (sims >= stats).sum(axis=0)) / (sims.shape[0] + 1)
    years = (bars.index[-1] - bars.index[0]).days / 365.25
    rows = []
    for k, (name, param, label, direction, stat, entry, exit_) in enumerate(real):
        paid = one.money(bars, asset, direction, entry, exit_)
        spread = sims[:, k].std(ddof=1)
        rows.append({"symbol": symbol, "timeframe": timeframe, "direction": direction,
                     "family": knobs["entries"][name]["family"], "entry": name, "param": param,
                     "exit": label, "measure": f"{name}_{param:g}_{label}", "stat": stat,
                     "null_mean": sims[:, k].mean(), "null_sd": spread,
                     "z": (stat - sims[:, k].mean()) / spread if spread > 0 else 0.0,
                     "p": p[k] if entry.size >= cfg["filters"]["min_trades"] else 1.0, **paid,
                     "trades_per_year": paid["n_trades"] / years})
    return pd.DataFrame(rows).assign(wall_s=time.time() - started)
