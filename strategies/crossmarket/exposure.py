"""Test 1c — exposure-adjusted return: is the edge concentrated in better-than-average bars?"""

import numpy as np
import pandas as pd

from core import trades as tradeio
from strategies.crossmarket import bootstrap, pricing


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


def drift(bars: pd.DataFrame) -> dict:
    """The market's own mean bar return, with the t-statistic that says whether it is a drift.

    Args:
        bars: One market's bars.

    Returns:
        Keys mu_m, t and bars. E divides by mu_m, so a market whose drift is statistically
        indistinguishable from zero has no meaningful E at all — and a market that drifted
        down has a negative one, which reads as the opposite of what it is.
    """
    returns = np.log(bars["Close"]).diff().to_numpy()
    mu = float(np.nanmean(returns))
    n = int(np.sum(~np.isnan(returns)))
    return {"mu_m": mu, "t": mu / float(np.nanstd(returns, ddof=1)) * np.sqrt(n), "bars": n}


def concentration(held: pd.DataFrame, bars: pd.DataFrame, mu_min_t: float) -> dict:
    """Concentration ratio E and drift-neutral excess A.

    Args:
        held: What envelope.occupancy() returned.
        bars: That market's bars.
        mu_min_t: |t| of the market's own drift below which E is withheld.

    Returns:
        Keys e, a, mu_m, mu_t and e_meaningful. A is the pooled mean over the occupied bars
        minus the market's mean bar, exactly as the source note defines it. E is that ratio,
        and it is returned as NaN when the denominator is not a drift: measured on Brent,
        mu_m = -1.1e-6 turns a market with the strongest A of the three into E = -69.4.
    """
    bar_returns = np.log(bars["Close"]).diff().to_numpy()
    market = drift(bars)
    held_mean = float(np.nanmean(bar_returns[occupied_bars(held)]))
    meaningful = abs(market["t"]) >= mu_min_t and market["mu_m"] > 0
    return {"e": held_mean / market["mu_m"] if meaningful else float("nan"),
            "a": held_mean - market["mu_m"], "mu_m": market["mu_m"], "mu_t": market["t"],
            "e_meaningful": bool(meaningful), "held_mean": held_mean}


def risk_normalised(a: float, bars: pd.DataFrame) -> float:
    """A expressed per unit of the market's own typical bar move.

    Args:
        a: Drift-neutral excess-per-bar, from concentration().
        bars: That market's bars.

    Returns:
        A / pricing.unit(bars) — a conditional Sharpe of the exposure the strategy chose.
    """
    return a / pricing.unit(bars)


def capture_ratio(trades: pd.DataFrame, point_value: float, drop_zero: bool) -> dict:
    """Fraction of the favourable excursion each trade converted into realised move.

    Args:
        trades: One market's trades, already restricted to the rows envelope kept.
        point_value: What pricing.point_value() measured for this market.
        drop_zero: Exclude trades whose MFE is zero rather than letting them divide by it.

    Returns:
        Keys mean, median and dropped. A trade that never moved favourably has an undefined
        capture ratio, not an infinite one: 7 of 844 silver trades are such, and keeping them
        makes the mean +/-inf while the median silently ignores the problem.
    """
    mfe = tradeio.excursions(trades, point_value)["mfe"]
    keep = mfe > 0 if drop_zero else np.ones(len(mfe), dtype=bool)
    ratio = ((trades["Close price"] - trades["Open price"])[keep] / mfe[keep]).to_numpy()
    return {"mean": float(ratio.mean()), "median": float(np.median(ratio)),
            "dropped": int((~keep).sum())}


def bootstrap_a(held: pd.DataFrame, per_trade: np.ndarray, mu_m: float, cfg: dict,
                rng: np.random.Generator) -> dict:
    """Confidence interval on A by block-bootstrap over trades.

    Args:
        held: What envelope.occupancy() returned, for the holds that weight each trade.
        per_trade: What per_trade_exposure() returned.
        mu_m: The market's mean bar return.
        cfg: What config.load() returned.
        rng: Seeded generator.

    Returns:
        What bootstrap.percentile_ci() returned. Each draw is weighted by its trades' holds,
        so the resampled statistic is the same pooled mean the point estimate uses: an
        unweighted mean of per-trade means is a different estimator, and on gold it sat 9%
        away from the A it was supposed to bracket.
    """
    b = cfg["bootstrap"]
    weight = held["hold"].to_numpy().astype(float)
    picks = bootstrap.block_bootstrap(b["draws"], len(per_trade), rng, b["block"])
    pooled = ((per_trade[picks] * weight[picks]).sum(axis=1) / weight[picks].sum(axis=1))
    return bootstrap.percentile_ci(pooled - mu_m, *b["ci"])


def run(fixed: dict, bars: pd.DataFrame, cfg: dict, rng: np.random.Generator) -> dict:
    """Test 1c for one strategy on one market.

    Args:
        fixed: What backtest.setting() returned — the trades already located on the bar grid.
        bars: That market's bars.
        cfg: What config.load() returned.
        rng: Seeded generator.

    Returns:
        Concentration (e, a, mu_m, mu_t, e_meaningful), risk-normalised A, its bootstrap CI,
        and the capture ratio. Takes `fixed` rather than raw trades so the fill convention is
        reconciled once per market instead of once per test.
    """
    conc = concentration(fixed["held"], bars, cfg["exposure"]["mu_min_t"])
    bar_returns = np.log(bars["Close"]).diff().to_numpy()
    per_trade = per_trade_exposure(fixed["held"], bar_returns)
    ci = bootstrap_a(fixed["held"], per_trade, conc["mu_m"], cfg, rng)
    capture = capture_ratio(fixed["aligned"], fixed["point_value"],
                            cfg["exposure"]["drop_zero_mfe"])
    return {**conc, "risk_normalised": risk_normalised(conc["a"], bars), "a_ci": ci,
            "capture": capture}
