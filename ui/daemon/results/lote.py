"""Where a one-off, multi-mother batch (structural, the ATR pass) keeps one strategy's result."""

import glob
from pathlib import Path

from core.paths import DATA

# Studies fabricated as a one-off batch of SEVERAL mothers together — unlike cloud/wfc/cscv/
# marketSurfaces (`ui.daemon.databank.batches`, always one JSON per single-mother batch), one
# of these lotes holds several strategies' own `estrategias/<name>.json`, the same shape
# `reports/` uses (`sqx.structural`, the ATR pass2 batch). `reports/<P>/<D>/<day>/` never holds
# them; block G's audit, 2026-09-30 (`studies/readings/structure`): the "Estructura" sub-panel
# fell back to the whole build's roster because nothing looked under `structural/`.
# `ui.daemon.workflow.steps.BATCH_ROOTS` names the same two folders for the workflow reader.
# A strategy in no lote is still looked for under `reports/` (`hits.sources`): the ATR study
# also runs on a databank (reports/<P>/WFM/<day>/atrCalculator/, 📓 2026-10-01).
ROOTS = {"structure": "structural", "atrCalculator": "atrCalculator"}


def paths(project: str, study: str, strategy: str) -> list[Path]:
    """Every lote's result for one strategy of a one-off multi-mother batch study.

    Args:
        project: SQX project name.
        study: Study key.
        strategy: The strategy's name as the lote spells it; these studies never judge a
            population.

    Returns:
        `<root>/<P>/<lote>/estudios/<study>/estrategias/<name>.json`, every lote that has it
        — project-wide, so found the same way whichever databank the page opened from. Two
        lotes with one strategy (the ATR pass1 and pass2) are both returned: the owner reads
        the newest and is told which pass it is (2026-10-01), never refused.
    """
    root = ROOTS.get(study)
    if root is None or not strategy:
        return []
    return sorted((DATA / root / project).glob(
        f"*/estudios/{study}/estrategias/{glob.escape(strategy)}.json"))


def name(path: Path) -> str:
    """The lote a result of `paths` belongs to: `pass2`, `batch1`, a day."""
    return path.parents[3].name
