"""Read config.yaml and find the WFM export on disk."""

from pathlib import Path

from core.paths import DATA
from core.study import config as study_config

HERE = Path(__file__).resolve().parent.parent


def load(overrides: list[str] | None = None) -> dict:
    """The study's settings.

    Args:
        overrides: "section.key=value" strings; each keeps the type of the value it replaces
            (core.study.config).

    Returns:
        The parsed `config.yaml`.
    """
    return study_config.load(HERE / "config.yaml", overrides or [])


def export(project: str, databank: str, day: str | None = None) -> Path:
    """The `wfm/` folder of one export.

    Args:
        project: Project name on the master.
        databank: Export folder name, underscores not spaces.
        day: Export date. None takes the most recent one holding a matrix.

    Returns:
        The folder holding cells, steps, params and check as Parquet, and trades.parquet.
    """
    root = DATA / "raw" / project / databank
    if day:
        return root / day / "wfm"
    return sorted(d / "wfm" for d in root.iterdir() if (d / "wfm").is_dir())[-1]
