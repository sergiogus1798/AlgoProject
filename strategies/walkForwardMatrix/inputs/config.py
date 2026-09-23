"""Read config.yaml and find the WFM export on disk."""

from pathlib import Path

import yaml

from core.paths import DATA

HERE = Path(__file__).resolve().parent.parent


def load() -> dict:
    """The study's settings.

    Returns:
        The parsed `config.yaml`, unmodified.
    """
    return yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8"))


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
