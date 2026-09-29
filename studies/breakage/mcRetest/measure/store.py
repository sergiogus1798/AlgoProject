"""Where the parquet lives, how it is partitioned, and the only way anything reads it back."""

from pathlib import Path

import pandas as pd

from core.paths import export_dir

SIMS, LEVELS, ORIGINAL, PNL, RETURNS, TRADES = ("sims", "levels", "original", "pnl", "returns",
                                                "trades")


def root(project: str, databank: str, day: str) -> Path:
    """The directory one ingest wrote.

    Args:
        project: SQX project name.
        databank: Name of the ingest run, not of a single SQX databank -- one run covers all
            eight tasks and they are the `task=` partition inside it.
        day: Ingest date as YYYY-MM-DD.

    Returns:
        Path under the data root. Exports are dated and immutable: a re-ingest is a new
        directory, never an overwrite.
    """
    return export_dir(project, databank, day)


def write(frame: pd.DataFrame, where: Path, parts: list[str], compression: str) -> int:
    """Write one dataset, partitioned.

    Args:
        frame: The rows.
        where: Directory for this dataset.
        parts: Columns to partition by, outermost first.
        compression: Parquet codec.

    Returns:
        Rows written.
    """
    where.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(where, partition_cols=parts, compression=compression, index=False)
    return len(frame)


def load_sims(project: str, databank: str, day: str, task: str | None = None) -> pd.DataFrame:
    """The reconstructed metrics, one row per simulation.

    Args:
        project: SQX project name.
        databank: Ingest run name.
        day: Ingest date.
        task: One task key, or None for the whole battery.

    Returns:
        One row per (task, strategy, simulation) with the 30 metrics as columns. This is the
        study's main table and nothing downstream reopens a .sqx.
    """
    where = root(project, databank, day) / SIMS
    filters = [("task", "==", task)] if task else None
    return pd.read_parquet(where, filters=filters)


def load_levels(project: str, databank: str, day: str, usable: bool = True) -> pd.DataFrame:
    """The confidence table SQX stored, long.

    Args:
        project: SQX project name.
        databank: Ingest run name.
        day: Ingest date.
        usable: Keep only the runs whose stored table can be read at all. Passing False is
            how a caller says out loud that it wants the rank-shifted ones too.

    Returns:
        One row per (task, strategy, level, metric). **Long, not wide, deliberately**: a
        level is a marginal order statistic per metric, so two metrics at one level come
        from two different simulations. In a wide frame `df[["NetProfit", "Drawdown"]]`
        looks like a scenario and is not one; in this shape that query cannot be written.
    """
    where = root(project, databank, day) / LEVELS
    filters = [("usable", "==", True)] if usable else None
    return pd.read_parquet(where, filters=filters)


def load_original(project: str, databank: str, day: str) -> pd.DataFrame:
    """The unperturbed backtest each task's simulations were perturbed away from.

    Args:
        project: SQX project name.
        databank: Ingest run name.
        day: Ingest date.

    Returns:
        One row per (task, strategy). Tasks 1 to 7 share one in-sample original per
        strategy; the production task has its own over the full sample, with roughly half
        as many trades again. They are different backtests and do not compare like for like.
    """
    return pd.read_parquet(root(project, databank, day) / ORIGINAL)


def load_pnl(project: str, databank: str, day: str, task: str, strategy: str) -> pd.DataFrame:
    """The raw P/L vectors of one strategy under one task.

    Args:
        project: SQX project name.
        databank: Ingest run name.
        day: Ingest date.
        task: One task key.
        strategy: One strategy id.

    Returns:
        One row per trade, with its simulation number and its P/L in **USD**. Stored in
        cents as integers, exactly as the .bin holds them, so the parquet is reproducible
        from the archive; the conversion is this one documented division. Kept as a
        separate dataset because only the equity fan and the coherent scenario need it, and
        the test battery should not pay to read it.
    """
    frame = pd.read_parquet(root(project, databank, day) / PNL,
                            filters=[("task", "==", task), ("strategy", "==", strategy)])
    return frame.assign(pnl=frame["pnl_cents"] / 100.0).drop(columns="pnl_cents")


def load_trades(project: str, databank: str, day: str, strategy: str = "") -> pd.DataFrame:
    """The unperturbed trade list each strategy actually produced, joined in from its harvest.

    Args:
        project: SQX project name.
        databank: Ingest run name.
        day: Ingest date.
        strategy: One strategy id, or empty for all of them.

    Returns:
        One row per trade: Open time, Close time, Type, Size and cost (USD, `core.trades.cost`),
        `strategy` naming it under this ingest's own key rather than the harvest's identity
        (`measure/originals.py`). Never a simulation -- a perturbed run carries no times or
        prices to price a random trader against, which is why this is a separate dataset from
        `pnl` and is read only for `footprint()`'s benchmark (OPEN.md #71).
    """
    filters = [("strategy", "==", strategy)] if strategy else None
    return pd.read_parquet(root(project, databank, day) / TRADES, filters=filters)


def load_returns(project: str, databank: str, day: str) -> pd.DataFrame:
    """Daily profit of each strategy's original backtest, one column per strategy.

    Args:
        project: SQX project name.
        databank: Ingest run name.
        day: Ingest date.

    Returns:
        A frame indexed by date with one column per strategy. This is the study's only
        dated series -- a simulation file carries no dates at all -- and so the only
        possible input to a correlation between strategies.
    """
    frame = pd.read_parquet(root(project, databank, day) / RETURNS)
    return frame.pivot(index="date", columns="strategy", values="ret").fillna(0.0)
