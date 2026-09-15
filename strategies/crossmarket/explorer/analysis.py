"""One strategy's whole cross-market analysis: every null model and every test, market by market."""

from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

from core import trades as tradeio
from strategies.crossmarket import (backtest, breadth, correlation, drivers, envelope,
                                    exposure, fingerprint, inference, metrics, paired,
                                    significance, stress, sweep)


def tests(fixed: dict, bars: pd.DataFrame, cfg: dict) -> dict:
    """Every test besides the random-entry one, on one strategy and one market.

    Args:
        fixed: What backtest.setting() returned for this market.
        bars: That market's bars.
        cfg: What config.load() returned.

    Returns:
        A flat row: exposure (Test 1c), the paired test (Test 1b), significance, cost and
        execution stress. Takes `fixed` so the fill convention is reconciled once per market
        rather than once per test.
    """
    rng = np.random.default_rng(cfg["nulls"]["seed"])
    exp = exposure.run(fixed, bars, cfg, rng)
    pair = paired.run(fixed, bars, fixed["market"], cfg, rng)
    returns = significance.trade_returns(fixed, bars)
    mtr = significance.min_track_record(returns, cfg["diagnostics"]["alpha"])
    pf_ci = significance.bootstrap_metric(returns, significance.profit_factor, cfg, rng)
    ex_ci = significance.bootstrap_metric(returns, significance.expectancy, cfg, rng)
    s = cfg["stress"]
    return {"e": exp["e"], "a": exp["a"], "mu_m": exp["mu_m"], "mu_t": exp["mu_t"],
            "e_meaningful": exp["e_meaningful"], "risk_normalised": exp["risk_normalised"],
            "a_ci_lo": exp["a_ci"]["lo"], "a_ci_hi": exp["a_ci"]["hi"],
            "capture_median": exp["capture"]["median"], "capture_mean": exp["capture"]["mean"],
            "capture_dropped": exp["capture"]["dropped"],
            "paired_mean": pair["mean"], "paired_median": pair["median"], "paired_p": pair["p"],
            "paired_beat": pair["beat_share"], "paired_ci_lo": pair["ci"]["lo"],
            "paired_ci_hi": pair["ci"]["hi"],
            "pf": significance.profit_factor(returns), "pf_ci_lo": pf_ci["lo"],
            "pf_ci_hi": pf_ci["hi"], "expectancy": significance.expectancy(returns),
            "expectancy_ci_lo": ex_ci["lo"], "expectancy_ci_hi": ex_ci["hi"],
            "sharpe": significance.moments(returns)[0],
            "min_track_needed": mtr["needed"], "min_track_enough": mtr["enough"],
            "cost_gradient": stress.cost_gradient(fixed, bars, s["cost_multiples"]
                                                  ).to_dict("records"),
            "breakeven": stress.breakeven_multiple(fixed, bars),
            "bar_shift_decay": stress.bar_shift_stress(fixed, bars, s["bar_shift"]),
            "slippage_decay": {str(f): stress.range_slippage_stress(fixed, bars, f)
                               for f in s["slippage_fractions"]}}


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
        points — per model the p, the null's σ and the mean live trades per random run at
        each size, None where withheld — resampled_holds and fitted_holds drop more of what
        overflows a block the smaller it is, so the count moves with the size; trend — per
        model, inference.sweep_trend()'s key; reference — sweep.reference's p, drawn flat
        because that model's regime is already fixed. The full window is read from the
        model's own run rather than drawn again: tests/test_sweep.py shows they are the same
        draws. Every point draws nulls.draws runs from the same seed.
    """
    s = cfg["sweep"]
    seen = backtest.real(fixed, bars, cfg)["stats"]["mean_r"]
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
                points[model].append({"p": None, "sigma": None, "trades": None})
                continue
            if window == sweep.FULL and model in runs:
                v, live = runs[model]["table"]["mean_r"], runs[model]["table"]["trades"]["mean"]
            else:
                drawn = backtest.swept(
                    fixed, cfg,
                    lambda size, rng, m=model, b=block: sweep.confine(m, fixed["held"], b,
                                                                      size, rng),
                    lambda done, n, k=k, w=window, m=model: step(f"barrido {w} · {m}",
                                                                 (k + done / n) / total))
                v = metrics.summarise(drawn["mean_r"], seen, "mean_r",
                                      cfg["equity"]["percentiles"])
                live = float(drawn["trades"].mean())
            points[model].append({"p": v["p_value"], "sigma": v["std"], "trades": live})
    return {"windows": windows, "points": points,
            "reference": (runs[s["reference"]]["table"]["mean_r"]["p_value"]
                          if s["reference"] in runs else None),
            "trend": {m: inference.sweep_trend(points[m], cfg) for m in s["models"]}}


def analyse_market(cfg: dict, market: dict, trades: Path, bars: pd.DataFrame, base: dict,
                   step: Callable[[str, float], None]) -> tuple[dict, dict, pd.Series]:
    """Every test in this build on one strategy's trades on one market.

    Args:
        cfg: What config.load() returned.
        market: One row of markets.universe()'s `markets` — feed, category, data_from.
        trades: That market's trade CSV for this strategy.
        bars: That market's bars.
        base: What backtest.setting() returned for the same strategy on the base asset.
        step: Called with (what is running, share of this market done) for the progress bar.

    Returns:
        (row, runs, curve): the flat per-market row with its warnings attached, one full
        result per null model plus the window sweep and the execution stress, and the weekly
        equity curve for the correlation tab.
    """
    real = tradeio.read(trades)
    # Everything below runs on the backtest's own window, never on the whole bar file: the
    # nulls must not be able to trade years the real strategy never saw, and the statistics
    # that compare against the market's own average — the drift in Test 1c, the blind window
    # in Test 1b, the market's structural profile — have to describe the same stretch.
    bars = envelope.window(real, bars)
    fixed = backtest.setting(real, bars, cfg)
    feed = market["feed"]
    models = cfg["nulls"]["models"]
    # The summary reports the headline model's p, whatever order the panel shows them in:
    # it is the only one that changes exactly one thing, so the only one whose low p can be
    # attributed to entry timing rather than to the regime the run happened to land in.
    headline = cfg["nulls"]["headline"]
    # One unit per model, per sweep point and for the stress, so the bar moves evenly.
    swept = len(cfg["sweep"]["windows"]) * len(cfg["sweep"]["models"])
    units = len(models) + swept + 1
    row, runs = {**market}, {}
    for i, model in enumerate(models):
        runs[model] = backtest.run(
            fixed, bars, cfg, model,
            lambda done, total, i=i, m=model: step(f"{feed} · {m}", (i + done / total) / units))
        table = runs[model]["table"]
        row[f"p_{model}"] = table["mean_r"]["p_value"]
        row[f"edge_r_{model}"] = table["mean_r"]["observed"] - table["mean_r"]["median"]
        if model == headline:
            row.update({k: v for k, v in runs[model].items()
                        if k not in ("table", "shapes", "cone", "model")},
                       p=table["mean_r"]["p_value"], edge_r=row[f"edge_r_{model}"],
                       real_r=table["mean_r"]["observed"], null_r=table["mean_r"]["median"],
                       resolution=1.0 / (1 + cfg["nulls"]["draws"]),
                       net=table["net"]["observed"], p_net=table["net"]["p_value"],
                       dd=table["dd"]["observed"], p_dd=table["dd"]["p_value"],
                       ret_dd=table["ret_dd"]["observed"])
    runs["sweep"] = window_sweep(fixed, bars, cfg, runs, lambda what, share: step(
        f"{feed} · {what}", (len(models) + share * swept) / units))
    step(f"{feed} · coste y ejecución", (units - 1) / units)
    runs["stress"] = stress.simulate(fixed, bars, cfg)
    row.update(tests(fixed, bars, cfg))
    row["drivers"] = drivers.profile(bars, cfg)
    row["fingerprint"] = fingerprint.fingerprint(feed, base, {**fixed, "bars": bars})
    row["warnings"] = inference.warnings(row, cfg)
    return row, runs, correlation.weekly_equity(fixed, bars)


def analyse_strategy(setup: dict, cfg: dict, name: str, only: str | None,
                     step: Callable[[str, float], None]) -> dict:
    """The whole cross-market analysis of one strategy.

    Args:
        setup: What serve.main() assembled: universe, bars per feed, trades folder.
        cfg: What config.load() returned.
        name: Strategy name, the CSV's stem.
        only: One market feed to run on its own, or None for all of them.
        step: Called with (what is running, share done) for the progress bar.

    Returns:
        The record the session holds: the per-market rows, every model's full result, the
        markets this strategy produced no trades on at all, the strategy's summary, its
        correlation and PCA, and the base asset's own row — the reference case, never
        evidence.
    """
    universe = setup["universe"]
    base_trades = tradeio.read(setup["trades"] / universe["main"] / f"{name}.csv")
    base_bars = envelope.window(base_trades, setup["bars"][universe["main"]])
    base = backtest.setting(base_trades, base_bars, cfg)
    curves = {universe["main"]: correlation.weekly_equity(base, base_bars)}

    wanted = [m for m in universe["markets"] if only is None or m["feed"] == only]
    rows, runs, missing = [], {}, []
    for i, market in enumerate(wanted):
        feed = market["feed"]
        trades = setup["trades"] / feed / f"{name}.csv"
        # The export writes a market's file only when that strategy traded there, so a
        # strategy that never fired on one market simply has no file.
        if not trades.exists():
            missing.append(feed)
            continue
        row, got, curve = analyse_market(
            cfg, market, trades, setup["bars"][feed], base,
            lambda what, share, i=i: step(what, (i + share) / len(wanted)))
        rows.append(row)
        runs[feed] = got
        curves[feed] = curve

    per_market = pd.DataFrame(rows)
    return {"rows": per_market.to_dict("records"), "runs": runs, "missing": missing,
            "summary": {"family": inference.family(per_market), "missing": len(missing),
                        **breadth.summary(per_market, cfg["diagnostics"]["alpha"])},
            "base": {"feed": universe["main"], **tests(base, base_bars, cfg),
                     "drivers": drivers.profile(base_bars, cfg), "trades": len(base["held"])},
            "correlation": correlation.correlation_matrix(curves).to_dict(),
            "pca": correlation.pca(correlation.returns_matrix(curves))}
