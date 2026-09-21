"""Turn the five CSVs an SPP export leaves into one grid: parameters wide, metrics beside them."""

from pathlib import Path

import pandas as pd

ORIGINAL = -1


def strategies(directory: Path) -> list[str]:
    """Every strategy the export carries a permutation table for.

    Args:
        directory: The export's `spp/` folder.

    Returns:
        Names as SQX writes them, sorted.
    """
    return sorted(pd.read_csv(directory / "runs.csv")["strategy"].unique())


def grid(directory: Path, strategy: str) -> pd.DataFrame:
    """One row per permutation: its parameter values, then its statistics.

    Args:
        directory: The export's `spp/` folder.
        strategy: Which strategy's table to read.

    Returns:
        Indexed by permutation number, parameter columns first. The original strategy
        sits at permutation -1 in `permutation_params.csv` but has no row in
        `permutations.csv`, so the inner join drops it; `original` reads it separately.
    """
    params = pd.read_csv(directory / "permutation_params.csv")
    stats = pd.read_csv(directory / "permutations.csv")
    wide = params[params["strategy"] == strategy].pivot(
        index="permutation", columns="parameter", values="value")
    measured = stats[stats["strategy"] == strategy].set_index("permutation").drop(
        columns="strategy")
    return wide.join(measured, how="inner")


def parameters(directory: Path, strategy: str) -> list[str]:
    """The parameters this strategy's SPP actually permuted.

    Args:
        directory: The export's `spp/` folder.
        strategy: Which strategy.

    Returns:
        Names in the order SQX lists them. A parameter absent here was frozen by the SPP
        settings, which says nothing about whether it matters.
    """
    runs = pd.read_csv(directory / "runs.csv").set_index("strategy")
    return runs.loc[strategy, "parameters"].split()


def original(directory: Path, strategy: str) -> dict[str, float]:
    """The tuple the strategy was built with.

    Args:
        directory: The export's `spp/` folder.
        strategy: Which strategy.

    Returns:
        Parameter name to value, read from permutation -1. It anchors everything
        downstream: a design that cannot contain it cannot show that the plateau moved.
    """
    params = pd.read_csv(directory / "permutation_params.csv")
    rows = params[(params["strategy"] == strategy) & (params["permutation"] == ORIGINAL)]
    return dict(zip(rows["parameter"], rows["value"]))


def varying(frame: pd.DataFrame, names: list[str]) -> list[str]:
    """Metric columns that are not constant across the grid.

    Args:
        frame: A grid from `grid`.
        names: Parameter columns, which are excluded.

    Returns:
        The columns worth reading. Measured 2026-09-20 on XAUUSD SPP IS, 42 of the 152
        statistics hold one value for the whole grid -- the four `AddMarkets*Median`,
        `BestWF`, `EdgeDecayRatio` and 34 unnamed `stat:*` columns -- and a constant
        column in an eta-squared table is a row of zeros pretending to be a measurement.
    """
    metrics = frame.columns.difference(names)
    numeric = frame[metrics].apply(pd.to_numeric, errors="coerce")
    return sorted(numeric.columns[numeric.nunique(dropna=True) > 1])
