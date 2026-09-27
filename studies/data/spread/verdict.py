"""Whether the relative spread is constant, which model reconstructs it best, and what to declare in SQX."""

import numpy as np
import pandas as pd

from studies.data.spread import model

BPS = 1e4


def full_years(yearly: pd.DataFrame) -> pd.DataFrame:
    """The yearly table without its first and last year, which the feed covers only in part."""
    return yearly.iloc[1:-1]


def constancy(yearly: pd.DataFrame, column: str, tolerance: float) -> dict:
    """Whether every full year's mean stays within ±tolerance of the median of the years.

    Args:
        yearly: `measure.yearly()`.
        column: "pb media" for the relative spread, "puntos media" for the spread in points.
        tolerance: The owner's band, e.g. 0.20.

    Returns:
        {"constant", "ratios": year -> year's mean / median of the years, "worst"}.
    """
    values = full_years(yearly)[column]
    ratios = values / values.median()
    worst = float(ratios.iloc[np.argmax(np.abs(ratios.to_numpy() - 1))])
    return {"constant": bool((np.abs(ratios - 1) <= tolerance).all()),
            "ratios": {int(y): float(r) for y, r in ratios.items()}, "worst": worst}


def validate(days: pd.DataFrame, candidates: list[str], split: int) -> pd.DataFrame:
    """Each model fitted on one side of `split` and judged year by year on the other, both ways.

    Returns:
        One row per model and predicted year: `error` = predicted mean / measured mean − 1.
        Backwards (fitted on the later years) is the direction the Dukascopy years need.
    """
    year = days.index.year
    folds = (("hacia atrás", year >= split, year < split), ("hacia delante", year < split, year >= split))
    rows = []
    for name in candidates:
        for direction, train, test in folds:
            got = model.predict(name, model.fit(name, days[train]), days[test])
            by_year = got.groupby(year[test]).mean() / days["rel"][test].groupby(year[test]).mean()
            rows += [{"modelo": name, "sentido": direction, "año": int(y), "error": float(e - 1)}
                     for y, e in by_year.items()]
    return pd.DataFrame(rows)


def choose(relative: dict, errors: pd.DataFrame) -> str:
    """`relativo` when the relative spread is constant; otherwise the smallest mean |error|."""
    if relative["constant"]:
        return "relativo"
    return errors.assign(e=errors["error"].abs()).groupby("modelo")["e"].mean().idxmin()


def reconstruct(days: pd.DataFrame, vol: pd.DataFrame, name: str) -> pd.DataFrame:
    """A daily relative spread for every Dukascopy day: measured where Darwinex has it, modelled elsewhere.

    Returns:
        Indexed by day: `rel`, `price` and `source` ("medido" | "modelo"). The model is
        fitted on every Darwinex day.
    """
    predicted = model.predict(name, model.fit(name, days), vol)
    rel = predicted.where(~vol.index.isin(days.index), days["rel"].reindex(vol.index))
    return pd.DataFrame({"rel": rel, "price": vol["price"],
                         "source": np.where(vol.index.isin(days.index), "medido", "modelo")})


def propose(daily: pd.DataFrame, windows: dict, tick: float, factor: float) -> pd.DataFrame:
    """What each segment should carry in SQX, from the reconstructed spread times the owner's factor.

    Args:
        daily: `reconstruct()`.
        windows: segment -> (from, to) in epoch ms, as `core.assetdata.window` gives them.
        tick: `assets/`'s tick size, the unit of an SQX spread.
        factor: The safety factor.

    Returns:
        One row per segment: the share of its days measured, the mean relative spread, the
        commission in % that charges it once per trade (SQX charges `PercentageBased` once,
        on the open — OPEN.md #26), and the equivalent spread in points at the segment's
        median price.
    """
    rows = []
    for segment, (start, end) in windows.items():
        part = daily[(daily.index >= pd.Timestamp(start, unit="ms")) & (daily.index < pd.Timestamp(end, unit="ms"))]
        rel = float(part["rel"].mean())
        price = float(part["price"].median())
        rows.append({"tramo": segment, "desde": f"{part.index[0]:%Y-%m-%d}", "hasta": f"{part.index[-1]:%Y-%m-%d}",
                     "% días medidos": float((part["source"] == "medido").mean() * 100),
                     "spread medio (pb)": rel * BPS, "comisión % propuesta": rel * factor * 100,
                     "precio mediano": price, "puntos equivalentes": rel * factor * price / tick})
    return pd.DataFrame(rows)


def mc_multiples(days: pd.DataFrame, name: str, quantiles: list[float]) -> dict:
    """How far a day's spread strays from the model's mean, as the MC Retest's range in multiples.

    Args:
        days: `measure.days()`, the Darwinex days.
        name: The model the mean comes from (`relativo`: proportional to price).
        quantiles: [low, high], the owner's 2.5 % and 97.5 %.

    Returns:
        {"min", "max"}: quantiles of measured day ÷ model mean. Times the spread a task runs
        at, they give RandomizeSpread's Min and Max in points. A multiple and not a raw
        quantile of points because SQX draws ONE spread per simulation for the whole window
        (`RandomizeSpread.java`): pooling 2012's prices with 2023's would widen the range with
        the price level, which no single run ever pays.
    """
    ratios = days["rel"] / model.predict(name, model.fit(name, days), days)
    low, high = ratios.quantile(quantiles)
    return {"min": float(low), "max": float(high)}
