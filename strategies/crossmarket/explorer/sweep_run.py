"""The window sweep's execution: the free-placement models re-drawn inside ever smaller
calendar blocks. Split from analysis.py so both stay under CODESTYLE's 250-line cap; the
partitioning itself is `simulate/sweep.py`, which is modelling and knows nothing about running."""

from collections.abc import Callable

import numpy as np
import pandas as pd

from strategies.crossmarket.simulate import backtest, metrics, sweep
from strategies.crossmarket.verdict import inference


def window_sweep(fixed: dict, bars: pd.DataFrame, cfg: dict, runs: dict,
                 step: Callable[[str, float], None]) -> dict:
    """The free-placement models re-drawn inside ever smaller calendar blocks, on one market.

    Args:
        fixed: What backtest.setting() returned for this market.
        bars: That market's bars.
        cfg: What config.load() returned.
        runs: This market's model results, for the full-window point and the reference line.
        step: Called with (what is running, share of the sweep done).

    Returns:
        windows — per size its blocks, their weak flags and why a point was withheld;
        points — per model, per size, the whole result of that confined null: the metric
        table, a histogram per metric and the equity cone, plus the mean live trades per
        random run — resampled_holds and fitted_holds drop more of what overflows a block the
        smaller it is, so the count moves with the size. A withheld point is None throughout.
        trend — per model and per metric, inference.sweep_trend()'s key; reference — per
        metric, sweep.reference's p, drawn flat because that model's regime is already fixed.
        The full window is read from the model's own run rather than drawn again:
        tests/test_sweep.py shows they are the same draws. Every point draws nulls.draws runs
        from the same seed, and every point now costs what a null model costs — the sweep
        used to price only mean_r, and could therefore answer for no other statistic.
    """
    s = cfg["sweep"]
    labels = sweep.ordered(s["windows"])
    total = len(labels) * len(s["models"])
    windows, points = [], {m: [] for m in s["models"]}
    for i, window in enumerate(labels):
        block = sweep.partition(bars, window)
        rows = sweep.blocks(fixed["held"], block, bars.index, sweep.bar_hours(bars))
        power = inference.sweep_power(rows, sweep.months(window), cfg)
        windows.append({"window": window, "blocks": rows, **power})
        for j, model in enumerate(s["models"]):
            k = i * len(s["models"]) + j
            if power["reason"]:
                points[model].append({"table": None, "shapes": None, "cone": None,
                                      "trades": None})
                continue
            if window == sweep.FULL and model in runs:
                view = {k2: runs[model][k2] for k2 in ("table", "shapes", "cone")}
            else:
                view = backtest.summary(fixed, bars, cfg, backtest.drawn(
                    fixed, cfg,
                    lambda size, rng, done, m=model, b=block: sweep.confine(
                        m, fixed["held"], b, size, rng),
                    lambda done, n, k=k, w=window, m=model: step(f"barrido {w} · {m}",
                                                                 (k + done / n) / total)))
            points[model].append({**view, "trades": view["table"]["trades"]["mean"]})
    return {"windows": windows, "points": points,
            "reference": ({q: runs[s["reference"]]["table"][q]["p_value"]
                           for q in metrics.TABLED} if s["reference"] in runs else None),
            "trend": {m: {q: inference.sweep_trend(
                [{"p": None if pt["table"] is None else pt["table"][q]["p_value"]}
                 for pt in points[m]], cfg) for q in metrics.TABLED} for m in s["models"]}}
