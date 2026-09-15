"""Breadth and consistency across a strategy's markets — replaces the single median. Reads
one strategy's per-market rows; no market is ever excluded, so a row that collected warnings
still counts here and the warnings are what say how much to trust it."""

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
    return {"market": worst["feed"], "pf": float(worst["pf"])}


def dispersion(rows: pd.DataFrame) -> float:
    """Coefficient of variation of profit factor across a strategy's markets.

    Args:
        rows: One strategy's testable per-market rows, carrying `pf`.

    Returns:
        std / mean of pf, or NaN on a single market — the spread of one number is not zero,
        it is undefined, and 2 of the 30 sampled strategies never traded on silver at all.
        Low means consistent behaviour across markets; high means one or two lucky markets
        are carrying the result.
    """
    pf = rows["pf"].to_numpy()
    return float(pf.std(ddof=1) / pf.mean()) if len(pf) > 1 else float("nan")


def summary(rows: pd.DataFrame, alpha: float) -> dict:
    """One strategy across its markets, as numbers rather than as a verdict.

    Args:
        rows: One strategy's per-market rows.
        alpha: The level p-values are counted against; it decides nothing, it only counts.

    Returns:
        Breadth, the worst market's profit factor, the dispersion of PF, how many markets
        came in under alpha on the verdict model and on the paired test, the median effect,
        and how many warnings the strategy collected across its markets. The owner reads
        these together; nothing here combines them into one number.
    """
    return {**breadth(rows), "worst_market": worst_market_floor(rows),
            "pf_cv": dispersion(rows),
            "under_alpha": int((rows["p"] <= alpha).sum()),
            "paired_under_alpha": int((rows["paired_p"] <= alpha).sum()),
            "edge_r": float(rows["edge_r"].median()),
            "warnings": int(rows["warnings"].map(len).sum())}
