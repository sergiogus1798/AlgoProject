"""Breadth and consistency across a strategy's markets — replaces the single median. Each
function reads one strategy's testable per-market rows, called from a `groupby("strategy")`
the same way inference.table() calls family() and call()."""

import pandas as pd


def breadth(rows: pd.DataFrame) -> dict:
    """Fraction of markets whose expectancy confidence interval clears zero.

    Args:
        rows: One strategy's testable per-market rows, carrying `expectancy_ci_lo`.

    Returns:
        Keys markets, cleared and fraction.
    """
    cleared = int((rows["expectancy_ci_lo"] > 0).sum())
    return {"markets": len(rows), "cleared": cleared, "fraction": cleared / len(rows)}


def worst_market_floor(rows: pd.DataFrame) -> dict:
    """The weakest market's profit factor.

    Args:
        rows: One strategy's testable per-market rows, carrying `pf`.

    Returns:
        Keys market and pf, for whichever market has the lowest profit factor.
    """
    worst = rows.loc[rows["pf"].idxmin()]
    return {"market": worst["market"], "pf": float(worst["pf"])}


def dispersion(rows: pd.DataFrame) -> float:
    """Coefficient of variation of profit factor across a strategy's markets.

    Args:
        rows: One strategy's testable per-market rows, carrying `pf`.

    Returns:
        std / mean of pf. Low means consistent behaviour across markets; high means one or
        two lucky markets are carrying the result.
    """
    pf = rows["pf"].to_numpy()
    return float(pf.std(ddof=1) / pf.mean())


def summary(rows: pd.DataFrame) -> dict:
    """Breadth, worst-market floor and dispersion together, for one strategy.

    Args:
        rows: One strategy's testable per-market rows.

    Returns:
        The three merged into one dict; no verdict is decided here, only numbers for the
        panel to show beside `inference.call()`'s own.
    """
    return {**breadth(rows), "worst_market": worst_market_floor(rows), "pf_cv": dispersion(rows)}
