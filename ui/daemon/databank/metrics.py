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
        when nothing was exported yet.
    """
    path = metrics_export(project, databank) / "metrics.csv"
    if not path.is_file():
        return None
    frame = pd.read_csv(path, sep=";").set_index("Strategy Name")
    return frame[[c for c in frame.columns if c not in TEXT]].select_dtypes("number")


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
