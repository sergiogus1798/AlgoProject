"""Per-strategy decay: how much of the in-sample edge survives, and whether what is left is real."""

import numpy as np
import pandas as pd

YEAR = 252
MIN_YEARS_POSITIVE = 4      # of the OOS years; 3 of 5 is what a coin flip gives
MAX_CONCENTRATION = 0.40    # share of OOS profit allowed to come from one quarter
# NOT a one-sided 5 % test: the curve this t is read on is SQX's daily curve, each day's LOWEST
# equity, whose low-to-low differences are 14-25 % more volatile than daily P&L — 🔬 the t reads
# 0.78-0.88 of its close-to-close value on three populations (knowhow/research/gate-t-scales.md).
# The threshold stays (decision E1, 2026-10-04); the statistic to judge an edge with is the
# gate's `drift_excess_t` (studies/screening/gate/measures.py), computed from trades.
SIGNIFICANT_T = 1.65


def sharpe(returns: pd.Series) -> float:
    """Annualised Sharpe of a daily P&L series, with no risk-free adjustment.

    Args:
        returns: Daily change in cumulative P&L.

    Returns:
        Mean over standard deviation, scaled by sqrt(252), SQX's own convention.
    """
    return returns.mean() / returns.std(ddof=1) * np.sqrt(YEAR)


def diagnose(curve: pd.Series, split: str, end: str) -> dict:
    """Everything the verdict needs about one strategy, from its daily equity.

    Args:
        curve: Daily cumulative P&L, indexed by date.
        split: First day of the out-of-sample stretch, YYYY-MM-DD.
        end: Last day to consider, YYYY-MM-DD.

    Returns:
        Sharpe either side, what fraction of it survived, the significance of the
        out-of-sample Sharpe, how many of its years were profitable, and how much of its
        profit came from its single best quarter. Concentration above 1.0 means the
        strategy loses money outside that quarter. Retention is NaN when the in-sample
        Sharpe is not positive, concentration when the out-of-sample total is not.
    """
    daily = curve.diff().dropna()
    before, after = daily[daily.index < split], daily[split:end]
    quarters = after.groupby([after.index.year, after.index.quarter]).sum()
    years = after.groupby(after.index.year).sum()
    edge = sharpe(after)
    total = after.sum()

    # Lo (2002), iid: SE of a per-day Sharpe over T days is sqrt((1 + SR_day**2 / 2) / T);
    # annualised, the squared term is the annual Sharpe's over the days in a year.
    error = np.sqrt((1 + 0.5 * edge ** 2 / YEAR) / (len(after) / YEAR))
    base = sharpe(before)   # a ratio on a losing denominator flips sign: undefined, not a survival
    return {"sharpe_is": base, "sharpe_oos": edge,
            "retention": edge / base if base > 0 else np.nan, "t": edge / error,
            "years_positive": int((years > 0).sum()), "years": len(years),
            "worst_year": years.min(), "concentration": quarters.max() / total if total > 0 else np.nan,
            "net_profit_oos": total}


def verdict(row: dict) -> str:
    """Keep, doubt or discard one strategy.

    Args:
        row: One diagnose() result.

    Returns:
        "DESCARTAR" when the out-of-sample stretch shows no edge, fails in most of its
        years, or owes its profit to a single quarter; "MANTENER" when the surviving
        edge is significant, consistent across years and not concentrated; "DUDOSA"
        for everything between, which is where most strategies land.
    """
    if row["sharpe_oos"] <= 0 or row["years_positive"] <= row["years"] // 2 \
            or row["concentration"] > 0.60:
        return "DESCARTAR"
    if row["t"] >= SIGNIFICANT_T and row["years_positive"] >= MIN_YEARS_POSITIVE \
            and row["concentration"] <= MAX_CONCENTRATION:
        return "MANTENER"
    return "DUDOSA"


def table(curves: dict, split: str, end: str) -> pd.DataFrame:
    """Diagnose and judge a whole databank, one row per strategy.

    Args:
        curves: {strategy name: daily equity series}.
        split: First out-of-sample day, YYYY-MM-DD.
        end: Last day to consider, YYYY-MM-DD.

    Returns:
        One row per strategy, sorted by t descending, with a "verdict" column. Rows are
        never aggregated: strategies from different templates do not pool.
    """
    rows = [dict(name=name, **diagnose(curve, split, end)) for name, curve in curves.items()]
    for row in rows:
        row["verdict"] = verdict(row)
    return pd.DataFrame(rows).sort_values("t", ascending=False).reset_index(drop=True)
