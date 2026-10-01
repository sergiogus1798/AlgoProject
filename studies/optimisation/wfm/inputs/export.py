"""Read a WFM export: the 30 cells, their steps, and the parameters the optimiser chose."""

from pathlib import Path

import pandas as pd

WINDOW = ("optimize_from", "optimize_to", "run_from", "run_to")


def cells(directory: Path) -> pd.DataFrame:
    """One row per matrix cell: a (runs, oos_pct) combination and its pooled result.

    Args:
        directory: The export's `wfm/` folder.

    Returns:
        The frame as exported. `fitness_is` and `fitness_oos` are the only fitness values
        SQX stores -- the per-step `is_Fitness` column exists but is zero throughout, so
        every step-level reading uses a real metric instead.
    """
    return pd.read_parquet(directory / "cells.parquet")


def steps(directory: Path, drop_future: bool = True) -> pd.DataFrame:
    """One row per walk-forward step: its two windows, and how it did in each.

    Args:
        directory: The export's `wfm/` folder.
        drop_future: Remove steps whose run window extends past the data.

    Returns:
        The frame with the four window columns parsed to timestamps.

        **The last step of every cell runs into the future.** Measured 2026-09-10, cell
        6x20 of `Strategy 1.19.29` ends with a step running 2025-12-31 to **2027-08-20**;
        60 of the 720 steps are marked that way. Their out-of-sample numbers are computed
        on data that does not exist and must never reach a correlation.
    """
    frame = pd.read_parquet(directory / "steps.parquet")
    if drop_future:
        frame = frame[~frame["future"]]
    for column in WINDOW:
        frame[column] = pd.to_datetime(frame[column], unit="s")
    return frame.reset_index(drop=True)


def trades(directory: Path) -> pd.DataFrame:
    """Every walk-forward trade, tagged by cell and by IS/OOS sample.

    Args:
        directory: The export's `wfm/` folder.

    Returns:
        The frame as `export_wfm.split` wrote it: `result` names the cell exactly as
        `cells()` and `steps()` do, `sample` is "IS" or "OOS", `period` the step index.
    """
    return pd.read_parquet(directory / "trades.parquet")


def chosen(directory: Path) -> pd.DataFrame:
    """The parameter values the optimiser settled on at each step.

    Args:
        directory: The export's `wfm/` folder.

    Returns:
        Wide: one row per (strategy, result, step index), one column per parameter, as
        the export wrote it. This is the only record of what the optimiser decided -- the thousands of combinations
        it tried inside each step are not stored anywhere, so nothing here can say how
        close the runner-up was.
    """
    return (pd.read_parquet(directory / "params.parquet")
            .set_index(["strategy", "result", "index"]))


def varying(frame: pd.DataFrame, prefix: str) -> list[str]:
    """Metric columns of one sample that are not constant.

    Args:
        frame: A steps or cells frame.
        prefix: `is_`, `oos_` or `all_`.

    Returns:
        Bare metric names. Of the 152 columns per sample, 42 to 46 hold one value for the
        whole export and carry nothing.
    """
    columns = [c for c in frame.columns if c.startswith(prefix)]
    live = [c for c in columns if frame[c].nunique(dropna=True) > 1]
    return sorted(c[len(prefix):] for c in live)


def conditions(directory: Path) -> pd.DataFrame | None:
    """Every cell against every condition SQX judged it by, or None for an older export.

    Args:
        directory: The export's `wfm/` folder.

    Returns:
        One row per (strategy, cell, condition): `family`, `metric`, `op`, `threshold`, the
        cell's `value`, and `met`. Exports before 2026-10-01 never wrote it.
    """
    path = directory / "conditions.parquet"
    return pd.read_parquet(path) if path.exists() else None


def objectives(directory: Path) -> pd.DataFrame | None:
    """Stability, score and the WF specials of every cell, conditions or not.

    Args:
        directory: The export's `wfm/` folder.

    Returns:
        One row per cell, `core.wfmobjectives.SHOWN` as columns, or None for an older export.
    """
    path = directory / "objectives.parquet"
    return pd.read_parquet(path) if path.exists() else None


def rules(directory: Path) -> pd.DataFrame:
    """The area rule each strategy ran with, as SQX stored it in the strategy.

    Args:
        directory: The export's `wfm/` folder.

    Returns:
        Indexed by strategy: `sqx_failed` and `threshold_pct`, `rows`, `cols`,
        `min_squares`. An export older than 2026-10-01 lacks the four and the caller takes
        `_build.yaml`'s; one older than 2026-09-26 has no `status.parquet` at all.
    """
    path = directory / "status.parquet"
    return (pd.read_parquet(path).set_index("strategy") if path.exists() else
            pd.DataFrame(index=pd.Index(cells(directory)["strategy"].unique(), name="strategy")))


def main(directory: Path) -> pd.DataFrame | None:
    """The original backtest's trades: each strategy with its own fixed parameters.

    Args:
        directory: The export's `wfm/` folder.

    Returns:
        tradestore's columns plus `Symbol` and `strategy`, or None for an export older than
        2026-10-01. SQX tags every trade `IST`: the window's own segments say which days
        were out of sample.
    """
    path = directory / "main.parquet"
    return pd.read_parquet(path) if path.exists() else None
