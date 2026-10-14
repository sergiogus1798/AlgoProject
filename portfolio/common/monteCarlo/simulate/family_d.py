"""Family D's execution: stationary bootstrap inside every calendar window and volatility
tercile, plus the two time series its page draws."""

from typing import TypedDict

import numpy as np
import pandas as pd

from engines.regimes import regime
from portfolio.common.monteCarlo.inputs import config
from portfolio.common.monteCarlo.model import windows
from portfolio.common.monteCarlo.simulate import engine, metrics, stitch
from portfolio.common.monteCarlo.verdict import confidence


class FamilyD(TypedDict):
    """Family D's whole result: window curves, the equity with its marks, the regime split, the stitched path, the calendar."""

    overlapping: list[dict]
    nonoverlapping: list[dict]
    equity: dict[str, list]
    regime: dict
    stitch: dict
    calendar: dict[str, dict]



def _resampled(job: tuple) -> dict:
    """One slice's stationary bootstrap, summarised where it ran so only four figures travel.

    Args:
        job: (payload of the slice, its observed net, sims, the whole config, keep the
            histogram, the slice's own seed).

    Returns:
        `median_net`, `net_5`, `pf_5` and `shape` (None unless asked for).
    """
    data, net_seen, sims, cfg, want_shape, seed = job
    got = engine.single(data, "draw", "stationary", config.stationary_block(data["pnl"].size),
                        sims, cfg, seed)
    return {"median_net": float(np.median(got["net"])),
            "net_5": float(np.percentile(got["net"], 5)),
            "pf_5": float(np.nanpercentile(got["pf"], 5)),
            "shape": metrics.shape(got["net"], net_seen, cfg["global"]["report_percentile"])
            if want_shape else None}


def _bootstrapped(source: dict, slices: list[np.ndarray], cfg: dict,
                  want_shape: bool) -> list[dict]:
    """`_resampled` for every slice of trade positions, across the pool (`engine.mapped`)."""
    jobs = [(engine.payload(source, pos), float(source["pnl"][pos].sum()),
             cfg["family_d"]["window_sims"], cfg, want_shape, config.seed(cfg) + i)
            for i, pos in enumerate(slices)]
    return engine.mapped(_resampled, jobs, cfg=cfg)


def _slices(source: dict, spans: list[dict], cfg: dict, want_shape: bool = False) -> list[dict]:
    """Stationary bootstrap inside each calendar slice of the history.

    Args:
        source: What stream.build() returned.
        spans: What windows.rolling() returned.
        cfg: What config.load() returned.
        want_shape: Keep the histogram too. True for the non-overlapping blocks, where
            there are few enough to look at one by one; false for the rolling windows,
            which overlap so heavily that a histogram per window would mostly repeat itself.

    Returns:
        One row per window: its dates, its trade count and the low percentiles of its own
        resampled distribution. Stationary, not i.i.d.: a window is a couple of years, short
        enough that trades inside it are plausibly correlated (a streak, a regime), and the
        independence assumption would smooth that away and read more comfortable than it
        is. A window with a negative median is a period in which the strategy did not work,
        which no average over windows may hide.
    """
    blank = {"median_net": float("nan"), "net_5": float("nan"), "pf_5": float("nan"),
             "shape": None}
    enough = [s["positions"] for s in spans if s["positions"].size >= confidence.MEAN_PROVISIONAL]
    done = iter(_bootstrapped(source, enough, cfg, want_shape))
    return [{**{k: span[k] for k in ("start", "end")}, "n": int(span["positions"].size),
             **(next(done) if span["positions"].size >= confidence.MEAN_PROVISIONAL else blank)}
            for span in spans]


def concentration(nets: list[float], total: float) -> float:
    """The share of the profit that one volatility tercile holds; NaN when there is no profit to share."""
    return max(nets) / total if total > 0 else float("nan")


def run(source: dict, day: pd.DataFrame, cfg: dict) -> FamilyD:
    """Regime luck: where in time and in market state the edge actually lived.

    Args:
        source: What stream.build() returned.
        day: Daily candles, from regime.daily().
        cfg: What config.load() returned.

    Returns:
        The overlapping and non-overlapping window curves, the equity curve with the
        window marks, the volatility buckets and their own price/vol time series, the
        stitched stress path and the calendar split.
    """
    d = cfg["family_d"]
    over = _slices(source, windows.rolling(source["open"], d["window_months"],
                                           d["window_step_months"]), cfg)
    segments = windows.rolling(source["open"], d["window_months"], d["window_months"])
    marks = np.cumsum([len(s["positions"]) for s in segments])[:-1].tolist()
    vol = regime.VOL[d["vol_model"]](day, d)
    tagged = regime.tag(source["open"], vol["vol"])
    scored = vol["vol"].notna()
    edges = tagged["edges"]
    series = {"dates": [dt.date().isoformat() for dt in day.index[scored]],
             "price": day["Close"][scored].tolist(),
             "vol": vol["vol"][scored].tolist(),
             "bucket": np.digitize(np.asarray(vol["vol"][scored]), edges).tolist()}
    names = list(tagged["positions"])
    buckets = {name: {"n": int(tagged["positions"][name].size),
                      "net": float(source["pnl"][tagged["positions"][name]].sum()), **got}
               for name, got in zip(names, _bootstrapped(
                   source, [tagged["positions"][n] for n in names], cfg, True))}
    total = float(source["pnl"].sum())
    equity0 = cfg["global"]["starting_equity"]
    return {"overlapping": over,
            "nonoverlapping": _slices(source, segments, cfg, want_shape=True),
            "equity": {"curve": (equity0 + np.cumsum(source["pnl"])).tolist(),
                      "marks": marks},
            "regime": {"model": vol["model"], "note": vol["note"],
                       "edges": edges, "coverage": tagged["coverage"],
                       "buckets": buckets, "series": series,
                       "concentration": concentration([b["net"] for b in buckets.values()], total)},
            "stitch": stitch.worst_path(source["pnl"], segments, d["window_sims"],
                                        d["stitch_quantiles"],
                                        cfg["global"]["starting_equity"]),
            "calendar": {k: v.round(0).to_dict()
                         for k, v in windows.calendar(source["open"],
                                                      source["pnl"]).items()}}
