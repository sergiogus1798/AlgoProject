"""Family D's execution: stationary bootstrap inside every calendar window and volatility
tercile, plus the two time series its page draws."""

import numpy as np
import pandas as pd

from strategies.monteCarlo import config, confidence, engine, metrics, regime, stitch, windows


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
    sims = cfg["family_d"]["window_sims"]
    q = cfg["global"]["report_percentile"]
    rows = []
    for span in spans:
        pos = span["positions"]
        if pos.size < confidence.MEAN_PROVISIONAL:
            rows.append({**{k: span[k] for k in ("start", "end")}, "n": int(pos.size),
                         "median_net": float("nan"), "net_5": float("nan"),
                         "pf_5": float("nan"), "shape": None})
            continue
        got = engine.single(engine.payload(source, pos), "draw", "stationary",
                            config.stationary_block(pos.size), sims, cfg)
        net_seen = float(source["pnl"][pos].sum())
        rows.append({**{k: span[k] for k in ("start", "end")}, "n": int(pos.size),
                     "median_net": float(np.median(got["net"])),
                     "net_5": float(np.percentile(got["net"], 5)),
                     "pf_5": float(np.nanpercentile(got["pf"], 5)),
                     "shape": metrics.shape(got["net"], net_seen, q) if want_shape else None})
    return rows


def run(source: dict, day: pd.DataFrame, cfg: dict) -> dict:
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
             "bucket": np.digitize(vol["vol"][scored].to_numpy(), edges).tolist()}
    buckets = {}
    for name, pos in tagged["positions"].items():
        got = engine.single(engine.payload(source, pos), "draw", "stationary",
                            config.stationary_block(pos.size), d["window_sims"], cfg)
        net_seen = float(source["pnl"][pos].sum())
        buckets[name] = {"n": int(pos.size), "net": net_seen,
                         "median_net": float(np.median(got["net"])),
                         "net_5": float(np.percentile(got["net"], 5)),
                         "pf_5": float(np.nanpercentile(got["pf"], 5)),
                         "shape": metrics.shape(got["net"], net_seen,
                                                cfg["global"]["report_percentile"])}
    total = float(source["pnl"].sum())
    equity0 = cfg["global"]["starting_equity"]
    return {"overlapping": over,
            "nonoverlapping": _slices(source, segments, cfg, want_shape=True),
            "equity": {"curve": (equity0 + np.cumsum(source["pnl"])).tolist(),
                      "marks": marks},
            "regime": {"model": vol["model"], "note": vol["note"],
                       "edges": edges, "coverage": tagged["coverage"],
                       "buckets": buckets, "series": series,
                       "concentration": max(b["net"] for b in buckets.values()) / total},
            "stitch": stitch.worst_path(source["pnl"], segments, d["window_sims"],
                                        d["stitch_quantiles"],
                                        cfg["global"]["starting_equity"]),
            "calendar": {k: v.round(0).to_dict()
                         for k, v in windows.calendar(source["open"],
                                                      source["pnl"]).items()}}
