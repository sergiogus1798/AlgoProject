"""Read config.yaml and find the SPP export on disk."""

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
