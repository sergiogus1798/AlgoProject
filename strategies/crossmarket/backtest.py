"""Run one strategy's real trades and its random counterparts on one market, under a given model."""

from collections.abc import Callable

import numpy as np
import pandas as pd

from core import trades as tradeio
from strategies.crossmarket import (envelope, equity, holdfit, metrics, pricing, strata,
                                    trade_models)


def setting(trades: pd.DataFrame, bars: pd.DataFrame, cfg: dict) -> dict:
    """Fix how this market is priced, before anything random is drawn.

    Args:
        trades: One market's real trades.
        bars: That market's bars.
        cfg: What config.load() returned.

    Returns:
        The bar locations of the real trades, the fill convention that reproduced SQX, the
        prices, the sizes and per-trade costs recovered from the export, the real P&L in USD
        and the scale. The convention is re-derived per market rather than assumed: real and
        random runs must be priced identically or the comparison measures the gap between two
        pricers instead of the timing. Computed once per market and passed to every test.
    """
    pricing.require_long_only(trades)
    held = envelope.occupancy(trades, bars)
    aligned = trades.loc[held.index]
    best = pricing.reconcile(aligned, bars, held)[0]
    enter_col, leave_col = pricing.CONVENTIONS[best["convention"]]
    value = pricing.point_value(aligned)
    enter_px, leave_px = bars[enter_col].to_numpy(), bars[leave_col].to_numpy()
    size = aligned["Size"].to_numpy() * value
    gross = (leave_px[held["exit"].to_numpy()] - enter_px[held["entry"].to_numpy()]) * size
    # What SQX charged, recovered per trade rather than assumed: gross reconstructed from
    # the bars minus the P/L it reported. Measured correlation 0.9996 over three markets, so
    # the residual is the cost and the swap and nothing else.
    return {"held": held, "aligned": aligned, "fill": best, "point_value": value,
            "enter_px": enter_px, "leave_px": leave_px, "size": size,
            "cost": pricing.cost_rate(aligned, value), "scale": pricing.unit(bars),
            "pnl": aligned["Profit/Loss"].to_numpy(),
            "charged": gross - aligned["Profit/Loss"].to_numpy(),
            "off_grid": len(trades) - len(held),
            "market": {**envelope.describe(bars, held, cfg["nulls"]["block_months"]),
                       "strata": strata.index(bars, cfg["strata"])}}


def price(entries: np.ndarray, holds: np.ndarray, fixed: dict) -> tuple[np.ndarray, ...]:
    """Price a batch of random runs exactly the way the real one was priced.

    Args:
        entries: A (runs, trades) array of entry bar indices.
        holds: Bars held, same shape.
        fixed: What setting() returned.

    Returns:
        (pnl, logret, closed, live): USD per trade, the log return per trade, the bar each
        trade closed on, and which columns are real trades of that run. Column k reuses real
        trade k's size and charged cost — wrapping round for the renewal model, which has
        more columns than there are real trades — so the random runs carry the same position
        sizes and the same costs as the run they are compared against.
    """
    leave_px, enter_px = fixed["leave_px"], fixed["enter_px"]
    out = entries + holds
    live = (out < leave_px.size) & (holds > 0)
    safe = np.where(live, out, 0)
    at = np.arange(entries.shape[1]) % fixed["size"].size
    move = np.where(live, leave_px[safe] - enter_px[entries], 0.0)
    pnl = move * fixed["size"][at] - np.where(live, fixed["charged"][at], 0.0)
    logret = np.where(live, np.log(leave_px[safe] / enter_px[entries]) - fixed["cost"], 0.0)
    return pnl, logret, safe, live


def null(fixed: dict, cfg: dict, model: str,
         on_chunk: Callable[[int, int], None] = lambda done, total: None) -> dict:
    """Every statistic and every equity curve of `draws` random runs, in batches.

    Args:
        fixed: What setting() returned.
        cfg: What config.load() returned.
        model: A key of trade_models.MODELS.
        on_chunk: Called with (runs done, runs total) after each batch, for the progress bar.

    Returns:
        Keys stats (one array per statistic across the runs), curves (one equity path per
        run) and entries (the first batch's entry indices, for the calendar diagnostic).
        Drawn and priced in batches because one 5,000 x 2,000 matrix plus the four numpy
        intermediates the statistics need is well over a gigabyte.
    """
    n, e = cfg["nulls"], cfg["equity"]
    rng = np.random.default_rng(n["seed"])
    stats, curves, first = [], [], None
    for done in range(0, n["draws"], n["chunk"]):
        size = min(n["chunk"], n["draws"] - done)
        entries, holds = trade_models.MODELS[model](fixed["held"], fixed["market"], size, rng)
        if n["replicate_friday"]:
            holds = trade_models.truncate(entries, holds, fixed["market"])
        pnl, logret, closed, live = price(entries, holds, fixed)
        batch = metrics.paths(pnl, live, e["starting"])
        batch["mean_r"] = (logret.sum(axis=1)
                           / np.maximum(live.sum(axis=1), 1) / fixed["scale"])
        stats.append(batch)
        curves.append(equity.path(pnl, closed, fixed["market"]["n_bars"], e["steps"],
                                  e["starting"]))
        first = entries if first is None else first
        on_chunk(done + size, n["draws"])
    return {"stats": {k: np.concatenate([b[k] for b in stats]) for k in stats[0]},
            "curves": np.concatenate(curves), "entries": first}


def swept(fixed: dict, cfg: dict,
          draw: Callable[[int, np.random.Generator], tuple[np.ndarray, np.ndarray]],
          on_chunk: Callable[[int, int], None] = lambda done, total: None) -> dict:
    """mean_r and trade count of `draws` random runs drawn by any function, priced like null().

    Args:
        fixed: What setting() returned.
        cfg: What config.load() returned.
        draw: Called with (runs, rng), returns (entries, holds); the window sweep passes a
            model confined to calendar blocks.
        on_chunk: Called with (runs done, runs total) after each batch.

    Returns:
        Keys mean_r and trades, one value per run; trades counts the ones still live after
        the draw and the Friday cut. Same seed, same batches, same truncation and same pricer
        as null(), so a draw that reproduces a model reproduces its p exactly. Only what the
        sweep reads is computed: the equity curves are most of null()'s time.
    """
    n = cfg["nulls"]
    rng = np.random.default_rng(n["seed"])
    out, counts = [], []
    for done in range(0, n["draws"], n["chunk"]):
        size = min(n["chunk"], n["draws"] - done)
        entries, holds = draw(size, rng)
        if n["replicate_friday"]:
            holds = trade_models.truncate(entries, holds, fixed["market"])
        _, logret, _, live = price(entries, holds, fixed)
        out.append(logret.sum(axis=1) / np.maximum(live.sum(axis=1), 1) / fixed["scale"])
        counts.append(live.sum(axis=1))
        on_chunk(done + size, n["draws"])
    return {"mean_r": np.concatenate(out), "trades": np.concatenate(counts)}


def real(fixed: dict, bars: pd.DataFrame, cfg: dict) -> dict:
    """The real backtest's own statistics and equity curve.

    Args:
        fixed: What setting() returned.
        bars: That market's bars.
        cfg: What config.load() returned.

    Returns:
        Keys stats and curve. `net` here is SQX's own reported profit summed, not a
        reconstruction, so the number on the page is the number in the databank.
    """
    e = cfg["equity"]
    pnl = fixed["pnl"]
    stats = metrics.observed(pnl, e["starting"])
    logret = pricing.realised(bars, fixed["held"], fixed["fill"]["convention"]) - fixed["cost"]
    stats["mean_r"] = float(logret.mean() / fixed["scale"])
    curve = equity.path(pnl[None, :], fixed["held"]["exit"].to_numpy()[None, :],
                        fixed["market"]["n_bars"], e["steps"], e["starting"])
    return {"stats": stats, "curve": curve[0].tolist()}


def diagnostics(fixed: dict, bars: pd.DataFrame, entries: np.ndarray) -> dict:
    """The checks that decide whether a market's result may be believed at all.

    Args:
        fixed: What setting() returned.
        bars: That market's bars.
        entries: One batch of the random runs' entry indices.

    Returns:
        Trade count, how many trades fell off the bar grid, fill error, share of entries on a
        bar open, share of exits at the bar cap and at the Friday close, median hold, cost,
        how much of the real entries' calendar the random runs kept, and the volatility at
        the real entries against the market's own average.
    """
    held, aligned = fixed["held"], fixed["aligned"]
    clock = bars.index.dayofweek.to_numpy() * 24 + bars.index.hour.to_numpy()
    entry_atr = pricing.atr(bars)[held["entry"].to_numpy()]
    kept = (float("nan") if entries.shape[1] != len(held)
            else float(np.mean(clock[entries] == clock[held["entry"].to_numpy()])))
    return {"trades": len(held), "off_grid": fixed["off_grid"],
            "convention": fixed["fill"]["convention"],
            "fill_error": fixed["fill"]["entry_median"] + fixed["fill"]["exit_median"],
            "on_bar_open": tradeio.on_bar_open(aligned, bars.index),
            "bar_cap": float((aligned["Close type"] == "Exit After X Bars").mean()),
            "friday_exit": float((aligned["Close type"] == "End Of Friday (Time)").mean()),
            "hold_median": float(held["hold"].median()),
            "cost_rate": fixed["cost"], "point_value": fixed["point_value"],
            "calendar_kept": kept,
            "atr_ratio": float(np.nanmean(entry_atr) / np.nanmean(pricing.atr(bars)))}


def run(fixed: dict, bars: pd.DataFrame, cfg: dict, model: str,
        on_chunk: Callable[[int, int], None] = lambda done, total: None) -> dict:
    """The real run and its random counterparts on one market, all priced identically.

    Args:
        fixed: What setting() returned for this market.
        bars: That market's bars.
        cfg: What config.load() returned.
        model: A key of trade_models.MODELS, which decides what is randomised.
        on_chunk: Progress callback, passed through to null().

    Returns:
        The metric table, a drawable histogram per metric, the equity cone with the real
        curve on it, and the diagnostics. No verdict and no ranking: judging these numbers
        is inference's job, and keeping the two apart is what lets the same runs be
        re-judged, or the same judgement re-run under another model.
    """
    e = cfg["equity"]
    drawn = null(fixed, cfg, model, on_chunk)
    seen = real(fixed, bars, cfg)
    return {"model": model,
            "table": metrics.table(drawn["stats"], seen["stats"], e["percentiles"]),
            "shapes": metrics.shapes(drawn["stats"], seen["stats"]),
            "cone": {"bands": equity.bands(drawn["curves"], e["bands"]),
                     "observed": seen["curve"], "dates": equity.dates(bars, e["steps"])},
            **diagnostics(fixed, bars, drawn["entries"]),
            **holdfit.goodness(fixed["held"], fixed["market"]["gaps"])}
