"""Read config.yaml and find the SPP export on disk."""

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
    """The `spp/` folder of one export.

    Args:
        project: Project name on the master.
        databank: Databank name with spaces replaced by underscores, e.g. "SPP_IS".
        day: Export date. None takes the most recent one that holds an SPP table.

    Returns:
        The folder holding runs.parquet and spp.parquet. Trade
        and bar exports are dated and immutable, so several dates coexist on purpose and
        which one was read belongs in the report.
    """
    root = DATA / "raw" / project / databank
    if day:
        return root / day / "spp"
    return sorted(d / "spp" for d in root.iterdir() if (d / "spp").is_dir())[-1]
