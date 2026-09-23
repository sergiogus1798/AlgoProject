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
