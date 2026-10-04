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


def median_pf(rows: pd.DataFrame) -> float:
    """The median profit factor across a strategy's markets, beside its worst one.

    Args:
        rows: One strategy's testable per-market rows, carrying `pf`.

    Returns:
        The median of `pf`; a single market's own value on one market.
    """
    return float(rows["pf"].median())


def dispersion(rows: pd.DataFrame) -> float:
    """Standard deviation of profit factor across a strategy's markets (📓 2026-09-30, owner:
    was the coefficient of variation — «CV del PF» — shown and read as a plain spread; the UI
    now reads it «STD del PF»).

    Args:
        rows: One strategy's testable per-market rows, carrying `pf`.

    Returns:
        std of pf, or NaN on a single market — the spread of one number is not zero, it is
        undefined, and 2 of the 30 sampled strategies never traded on silver at all. Low
        means consistent behaviour across markets; high means one or two lucky markets are
        carrying the result.
    """
    pf = rows["pf"].to_numpy()
    return float(pf.std(ddof=1)) if len(pf) > 1 else float("nan")


def counts(rows: pd.DataFrame) -> dict:
    """What the markets add up to, with no level applied: the numbers a rule outside can test.

    Args:
        rows: One strategy's per-market rows, carrying `trades`, `net`, `p`, `z`,
            `a_ci_lo` and `expectancy`.

    Returns:
        `trades_total` and `trades_min` (the thinnest market), `net_total` (account currency,
        every market summed, over the trades the bar grid located) and `net_positive`
        (markets that made money), `p_median`, `p_min` and `z_median` of the headline null,
        `a_cleared` (markets whose drift-neutral excess interval clears zero) and
        `expectancy_positive`.
    """
    return {"trades_total": int(rows["trades"].sum()), "trades_min": int(rows["trades"].min()),
            "net_total": float(rows["net"].sum()),
            "net_positive": int((rows["net"] > 0).sum()),
            "p_median": float(rows["p"].median()), "p_min": float(rows["p"].min()),
            "z_median": float(rows["z"].median()),
            "a_cleared": int((rows["a_ci_lo"] > 0).sum()),
            "expectancy_positive": int((rows["expectancy"] > 0).sum())}


def summary(rows: pd.DataFrame, alpha: float) -> dict:
    """One strategy across its markets, as numbers rather than as a verdict.

    Args:
        rows: One strategy's per-market rows.
        alpha: The level p-values are counted against; it decides nothing, it only counts.

    Returns:
        Breadth, the worst market's profit factor, the dispersion of PF, how many markets
        came in under alpha on the verdict model and on the paired test, the median effect,
        how many warnings the strategy collected across its markets, and `counts()`. The
        owner reads these together; nothing here combines them into one number.
    """
    return {**breadth(rows), "worst_market": worst_market_floor(rows),
            "median_pf": median_pf(rows), "pf_cv": dispersion(rows),
            "under_alpha": int((rows["p"] <= alpha).sum()),
            "paired_under_alpha": int((rows["paired_p"] <= alpha).sum()),
            "edge_r": float(rows["edge_r"].median()),
            "warnings": int(rows["warnings"].map(len).sum()), **counts(rows)}


def judge(summary: dict, floor: float) -> tuple[str, str]:
    """Whether a strategy's edge showed up on the markets it never saw.

    Args:
        summary: What summary() returned for one strategy.
        floor: verdict.breadth_floor, the share of markets whose expectancy interval must
            clear zero.

    Returns:
        (verdict, reason). DESCARTAR is what `/curate` acts on; MANTENER is kept.

    One screen and one number, deliberately: breadth is the only reading of this study that
    does not need a model to be believed — an expectancy interval clearing zero on a market
    the strategy was never fitted to is arithmetic. The p-values are reported beside it and
    decide nothing, because they come from a placement model and the owner reads the model
    before he reads its p.
    """
    markets = summary["markets"] + summary.get("missing", 0)
    got = summary["cleared"] / markets
    if got >= floor:
        return "MANTENER", (f"{summary['cleared']} de {markets} mercados con la "
                            f"esperanza por encima de cero ({got:.1%} >= {floor:.1%})")
    return "DESCARTAR", (f"solo {summary['cleared']} de {markets} mercados con la "
                         f"esperanza por encima de cero ({got:.1%} < {floor:.1%})")
