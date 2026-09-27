"""Run one strategy's real trades and its random counterparts on one market, under a given model."""

from collections.abc import Callable

import numpy as np
import pandas as pd

from core import trades as tradeio
from engines.nulls.placement import holdfit, kernel, trade_models
from studies.transfer.crossmarket.mechanics import envelope, equity, pricing, strata
from studies.transfer.crossmarket.simulate import metrics, realrun


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

        `all` carries **every trade SQX reported**, priced by SQX itself and independent of
        the bar grid, because `held` does not: a trade that opens and closes inside one bar
        has no interval to occupy and is dropped from every test that needs one. Measured
        across this databank that is 1.84% of 92,329 trades, up to 9.8% on one pair, almost
        all of them zero-duration `Exit Signal` exits. They are real trades with real P&L, so
        what the backtest **did** is reported from `all`, and what the tests could compare is
        reported from `held`, with both counts on the page.
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
    charged = gross - aligned["Profit/Loss"].to_numpy()
    # What SQX charged, recovered per trade rather than assumed: gross reconstructed from
    # the bars minus the P/L it reported. Measured correlation 0.9996 over three markets, so
    # the residual is the cost and the swap and nothing else.
    order = np.argsort(trades["Close time"].to_numpy(), kind="stable")
    profile = pricing.fill_profile(aligned, bars, held, best["convention"],
                                   cfg["diagnostics"]["fill_tolerance"])
    return {"held": held, "aligned": aligned, "fill": best, "profile": profile,
            "point_value": value,
            "all": {"pnl": trades["Profit/Loss"].to_numpy()[order],
                    "close": trades["Close time"].to_numpy()[order],
                    "open": trades["Open time"].to_numpy()[order],
                    "trades": len(trades), "dropped": len(trades) - len(held),
                    "dropped_pnl": float(trades["Profit/Loss"].sum()
                                         - aligned["Profit/Loss"].sum())},
            "enter_px": enter_px, "leave_px": leave_px, "size": size,
            "cost": pricing.cost_rate(charged, size, aligned["Open price"]),
            "scale": pricing.unit(bars), "pnl": aligned["Profit/Loss"].to_numpy(),
            "charged": charged,
            "off_grid": len(trades) - len(held),
            "market": {**envelope.describe(bars, held, cfg["nulls"]["block_months"]),
                       "strata": strata.index(bars, cfg["strata"]),
                       # block_shift draws one displacement per calendar semester from this
                       # seed, so the same semester moves the same way in every market.
                       "seed": cfg["nulls"]["seed"]}}


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


def drawn(fixed: dict, cfg: dict,
          draw: Callable[[int, np.random.Generator, int], tuple[np.ndarray, np.ndarray]],
          on_chunk: Callable[[int, int], None] = lambda done, total: None) -> dict:
    """Every statistic and every equity curve of `draws` random runs, in batches.

    Args:
        fixed: What setting() returned.
        cfg: What config.load() returned.
        draw: Called with (runs, rng, runs already produced), returns (entries, holds) — a
            null model, or the window sweep's model confined to calendar blocks. The third
            argument exists for `block_shift`, whose randomness is keyed by the calendar so
            that it matches across markets and therefore cannot come from `rng`: without it
            every chunk would redraw the same displacements.
        on_chunk: Called with (runs done, runs total) after each batch, for the progress bar.

    Returns:
        Keys stats (one array per statistic across the runs), curves (one equity path per
        run) and entries (the first batch's entry indices, for the calendar diagnostic).
        Drawn in batches because the entries and holds of 5,000 x 2,000 are still large;
        pricing, statistics and curves run in `kernel.batch`, which keeps no (runs, trades)
        intermediate at all. `price()`, `metrics.paths` and `equity.path` remain as the
        readable definition it is checked against.
    """
    n, e = cfg["nulls"], cfg["equity"]
    rng = np.random.default_rng(n["seed"])
    stats, curves, first = [], [], None
    for done in range(0, n["draws"], n["chunk"]):
        size = min(n["chunk"], n["draws"] - done)
        entries, holds = draw(size, rng, done)
        if n["replicate_friday"]:
            holds = trade_models.truncate(entries, holds, fixed["market"])
        batch, curve = np.empty((size, len(metrics.NAMES))), np.zeros((size, e["steps"]))
        kernel.batch(entries, holds, fixed["leave_px"], fixed["enter_px"], fixed["size"],
                     fixed["charged"], fixed["cost"], fixed["scale"], e["starting"],
                     fixed["market"]["n_bars"], batch, curve)
        stats.append(batch)
        curves.append(curve)
        first = entries if first is None else first
        on_chunk(done + size, n["draws"])
    stats = np.concatenate(stats)
    return {"stats": {k: stats[:, i] for i, k in enumerate(metrics.NAMES)},
            "curves": np.concatenate(curves), "entries": first}


def null(fixed: dict, cfg: dict, model: str,
         on_chunk: Callable[[int, int], None] = lambda done, total: None) -> dict:
    """One null model's random runs: drawn(), with that model doing the drawing.

    Args:
        fixed: What setting() returned.
        cfg: What config.load() returned.
        model: A key of trade_models.MODELS.
        on_chunk: Called with (runs done, runs total) after each batch.

    Returns:
        What drawn() returns. The window sweep calls drawn() directly with the same model
        confined to blocks, so both sides of the sweep are priced by one code path — the
        full-window point of the sweep and the model's own run are then the same draws, which
        is the property tests/test_sweep.py pins down.
    """
    return drawn(fixed, cfg,
                 lambda size, rng, done: trade_models.MODELS[model](
                     fixed["held"], fixed["market"], size, rng, done),
                 on_chunk)


def summary(fixed: dict, bars: pd.DataFrame, cfg: dict, draws: dict) -> dict:
    """What the panel shows for one set of random runs, real backtest included.

    Args:
        fixed: What setting() returned for this market.
        bars: That market's bars.
        cfg: What config.load() returned.
        draws: What drawn() returned.

    Returns:
        The metric table, a drawable histogram per metric, and the equity cone with the real
        curve on it. The raw draws are hundreds of megabytes and are dropped here: everything
        the panel can ask for later has to be in what this returns.
    """
    e = cfg["equity"]
    seen = realrun.real(fixed, bars, cfg)
    return {"table": metrics.table(draws["stats"], seen["stats"], e["percentiles"]),
            "shapes": metrics.shapes(draws["stats"], seen["stats"]),
            "cone": {"bands": equity.bands(draws["curves"], e["bands"]),
                     "observed": seen["curve"], "dates": equity.dates(bars, e["steps"])}}


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
    draws = null(fixed, cfg, model, on_chunk)
    return {"model": model, **summary(fixed, bars, cfg, draws),
            # Kept per draw, and only for the statistic that compares across markets: the
            # joint null in joint.py pools draw d of every market at once and cannot be
            # rebuilt from summaries. 25,000 floats per model and market, against the
            # hundreds of megabytes of raw P&L that summary() drops.
            "mean_r_draws": draws["stats"]["mean_r"],
            **realrun.diagnostics(fixed, bars, draws["entries"]),
            **holdfit.goodness(fixed["held"], fixed["market"]["gaps"])}
