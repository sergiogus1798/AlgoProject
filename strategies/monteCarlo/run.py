"""Everything one strategy is put through, assembled into the single result the report reads."""

import numpy as np
import pandas as pd

from strategies.monteCarlo import (confidence, costs, draws, engine, metrics, regime,
                                   significance, stitch, stream, stress, sweeps, windows)


def _family_a(runs: dict, seen: dict, cfg: dict) -> dict:
    """Order luck: what the drawdown looks like when the same trades arrive differently.

    Args:
        runs: Every sub-run's arrays, keyed by label.
        seen: The observed backtest's statistics.
        cfg: What config.load() returned.

    Returns:
        Per-label summaries, the headline drawdown percentiles and the inflation ratio. The
        ratio is the number to read: it says how much of the backtest's comfortable
        drawdown was the order the trades happened to arrive in.
    """
    qs = cfg["global"]["percentile_set"]
    labels = [k for k in runs if k == sweeps.HEADLINE or "shuffle" in k]
    head = runs[sweeps.HEADLINE]
    return {"runs": {k: metrics.table(runs[k], seen, qs) for k in labels},
            "shapes": {k: metrics.shapes(runs[k], seen) for k in labels},
            "invariant": {k: sweeps.invariant(runs[k]) for k in labels
                          if k.split("/")[0] in draws.KEEPS_MULTISET},
            "dd_pct_95": float(np.percentile(head["dd_pct"], 95)),
            "dd_pct_99": float(np.percentile(head["dd_pct"], 99)),
            "inflation": float(np.percentile(head["dd_pct"], 95) / seen["dd_pct"]),
            "shape": metrics.shape(head["dd_pct"], seen["dd_pct"])}


def _leave_one_out(pnl: np.ndarray) -> dict:
    """What the result loses when its single best trade is taken away.

    Args:
        pnl: Net USD per trade.

    Returns:
        Net profit without the best trade and the share of the total it carried. Not a
        simulation: the question is about one specific trade, so it is answered by removing
        that trade rather than by resampling around it.
    """
    total = float(pnl.sum())
    without = total - float(pnl.max())
    return {"net_without_best": without, "best": float(pnl.max()),
            "share": float(1 - without / total) if total else float("nan")}


def _family_b(runs: dict, source: dict, cfg: dict, sims: int) -> dict:
    """Composition luck: how much of the result rests on which trades occurred.

    Args:
        runs: Every sub-run's arrays, keyed by label.
        source: What stream.build() returned.
        cfg: What config.load() returned.
        sims: Simulations for the in-sample and out-of-sample re-runs.

    Returns:
        Per-label summaries, the worst 5th percentile across the resampling runs, the
        single-best-trade dependence and the IS/OOS level comparison. The gates read the
        worst sub-run rather than the independence baseline: block resampling keeps the
        runs of correlated trades that make a bad stretch possible.
    """
    seen = metrics.observed(source["pnl"], cfg["global"]["starting_equity"])
    qs = cfg["global"]["percentile_set"]
    labels = [k for k in runs if "bootstrap" in k]
    parts = {}
    for name, positions in stream.samples(source).items():
        if positions.size < confidence.MEAN_PROVISIONAL:
            continue
        cut = engine.payload(source, positions)
        got = engine.single(cut, "draw", "iid_bootstrap", 0, sims, cfg)
        parts[name] = {"n": int(positions.size),
                       "sharpe": float(np.median(got["sharpe"])),
                       "net": float(np.median(got["net"])),
                       "pf_5": float(np.nanpercentile(got["pf"], 5))}
    ratio = (parts["OOS"]["sharpe"] / parts["IS"]["sharpe"]
             if {"IS", "OOS"} <= parts.keys() and parts["IS"]["sharpe"] else float("nan"))
    return {"runs": {k: metrics.table(runs[k], seen, qs) for k in labels},
            "shapes": {k: metrics.shapes(runs[k], seen) for k in labels},
            "net_5": min(float(np.percentile(runs[k]["net"], 5)) for k in labels),
            "pf_5": min(float(np.nanpercentile(runs[k]["pf"], 5)) for k in labels),
            "outlier": _leave_one_out(source["pnl"]),
            "samples": parts, "oos_ratio": float(ratio),
            "shape": metrics.shape(runs[sweeps.BASELINE]["net"], seen["net"])}


def _family_c(source: dict, cfg: dict, sims: int) -> dict:
    """Execution luck: the same trades under worse fills, worse costs and missed entries.

    Args:
        source: What stream.build() returned.
        cfg: What config.load() returned.
        sims: Simulations per sub-test.

    Returns:
        One entry per sub-test with the numbers its floor is read against. Nothing here
        decides anything: gates.py owns every threshold.
    """
    seen = metrics.observed(source["pnl"], cfg["global"]["starting_equity"])
    data = engine.payload(source)
    out = {}
    for name in stress.STRESS:
        got = engine.run(data, "stress", name, 0, sims, cfg, stress.TITLES[name])
        out[name] = {"median_net": float(np.median(got["net"])),
                     "net_5": float(np.percentile(got["net"], 5)),
                     "pf_5": float(np.nanpercentile(got["pf"], 5)),
                     "keep": float(np.median(got["net"]) / seen["net"]),
                     "model": stress.MODELS[name],
                     "table": metrics.table(got, seen, cfg["global"]["percentile_set"]),
                     "shapes": metrics.shapes(got, seen)}
    return out


def _slices(source: dict, spans: list[dict], cfg: dict) -> list[dict]:
    """Composition bootstrap inside each calendar slice of the history.

    Args:
        source: What stream.build() returned.
        spans: What windows.rolling() returned.
        cfg: What config.load() returned.

    Returns:
        One row per window: its dates, its trade count and the low percentiles of its own
        resampled distribution. A window with a negative median is a period in which the
        strategy did not work, which no average over windows may hide.
    """
    sims = cfg["family_d"]["window_sims"]
    rows = []
    for span in spans:
        pos = span["positions"]
        if pos.size < confidence.MEAN_PROVISIONAL:
            rows.append({**{k: span[k] for k in ("start", "end")}, "n": int(pos.size),
                         "median_net": float("nan"), "net_5": float("nan"),
                         "pf_5": float("nan")})
            continue
        got = engine.single(engine.payload(source, pos), "draw", "iid_bootstrap", 0,
                            sims, cfg)
        rows.append({**{k: span[k] for k in ("start", "end")}, "n": int(pos.size),
                     "median_net": float(np.median(got["net"])),
                     "net_5": float(np.percentile(got["net"], 5)),
                     "pf_5": float(np.nanpercentile(got["pf"], 5))})
    return rows


def _family_d(source: dict, day: pd.DataFrame, cfg: dict) -> dict:
    """Regime luck: where in time and in market state the edge actually lived.

    Args:
        source: What stream.build() returned.
        day: Daily candles, from regime.daily().
        cfg: What config.load() returned.

    Returns:
        The overlapping and non-overlapping window curves, the volatility buckets, the
        stitched stress path and the calendar split.
    """
    d = cfg["family_d"]
    over = _slices(source, windows.rolling(source["open"], d["window_months"],
                                           d["window_step_months"]), cfg)
    segments = windows.rolling(source["open"], d["window_months"], d["window_months"])
    vol = regime.VOL[d["vol_model"]](day, d)
    tagged = regime.tag(source["open"], vol["vol"])
    buckets = {}
    for name, pos in tagged["positions"].items():
        got = engine.single(engine.payload(source, pos), "draw", "iid_bootstrap", 0,
                            d["window_sims"], cfg)
        buckets[name] = {"n": int(pos.size), "net": float(source["pnl"][pos].sum()),
                         "median_net": float(np.median(got["net"])),
                         "net_5": float(np.percentile(got["net"], 5)),
                         "pf_5": float(np.nanpercentile(got["pf"], 5))}
    total = float(source["pnl"].sum())
    return {"overlapping": over, "nonoverlapping": _slices(source, segments, cfg),
            "regime": {"model": vol["model"], "note": vol["note"],
                       "edges": tagged["edges"], "coverage": tagged["coverage"],
                       "buckets": buckets,
                       "concentration": max(b["net"] for b in buckets.values()) / total},
            "stitch": stitch.worst_path(source["pnl"], segments, d["window_sims"], 0.05,
                                        cfg["global"]["starting_equity"]),
            "calendar": {k: v.round(0).to_dict()
                         for k, v in windows.calendar(source["open"],
                                                      source["pnl"]).items()}}


def one(source: dict, step: dict, cfg: dict) -> dict:
    """A single sub-test on demand, without redoing the rest.

    Args:
        source: What stream.build() returned.
        step: One entry of sweeps.plan(), or {"label", "model", "block", "title"} naming a
            Family C perturbation.
        cfg: What config.load() returned.

    Returns:
        That sub-run's percentile table and the histogram of every statistic. It judges
        nothing: a sub-test re-run on its own cannot move a verdict, which is decided from
        one whole analysis or from none.
    """
    seen = metrics.observed(source["pnl"], cfg["global"]["starting_equity"])
    kind = "stress" if step["model"] in stress.STRESS else "draw"
    got = engine.run(engine.payload(source), kind, step["model"], step["block"],
                     cfg["global"]["n_sims"], cfg, step["title"])
    return {"label": step["label"], "title": step["title"],
            "table": metrics.table(got, seen, cfg["global"]["percentile_set"]),
            "shapes": metrics.shapes(got, seen)}


def analyse(source: dict, day: pd.DataFrame, asset: dict, cfg: dict) -> dict:
    """Put one trade stream through every family and return the whole result.

    Args:
        source: What stream.build() or stream.portfolio() returned.
        day: Daily candles, from regime.daily().
        asset: What costs.load() returned.
        cfg: What config.load() returned.

    Returns:
        The result the gates, the score and the report all read. This function produces
        numbers and judges none of them.
    """
    g = cfg["global"]
    n = int(source["pnl"].size)
    seen = metrics.observed(source["pnl"], g["starting_equity"])
    steps = sweeps.plan(n, cfg)
    runs = sweeps.execute(engine.payload(source), steps, g["n_sims"], cfg)
    psr = significance.psr(source["pnl"], cfg["family_e"]["psr_benchmark"])
    return {"name": source["name"], "n_trades": n, "observed": seen,
            "blocks": sorted({s["block"] for s in steps if s["block"] > 1}),
            "titles": {s["label"]: s["title"] for s in steps},
            "A": _family_a(runs, seen, cfg),
            "B": _family_b(runs, source, cfg, g["n_sims"]),
            "C": _family_c(source, cfg, g["n_sims"]),
            "D": _family_d(source, day, cfg),
            "E": {**psr, **significance.crosscheck(psr["psr"],
                                                   runs[sweeps.BASELINE]["sharpe"])},
            "cost_check": costs.crosscheck(source["frame"], asset),
            "overlap": stream.overlap(source)}
