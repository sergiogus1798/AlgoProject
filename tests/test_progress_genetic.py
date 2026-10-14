"""«En marcha» shows the genetic settings of a running Build: PopulationSize × Islands must fill first."""

from pathlib import Path

from core.paths import WORKERS
from ui.daemon.progress import genetic


def test_genetic_none_when_no_build_runs() -> None:
    """No running Build, no genetic line."""
    assert genetic(Path("/nonexistent"), False, {}) is None


def test_genetic_reads_settings_of_a_real_project() -> None:
    """Population is size times islands, read from a real project.cfx when one exists."""
    cfx = (
        next(iter(WORKERS.values()))["path"]
        / "user/projects/Test_Calib10_EURJPY_H1_L/project.cfx"
    )
    if not cfx.exists():
        return
    g = genetic(cfx, True, {"Initial population": 7})
    assert (
        g["population"] == g["size"] * g["islands"]
        and g["initial"] == 7
        and g["last"] is None
    )
