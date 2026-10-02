"""A databank's SQX metrics: its newest cosecha (IS + OOS paired) or its current metrics export."""

import pandas as pd

from core.paths import harvest_dir, metrics_export
from ui.daemon.loader.state import newest

# Columns of either file that are labels, not figures.
TEXT = {"strategy", "strategy_build", "structure", "Strategy Name", "Filters result"}


def harvest(project: str, databank: str) -> pd.DataFrame | None:
    """The newest cosecha's metrics of a build databank, by identity.

    Args:
        project: Project name.
        databank: Either spelling.

    Returns:
        Indexed by identity: `name` (the build's) and one column per metric and sample,
        spelled `Net profit (IS)`; None when the databank has no cosecha.
    """
    found = newest(harvest_dir(project, databank, "x").parent, "metrics.parquet")
    if found is None:
        return None
    frame = pd.read_parquet(found)
    figures = frame[[c for c in frame.columns if c not in TEXT]].select_dtypes("number")
    figures.columns = [c.replace(" [", " (").replace("]", ")") for c in figures.columns]
    return figures.assign(name=frame["strategy_build"])


def export(project: str, databank: str) -> pd.DataFrame | None:
    """The databank's current metrics export (`metrics.csv`), by strategy name.

    Args:
        project: Project name.
        databank: Either spelling.

    Returns:
        Indexed by the strategy's name, one numeric column per metric and sample; None
        when nothing was exported yet, or the export of an empty databank (a header, or the
        1-byte file older exports left, which pandas refuses: «No columns to parse»).
    """
    path = metrics_export(project, databank) / "metrics.csv"
    if not path.is_file():
        return None
    try:
        frame = pd.read_csv(path, sep=";")
    except pd.errors.EmptyDataError:
        return None
    if "Strategy Name" not in frame:
        return None
    frame = frame.set_index("Strategy Name")
    figures = frame[[c for c in frame.columns if c not in TEXT]].select_dtypes("number")
    return empty_samples(swap_block(figures, databank))


def swap_block(frame: pd.DataFrame, databank: str) -> pd.DataFrame:
    """Relabel (IS)/(OOS) when SQX filed a single-window task's real numbers under the
    other sample's columns — a known quirk (`knowhow/export/databank-metrics-is-oos.md`):
    `SPP OOS` files its retest figures as `(IS)`, `OOS` files them as `(OOS)`; which one
    cannot be assumed from the column name, only read off the data (🔬 2026-09-30, `SPP
    OOS`: 367 trades / 31,133 net profit under `(IS)`, `(OOS)` all zero — the SPP databank
    showing «IS» and «OOS» as the same figures traced here, not to a join bug).

    Args:
        frame: Numeric columns only, `Net profit (IS)`-spelled.
        databank: This databank's own name, spelled either way.

    Returns:
        `frame`, its (IS) and (OOS) suffixes swapped when the databank's own sample (its
        name's last word, OOS or else IS) is empty while the other is filled; unchanged
        when nothing needs recovering, including when both or neither carry numbers (an
        actual in/out split, or truly no trades, is not this quirk's business to guess at).
    """
    role = "OOS" if databank.replace("_", " ").rsplit(" ", 1)[-1] == "OOS" else "IS"
    other = "IS" if role == "OOS" else "OOS"
    mine = [c for c in frame.columns if c.endswith(f"({role})")
            and not c.startswith(("Param Count", "TimeFrame", "DoF Ratio"))]
    theirs = [c.replace(f"({role})", f"({other})") for c in mine if
              c.replace(f"({role})", f"({other})") in frame.columns]
    if not mine or not theirs:
        return frame
    mine_filled = bool(frame[mine].fillna(0).abs().to_numpy().sum())
    theirs_filled = bool(frame[theirs].fillna(0).abs().to_numpy().sum())
    if mine_filled or not theirs_filled:
        return frame
    swap = {c: c.replace(f"({role})", f"({other})") if c.endswith(f"({role})")
            else c.replace(f"({other})", f"({role})") if c.endswith(f"({other})") else c
            for c in frame.columns}
    return frame.rename(columns=swap)


def empty_samples(frame: pd.DataFrame) -> pd.DataFrame:
    """Every metric of a sample a strategy made no trade in, blanked: no trades, no figures.

    A Cross Market or Cross TF task runs `build..oos1` as one window SQX files under OOS, so
    its IS block is all zeros — and a 0 Profit Factor is painted red as a loss (📓 2026-09-30).
    A blank reads «—», which is what it is.
    """
    for sample in ("IS", "OOS"):
        cols = [c for c in frame.columns if c.endswith(f"({sample})")
                and not c.startswith(("Param Count", "TimeFrame", "DoF Ratio"))]  # not measured
        if cols:
            none = (frame[cols].fillna(0) == 0).all(axis=1)
            frame.loc[none, cols] = float("nan")
    return frame


def source(project: str, databank: str) -> tuple[str, pd.DataFrame | None]:
    """Which of the two the table reads, and its frame.

    Returns:
        ("cosecha", by identity) when a cosecha exists — it pairs IS with the OOS retest —
        else ("export", by name), else ("", None).
    """
    got = harvest(project, databank)
    if got is not None:
        return "cosecha", got
    got = export(project, databank)
    return ("export", got) if got is not None else ("", None)
