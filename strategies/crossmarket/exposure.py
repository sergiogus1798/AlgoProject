"""Test 1c — exposure-adjusted return: is the edge concentrated in better-than-average bars?"""

import numpy as np
import pandas as pd

from core import trades as tradeio
from strategies.crossmarket import backtest, bootstrap, pricing

BLOCK = 5   # trades per bootstrap block; configurable per PDF §4, overridable by the panel


def occupied_bars(held: pd.DataFrame) -> np.ndarray:
    """Every bar index a trade was open on.

    Args:
        held: What envelope.occupancy() returned.

    Returns:
        Bar indices, one entry per occupied bar, one trade's range at a time. Trades never
        overlap, so no index appears twice.
    """
    return np.concatenate([np.arange(e, x) for e, x in zip(held["entry"], held["exit"])])


def per_trade_exposure(held: pd.DataFrame, bar_returns: np.ndarray) -> np.ndarray:
    """The mean bar return during each trade, one scalar per trade.

    Args:
        held: What envelope.occupancy() returned.
        bar_returns: Log return of every bar in the market.

    Returns:
        One value per trade — the unit the bootstrap resamples.
    """
    return np.array([np.nanmean(bar_returns[e:x]) for e, x in zip(held["entry"], held["exit"])])


def concentration(fixed: dict, bars: pd.DataFrame) -> dict:
    """Concentration ratio E and drift-neutral excess A.

    Args:
        fixed: What backtest.setting() returned.
        bars: That market's bars.

    Returns:
        Keys e, a and mu_m. Both are computed on the pooled occupied bars, not the mean of
        per-trade means, matching the PDF §4 definition literally.
    """
    bar_returns = np.log(bars["Close"]).diff().to_numpy()
    mu_m = float(np.nanmean(bar_returns))
    held_mean = float(np.nanmean(bar_returns[occupied_bars(fixed["held"])]))
    return {"e": held_mean / mu_m, "a": held_mean - mu_m, "mu_m": mu_m}


def risk_normalised(a: float, bars: pd.DataFrame) -> float:
    """A expressed per unit of the market's own typical bar move.

    Args:
        a: Drift-neutral excess-per-bar, from concentration().
        bars: That market's bars.

    Returns:
        A / pricing.unit(bars) — a conditional Sharpe of the exposure the strategy chose.
    """
    return a / pricing.unit(bars)


def capture_ratio(trades: pd.DataFrame, point_value: float) -> pd.Series:
    """Fraction of the favourable excursion each trade converted into realised move.

    Args:
        trades: One market's trades, already restricted to the rows envelope kept.
        point_value: What pricing.point_value() measured for this market.

    Returns:
        One ratio per trade: (close - open) / mfe, in price. Long-only, so no sign flip.
    """
    move = trades["Close price"] - trades["Open price"]
    mfe = tradeio.excursions(trades, point_value)["mfe"]
    return move / mfe


def bootstrap_a(per_trade: np.ndarray, mu_m: float, draws: int, rng: np.random.Generator,
                block: int = BLOCK) -> dict:
    """Confidence interval on A by block-bootstrap over trades.

    Args:
        per_trade: What per_trade_exposure() returned.
        mu_m: The market's mean bar return.
        draws: Bootstrap draws.
        rng: Seeded generator.
        block: Trades per block.

    Returns:
        What bootstrap.percentile_ci() returned, on A = mean(sample) - mu_m per draw.
    """
    picks = bootstrap.block_bootstrap(draws, len(per_trade), rng, block)
    return bootstrap.percentile_ci(per_trade[picks].mean(axis=1) - mu_m)


def run(trades: pd.DataFrame, bars: pd.DataFrame, draws: int, block: int = BLOCK) -> dict:
    """Test 1c for one strategy on one market.

    Args:
        trades: One market's real trades.
        bars: That market's bars.
        draws: Bootstrap draws for the confidence interval on A.
        block: Trades per bootstrap block.

    Returns:
        Concentration (e, a, mu_m), risk-normalised A, its bootstrap CI, and the capture
        ratio's mean and median. Entry point for the panel: everything else here is a step.
    """
    fixed = backtest.setting(trades, bars)
    conc = concentration(fixed, bars)
    bar_returns = np.log(bars["Close"]).diff().to_numpy()
    per_trade = per_trade_exposure(fixed["held"], bar_returns)
    rng = np.random.default_rng(backtest.SEED)
    ci = bootstrap_a(per_trade, conc["mu_m"], draws, rng, block)
    capture = capture_ratio(fixed["aligned"], fixed["point_value"])
    return {**conc, "risk_normalised": risk_normalised(conc["a"], bars), "a_ci": ci,
            "capture_mean": float(capture.mean()), "capture_median": float(capture.median())}
