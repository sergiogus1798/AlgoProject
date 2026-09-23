"""Read an SPP export: the wide permutation table, the parameters it permuted, and the origin."""

from pathlib import Path

import pandas as pd

ORIGINAL = -1
KEYS = ["strategy", "permutation"]


def strategies(directory: Path) -> list[str]:
    """Every strategy the export carries a permutation table for.

    Args:
        directory: The export's `spp/` folder.

    Returns:
        Names as SQX writes them, sorted.
    """
    return sorted(pd.read_parquet(directory / "runs.parquet")["strategy"].unique())


def grid(directory: Path, strategy: str) -> pd.DataFrame:
    """One row per permutation: its parameter values, then its statistics.

    Args:
        directory: The export's `spp/` folder.
        strategy: Which strategy's table to read.

    Returns:
        Indexed by permutation number, parameter columns first. The original strategy is
        permutation -1 and is a row here too. Parameter columns other strategies permuted
        and this one did not come out all-NaN in the wide table and are dropped, so the
        frame holds exactly this strategy's parameters, as the long form used to.
    """
    frame = pd.read_parquet(directory / "spp.parquet", filters=[("strategy", "==", strategy)])
    frame = frame.drop(columns="strategy").set_index("permutation")
    return frame.dropna(axis=1, how="all")


def parameters(directory: Path, strategy: str) -> list[str]:
    """The parameters this strategy's SPP actually permuted.

    Args:
        directory: The export's `spp/` folder.
        strategy: Which strategy.

    Returns:
        Names in the order SQX lists them. A parameter absent here was frozen by the SPP
        settings, which says nothing about whether it matters.
    """
    runs = pd.read_parquet(directory / "runs.parquet").set_index("strategy")
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
    names = parameters(directory, strategy)
    row = pd.read_parquet(directory / "spp.parquet", columns=[*KEYS, *names],
                          filters=[("strategy", "==", strategy), ("permutation", "==", ORIGINAL)])
    return {k: float(row[k].iloc[0]) for k in names}


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
