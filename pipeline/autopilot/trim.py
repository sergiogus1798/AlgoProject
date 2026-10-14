"""After step 8: save the survivors to the store, then cut `Results` down to them (D16, encargo 66).

`Results` at full size costs 113-116 s per SQX stop and 45 s per load; nothing after step 8 reads it
(the studies read the harvest parquet, the task chain reads `OOS` and beyond).
"""

from collections.abc import Callable
from pathlib import Path

import pandas as pd

from core.paths import WORKERS
from core.store import save
from sqx.curate import apply_verdict

BANK = "Results"
REFUSED = "RESULTS SIN RECORTAR:"


def results(
    project: str,
    role: str,
    pop: pd.DataFrame,
    held: pd.DataFrame,
    out: Path,
    full: Callable[[], set[str] | None],
    seal: Callable[[], Callable[[], None]],
) -> str:
    """Cut `Results` to the strategies step 8 kept (survivors and limbo), worker stopped.

    Args:
        project: Project name.
        role: The worker holding the project.
        pop: Step 8's verdict frame: `strategy`, `identity` and `verdict` (DESCARTAR drops).
        held: What `Results` holds, `judge.population` of it: `strategy` and `identity`.
        out: The step's folder; the `Results` verdict lands there.
        full: The identities of the newest full `Results` harvest on disk, None when there is none.
        seal: Called before the cut; returns what re-signs the `Results` exports that were fresh,
            called after it (the pre-trim export is the whole build and must stay so).

    Returns:
        One line for the step's report. Nothing is touched when `Results` already holds only
        survivors, or when there are none (the run ends). A refusal (this run's kept strategies
        not in the store, the full harvest not on disk) is a line starting `RESULTS SIN RECORTAR:`,
        never an exit: step 8 stays done and a retry would only sign another ledger row.
    """
    kept = pop[pop["verdict"] != apply_verdict.DROP]
    keep = set(kept["identity"])
    if not keep or held.empty or bool(held["identity"].isin(list(keep)).all()):
        return f"{BANK}: nada que recortar"
    whole = full()
    if whole is None or not keep <= whole:
        return f"{REFUSED} la cosecha completa de {BANK} no está en disco"
    dirs = sorted(
        d
        for w in WORKERS.values()
        for d in (w["path"] / "user/projects" / project / "databanks").glob("*")
    )
    try:
        save.project(project, dirs)
    except (
        Exception,
        SystemExit,
    ) as e:  # a failed save is a refusal, not the end of the workflow
        return f"{REFUSED} el guardado falló ({e})"
    lost = sorted(
        set(save.unsaved(project)) & set(kept["strategy"])
    )  # this run's, not an older run's
    if lost:
        return (
            f"{REFUSED} {len(lost)} supervivientes del paso 8 no están en el almacén "
            f"({', '.join(lost[:3])}); `python3 -m core.store save {project}`"
        )
    csv = out / "verdict-results.csv"
    held.assign(
        verdict=[
            apply_verdict.DROP if i not in keep else "MANTENER"
            for i in held["identity"]
        ]
    ).to_csv(csv, index=False)
    resign = seal()
    cut = apply_verdict.apply(project, BANK, csv, role)
    resign()
    return f"{BANK}: {cut['before']} → {cut['after']}"
