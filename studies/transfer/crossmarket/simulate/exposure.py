"""Test 1c — exposure-adjusted return: were the bars this strategy held better than average?

Measured per **bar**, against the market's own average bar over the whole backtest window —
which is what separates it from Test 1b, measured per trade against the same stretch of
market. A strategy that picks the right year but enters at random inside it scores here and
not there."""

import numpy as np
import pandas as pd

from engines.nulls.placement import bootstrap
from studies.transfer.crossmarket.mechanics import pricing
from studies.transfer.crossmarket.verdict import fieller

Z90 = 1.6448536269514722   # one-sided 95% normal quantile: the 90% interval bootstrap.ci uses


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
        mu_min_t: |t| of the market's own drift below which E is called not meaningful.

    Returns:
        Keys e, a, mu_m, mu_t, held_mean and e_meaningful. A is the pooled mean over the
        occupied bars minus the market's mean bar, exactly as the source note defines it. E
        is that ratio. E is now always computed and always shown with its Fieller interval —
        the flag says whether the denominator is a drift at all, and the interval says what
        that costs: on Brent, mu_m = -1.1e-6 makes E = -69.4 with unbounded limits.
    """
    bar_returns = np.log(bars["Close"]).diff().to_numpy()
    market = drift(bars)
    held_mean = float(np.nanmean(bar_returns[occupied_bars(held)]))
    meaningful = abs(market["t"]) >= mu_min_t and market["mu_m"] > 0
    return {"e": held_mean / market["mu_m"] if market["mu_m"] else float("nan"),
            "a": held_mean - market["mu_m"], "mu_m": market["mu_m"], "mu_t": market["t"],
            "e_meaningful": bool(meaningful), "held_mean": held_mean}


def risk_normalised(a: float, bars: pd.DataFrame) -> float:
    """A expressed per unit of the market's own typical bar move.

    Args:
        a: Drift-neutral excess-per-bar, from concentration().
        bars: That market's bars.

    Returns:
        A / pricing.unit(bars) — a conditional Sharpe of the exposure the strategy chose. It
        divides by the market's typical move, which is always positive and never near zero,
        so unlike E it is defined in every market. This is the number the panel leads with.
    """
    return a / pricing.unit(bars)


def block_sums(bar_returns: np.ndarray, occupied: np.ndarray, size: int) -> dict:
    """Bars reduced to contiguous blocks, so the ratio can be resampled without a copy per bar.

    Args:
        bar_returns: Log return of every bar.
        occupied: Boolean, True where a trade was open.
        size: Bars per block.

    Returns:
        Per block: the sum and count of every bar, and of the occupied ones alone. Resampling
        blocks of these four totals is the same estimator as resampling the bars themselves,
        at a thousandth of the memory — a 120,000-bar market times 2,000 draws is a matrix
        nobody needs to build.
    """
    ok = np.isfinite(bar_returns)
    value, live = np.where(ok, bar_returns, 0.0), ok & occupied
    stacked = np.vstack([value, ok.astype(float), np.where(live, value, 0.0),
                         live.astype(float)])
    edges = np.arange(0, bar_returns.size, size)
    summed = np.add.reduceat(stacked, edges, axis=1)
    return dict(zip(("sum", "n", "sum_occ", "n_occ"), summed))


def resample(totals: dict, draws: int, rng: np.random.Generator) -> tuple[np.ndarray, ...]:
    """Paired bootstrap replicates of the occupied mean and the market mean.

    Args:
        totals: What block_sums() returned.
        draws: Replicates.
        rng: Seeded generator.

    Returns:
        (numerator, denominator), one entry each per replicate, both computed from the **same**
        resampled blocks. That pairing is what carries the dependence: the occupied bars are a
        subset of the market's own, so treating the two as independent understates the
        interval on their ratio.
    """
    blocks = totals["sum"].size
    pick = rng.integers(0, blocks, (draws, blocks))
    summed = {k: v[pick].sum(axis=1) for k, v in totals.items()}
    empty = np.full(draws, np.nan)
    return (np.divide(summed["sum_occ"], summed["n_occ"], out=empty.copy(),
                      where=summed["n_occ"] > 0),
            np.divide(summed["sum"], summed["n"], out=empty.copy(), where=summed["n"] > 0))


def ratio_interval(fixed: dict, bars: pd.DataFrame, cfg: dict,
                   rng: np.random.Generator) -> dict:
    """E with a Fieller interval, and how often the denominator changed sign.

    Args:
        fixed: What backtest.setting() returned.
        bars: That market's bars.
        cfg: What config.load() returned.
        rng: Seeded generator.

    Returns:
        What fieller.interval() returned, plus sign_flip — the share of replicates whose
        market drift came out at or below zero. That share is the diagnostic to read before
        E itself: "in 38% of the resamples the denominator changed sign" says more about how
        much E can be trusted than any threshold on a t-statistic.
    """
    bar_returns = np.log(bars["Close"]).diff().to_numpy()
    occupied = np.zeros(bar_returns.size, dtype=bool)
    occupied[occupied_bars(fixed["held"])] = True
    totals = block_sums(bar_returns, occupied, cfg["exposure"]["bar_block"])
    num, den = resample(totals, cfg["bootstrap"]["draws"], rng)
    ok = np.isfinite(num) & np.isfinite(den)
    out = fieller.interval(**fieller.moments(num[ok], den[ok]), z=Z90)
    return {**out, "sign_flip": float(np.mean(den[ok] <= 0))}


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
        Concentration (e, a, mu_m, mu_t, e_meaningful), risk-normalised A, A's bootstrap CI,
        and E's Fieller interval with its sign-flip share. The MFE capture ratio used to live
        here and moved to fingerprint.py: it measures how much of a favourable excursion the
        **exit** converted, which is behaviour, not exposure.
    """
    conc = concentration(fixed["held"], bars, cfg["exposure"]["mu_min_t"])
    bar_returns = np.log(bars["Close"]).diff().to_numpy()
    per_trade = per_trade_exposure(fixed["held"], bar_returns)
    ci = bootstrap_a(fixed["held"], per_trade, conc["mu_m"], cfg, rng)
    return {**conc, "risk_normalised": risk_normalised(conc["a"], bars), "a_ci": ci,
            "e_ci": ratio_interval(fixed, bars, cfg, rng)}
