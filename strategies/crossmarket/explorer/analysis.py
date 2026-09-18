"""One strategy's whole cross-market analysis: every null model and every test, market by market."""

from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

from core import trades as tradeio
from strategies.crossmarket import (backtest, breadth, correlation, curves, envelope,
                                    execution, exposure, fingerprint, inference, metrics,
                                    paired, portfolio, realrun, significance, stress, views)
from strategies.crossmarket.explorer import sweep_run


def tests(fixed: dict, bars: pd.DataFrame, cfg: dict, feed: str) -> dict:
    """Every test besides the random-entry one, on one strategy and one market.

    Args:
        fixed: What backtest.setting() returned for this market.
        bars: That market's bars.
        cfg: What config.load() returned.
        feed: The market's SQX symbol, for its execution assumptions.

    Returns:
        A flat row: the real backtest's own statistics, exposure (Test 1c), the paired test
        (Test 1b) with its sensitivity to the reference window, significance, and cost and
        execution stress. Takes `fixed` so the fill convention is reconciled once per market
        rather than once per test.
    """
    rng = np.random.default_rng(cfg["nulls"]["seed"])
    exp = exposure.run(fixed, bars, cfg, rng)
    stressed = execution.settings(fixed, feed, cfg)
    # What the backtest DID, over every trade SQX reported. realrun.real() stays on the
    # located subset and is what the null comparison uses: the real run and its random
    # counterparts have to be the same trades.
    seen = realrun.reported(fixed, cfg)
    pair = paired.run(fixed, bars, fixed["market"], cfg, rng)
    returns = significance.trade_returns(fixed, bars)
    mtr = significance.min_track_record(returns, cfg["diagnostics"]["alpha"])
    pf_ci = significance.bootstrap_metric(returns, significance.profit_factor, cfg, rng)
    ex_ci = significance.bootstrap_metric(returns, significance.expectancy, cfg, rng)
    s = cfg["stress"]
    return {"e": exp["e"], "a": exp["a"], "mu_m": exp["mu_m"], "mu_t": exp["mu_t"],
            "e_meaningful": exp["e_meaningful"], "risk_normalised": exp["risk_normalised"],
            "a_ci_lo": exp["a_ci"]["lo"], "a_ci_hi": exp["a_ci"]["hi"],
            "e_ci": exp["e_ci"], "paired_sensitivity": pair["sensitivity"],
            "paired_bps": pair["bps"], "paired_pct": pair["pct"], "paired_r": pair["r"],
            "paired_usd": pair["usd"], "paired_usd_total": pair["usd_total"],
            "paired_reference": pair["reference"],
            "paired_mean": pair["mean"], "paired_median": pair["median"], "paired_p": pair["p"],
            "paired_beat": pair["beat_share"], "paired_ci_lo": pair["ci"]["lo"],
            "paired_ci_hi": pair["ci"]["hi"],
            "pf": significance.profit_factor(returns), "pf_ci_lo": pf_ci["lo"],
            "pf_ci_hi": pf_ci["hi"], "expectancy": significance.expectancy(returns),
            "expectancy_ci_lo": ex_ci["lo"], "expectancy_ci_hi": ex_ci["hi"],
            "sharpe": significance.moments(returns)[0],
            "min_track_needed": mtr["needed"], "min_track_enough": mtr["enough"],
            "real": seen, "equalised": curves.equalised(seen, cfg),
            "trades_all": fixed["all"]["trades"], "dropped": fixed["all"]["dropped"],
            "dropped_pnl": fixed["all"]["dropped_pnl"],
            "costs": execution.compare(fixed, feed), "stress_settings": stressed,
            "cost_gradient": stress.cost_gradient(fixed, bars, s["cost_multiples"]
                                                  ).to_dict("records"),
            "breakeven": stress.breakeven_multiple(fixed, bars),
            "bar_shift_decay": stress.bar_shift_stress(fixed, bars, s["bar_shift"]),
            "slippage_decay": {str(f): stress.range_slippage_stress(fixed, bars, f)
                               for f in s["slippage_fractions"]}}


def analyse_market(cfg: dict, market: dict, trades: Path, bars: pd.DataFrame, base: dict,
                   step: Callable[[str, float], None]) -> tuple[dict, dict, dict]:
    """Every test in this build on one strategy's trades on one market.

    Args:
        cfg: What config.load() returned.
        market: One row of markets.universe()'s `markets` — feed, category, data_from.
        trades: That market's trade CSV for this strategy.
        bars: That market's bars.
        base: What backtest.setting() returned for the same strategy on the base asset.
        step: Called with (what is running, share of this market done) for the progress bar.

    Returns:
        (row, runs, extra): the flat per-market row with its warnings attached; one full
        result per null model plus the window sweep and the execution stress; and what the
        strategy-level views need from this market — its weekly equity curve for the
        correlation matrix, its equity in per cent for the overlay, and the priced trades
        themselves for the portfolio account.
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
            r = table["mean_r"]
            row.update({k: v for k, v in runs[model].items()
                        # mean_r_draws is one array per draw and belongs in `runs`; the rows
                        # become a DataFrame, and a 25,000-long cell in it helps nobody.
                        if k not in ("table", "shapes", "cone", "model", "mean_r_draws")},
                       p=r["p_value"], edge_r=row[f"edge_r_{model}"],
                       real_r=r["observed"], null_r=r["median"],
                       # The effect size in units of the null's own width. p saturates at the
                       # resolution on the best markets and the null is wider on a market with
                       # fewer trades, neither of which is edge; z divides both out and is
                       # what makes two markets comparable. It is a companion to p, never a
                       # replacement: it is not converted to a normal-tail p anywhere.
                       z=(r["observed"] - r["mean"]) / (r["std"] or float("nan")),
                       resolution=1.0 / (1 + cfg["nulls"]["draws"]),
                       net=table["net"]["observed"], p_net=table["net"]["p_value"],
                       dd=table["dd"]["observed"], p_dd=table["dd"]["p_value"],
                       ret_dd=table["ret_dd"]["observed"])
    runs["sweep"] = sweep_run.window_sweep(fixed, bars, cfg, runs, lambda what, share: step(
        f"{feed} · {what}", (len(models) + share * swept) / units))
    step(f"{feed} · coste y ejecución", (units - 1) / units)
    row.update(tests(fixed, bars, cfg, feed))
    row["exits"] = realrun.exits(fixed)
    row["reproducible_pnl"] = sum(e["gross_share"] for e in row["exits"] if e["reproducible"])
    runs["stress"] = stress.simulate(fixed, bars, cfg, row["stress_settings"])
    row["fingerprint"] = fingerprint.fingerprint(feed, base, {**fixed, "bars": bars},
                                                 cfg["exposure"]["drop_zero_mfe"])
    row["warnings"] = inference.warnings(row, cfg)
    return row, runs, {"weekly": correlation.weekly_equity(fixed, bars),
                       "curve": curves.series(fixed, cfg),
                       "stream": portfolio.priced(fixed, feed)}


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
        markets this strategy produced no trades on at all, the strategy's summary, every
        market's equity curve, the combined portfolio account, the correlation matrix, and
        the base asset's own row — the reference case, never evidence. The base asset is in
        the portfolio and in the equity overlay because the question there is what the
        combination does, and the combination the owner would trade has gold in it.
    """
    universe = setup["universe"]
    main = universe["main"]
    base_trades = tradeio.read(setup["trades"] / main / f"{name}.csv")
    base_bars = envelope.window(base_trades, setup["bars"][main])
    # The base asset carries its own bars: the fingerprint compares every market's
    # distributions against it, and that needs its ATR as well as its trades.
    base = {**backtest.setting(base_trades, base_bars, cfg), "bars": base_bars}
    weekly = {main: correlation.weekly_equity(base, base_bars)}
    equity = {main: curves.series(base, cfg)}
    streams = {main: portfolio.priced(base, main)}

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
        row, got, extra = analyse_market(
            cfg, market, trades, setup["bars"][feed], base,
            lambda what, share, i=i: step(what, (i + share) / len(wanted)))
        rows.append(row)
        runs[feed] = got
        weekly[feed], equity[feed] = extra["weekly"], extra["curve"]
        streams[feed] = extra["stream"]

    per_market = pd.DataFrame(rows)
    return {"rows": per_market.to_dict("records"), "runs": runs, "missing": missing,
            "summary": {"family": inference.family(per_market), "missing": len(missing),
                        **breadth.summary(per_market, cfg["diagnostics"]["alpha"])},
            "base": {"feed": main, **tests(base, base_bars, cfg, main),
                     "trades": len(base["held"])},
            "equity": equity, "weekly": weekly, "streams": streams,
            **views.build(weekly, streams, runs, cfg)}
