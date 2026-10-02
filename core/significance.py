"""Could this edge be zero? The Sharpe-based tests three studies now share, and the one Sharpe total."""

import numpy as np
import pandas as pd
from scipy import stats


def moments(returns: np.ndarray) -> tuple[float, float, float]:
    """Sharpe, skew and raw kurtosis of a per-observation series.

    Args:
        returns: One value per trade. Any scale -- USD P/L or log return -- since every
            statistic below is scale-invariant.

    Returns:
        (sharpe, skew, kurtosis). Sharpe is the plain mean over standard deviation with
        ddof=1, unannualised, because that is the unit the two formulas below need.
        Kurtosis is raw, 3 for a normal, not excess: `variance_factor`'s (kurtosis - 1) / 4
        term expects it that way and excess kurtosis silently shifts both answers.
    """
    sharpe = float(returns.mean() / returns.std(ddof=1))
    return sharpe, float(stats.skew(returns)), float(stats.kurtosis(returns, fisher=False))


def variance_factor(sharpe: float, skew: float, kurtosis: float) -> float:
    """How much the shape of the returns inflates the variance of their Sharpe estimate.

    Args:
        sharpe: Per-observation Sharpe.
        skew: Its skew.
        kurtosis: Its raw kurtosis, 3 for a normal.

    Returns:
        The factor both PSR and the minimum track-record length divide by. Negative skew
        and fat tails push it above 1, which is what makes a strategy whose profit sits in
        a few enormous trades score worse than a normal-looking one with the same Sharpe.
    """
    return 1 - skew * sharpe + (kurtosis - 1) / 4 * sharpe ** 2


def footprint(h: np.ndarray, d: np.ndarray, s: np.ndarray, c: np.ndarray, mu: float,
             sigma: float, pv: float) -> float:
    """Sharpe of a same-footprint random trader, under the market's own noise, for
    `psr()`/`min_track_record()`'s `benchmark`. The one implementation three studies share:
    `studies.transfer.crossmarket`, `portfolio.common.monteCarlo` and `studies.breakage.mcRetest`
    each build `h`, `d`, `s`, `c`, `mu`, `sigma` and `pv` their own way -- a market's bars are
    not a trade stream, and a trade stream is not a batch of simulations -- and call this once
    for the arithmetic and the Sharpe both share.

    **Fixed 2026-09-29 (OPEN.md #71):** the version this replaced fed the random trader the
    market's mean move with no noise around it -- its only dispersion came from how long each
    trade happened to hold -- so it scored a per-trade Sharpe near the market's own annualised
    Sharpe (~+2 measured on USDJPY) instead of near zero, and every real strategy failed
    against it (mcRetest's `p_positive` collapsed from 1.0 to 0.0 for every strategy checked,
    `knowhow/research/random-entry-nulls.md`). This version puts the market's own bar-to-bar
    noise back in: per trade i, with hold h_i (bars), direction d_i (+1/-1), size s_i, point
    value pv and cost c_i, against the market's own per-bar mean mu and std sigma over the
    trades' own window,

        mean_i = d_i * mu * h_i * s_i * pv - c_i
        var_i  = sigma**2 * h_i * (s_i * pv)**2

    and the law of total variance -- Var(X) = E[Var(X|i)] + Var(E[X|i]) -- gives the
    population of hypothetical same-footprint trades a combined variance of mean(var_i) (the
    market's own noise, averaged over the holds actually seen) plus var(mean_i) (the
    dispersion the footprints themselves add), rather than treating every hold as if it were
    the same length.

    Args:
        h: Bars held per trade, or one scalar broadcast to all of them.
        d: Direction per trade, +1 long / -1 short, or one scalar.
        s: Size per trade, or one scalar -- 1.0 where the caller's own scale already prices
            size in (crossmarket's log return).
        c: What was actually charged, per trade or one scalar, on the same per-observation
            scale `mean_i` is in.
        mu: The market's own mean move per bar over the trades' own window -- price or log
            return, whichever scale the caller's `psr()` sharpe sits on.
        sigma: That same move's standard deviation over the same window.
        pv: Account currency per 1.0 of price per 1.0 lot, or 1.0 where `mu`/`sigma` are
            already on the caller's per-observation scale.

    Returns:
        SR_b = mean(mean_i) / sqrt(mean(var_i) + var(mean_i, ddof=1)), on whatever
        per-observation scale the caller's own `returns`/`pnl` is on -- log return or USD --
        so it is the same ruler `psr()`'s own `sharpe` sits on, only centred differently.
    """
    h, d, s, c = (np.asarray(h, dtype=np.float64), np.asarray(d, dtype=np.float64),
                 np.asarray(s, dtype=np.float64), np.asarray(c, dtype=np.float64))
    mean_i = d * mu * h * s * pv - c
    var_i = sigma ** 2 * h * (s * pv) ** 2
    return float(np.mean(mean_i) / np.sqrt(np.mean(var_i) + np.var(mean_i, ddof=1)))


def psr(returns: np.ndarray, benchmark: float) -> dict:
    """Probabilistic Sharpe Ratio of a return series.

    Args:
        returns: One value per trade.
        benchmark: Sharpe to beat, per observation. Zero asks whether there is any edge; that
            is not the null a trading strategy is measured against (OPEN.md #71) -- the
            honest one is what a same-footprint random trader would have scored under the
            market's own noise (`footprint()`), computed on the same per-observation scale
            so it sits on the same ruler as `sharpe` below, only centred differently. Zero
            remains a legitimate benchmark to pass explicitly; it is no longer the default
            any caller should reach for without saying why.

    Returns:
        The observed Sharpe, its skew and kurtosis, the observation count, and the
        probability that the true Sharpe exceeds the benchmark. It is a point estimate,
        not a distribution: bootstrapping it would count the same sampling uncertainty
        twice.
    """
    sharpe, skew, kurtosis = moments(returns)
    z = (sharpe - benchmark) * np.sqrt(returns.size - 1) / np.sqrt(
        variance_factor(sharpe, skew, kurtosis))
    return {"sharpe": sharpe, "skew": skew, "kurtosis": kurtosis, "n": returns.size,
            "psr": float(stats.norm.cdf(z))}


def min_track_record(returns: np.ndarray, alpha: float = 0.05, benchmark: float = 0.0) -> dict:
    """Bailey / Lopez de Prado minimum track-record length.

    Args:
        returns: One value per trade.
        alpha: Significance level for the one-sided test that Sharpe > benchmark.
        benchmark: Sharpe to beat, per observation. Zero asks whether there is any edge; the
            honest benchmark for a trading strategy is what a same-footprint random trader
            would have scored under the market's own noise (`footprint()`, OPEN.md #71) --
            the same ruler `psr()` uses, with the same centring.

    Returns:
        How many observations the observed shape would need before Sharpe > benchmark is
        significant, how many there are, and whether that is enough. `needed` is None
        ("no alcanzable") when the observed Sharpe does not exceed the benchmark: no track
        record, however long, makes SR > SR* significant then, and squaring the negative gap
        would print a large finite number that reads as reachable.
    """
    sharpe, skew, kurtosis = moments(returns)
    if sharpe <= benchmark:
        return {"needed": None, "have": len(returns), "enough": False}
    z = stats.norm.isf(alpha)
    needed = 1 + variance_factor(sharpe, skew, kurtosis) * (z / (sharpe - benchmark)) ** 2
    return {"needed": float(needed), "have": len(returns), "enough": bool(len(returns) >= needed)}


def annual_sharpe(pnl: np.ndarray, closed: np.ndarray) -> float:
    """"Sharpe total" (owner's rule): the classic Sharpe of the whole backtest's daily P&L.

    Args:
        pnl: Account currency per trade.
        closed: Each trade's close time, same order as `pnl`.

    Returns:
        Mean over standard deviation (ddof=1) of the P&L of every trading day — Monday to
        Friday, from the first close to the last, days with nothing closed at zero — times
        sqrt(252). A trade closing on a weekend counts on the next Monday. NaN with fewer
        than two days or no variation. Fixed sizing makes daily P&L and daily return on the
        account the same series up to a constant, so the ratio is the same either way.
    """
    day = pd.DatetimeIndex(closed).normalize() + pd.offsets.BDay(0)
    daily = pd.Series(np.asarray(pnl, dtype=np.float64), index=day).groupby(level=0).sum()
    rets = daily.reindex(pd.bdate_range(daily.index.min(), daily.index.max()), fill_value=0.0)
    sd = rets.std(ddof=1) if len(rets) > 1 else 0.0
    return float(rets.mean() / sd * np.sqrt(252)) if sd > 0 else float("nan")
