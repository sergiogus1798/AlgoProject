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


def pair(databank: str) -> str:
    """The other half of an IS/OOS SPP databank pair.

    Args:
        databank: "SPP_IS" or "SPP_OOS" (or any name ending the same way).

    Returns:
        The counterpart name. `report.py` needs both: the IS/OOS panels compare across
        them, and neither export alone carries the other window's numbers.
    """
    if databank.upper().endswith("_OOS"):
        return databank[:-len("_OOS")] + "_IS"
    if databank.upper().endswith("_IS"):
        return databank[:-len("_IS")] + "_OOS"
    raise ValueError(f"{databank!r} does not end in _IS or _OOS")


def other(project: str, databank: str) -> Path | None:
    """The paired databank's own most recent export folder, or None when it has none yet.

    Args:
        project: Project name on the master.
        databank: The databank whose pair is wanted.

    Returns:
        `export(project, pair(databank))`, dated on its own — IS and OOS are exported on
        different days as a rule — or None when that databank carries no `spp/` export at
        all, a real state (OOS often lags IS, or exports something else entirely) rather
        than a malformed one.
    """
    root = DATA / "raw" / project / pair(databank)
    if not root.is_dir() or not any((d / "spp").is_dir() for d in root.iterdir()):
        return None
    return export(project, pair(databank))
