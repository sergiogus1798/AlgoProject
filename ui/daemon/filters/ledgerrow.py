"""The ledger row of a filter or a manual deletion: its study (Q9), its step and its segment."""

from ledger import record, study as studymod
from sqx.projects.stage import titles
from ui.daemon.databank import layout
from ui.daemon.runner import where
from ui.daemon.workflow.steps import STAGE, STEPS

# Stages whose databanks hold OOS2 figures: nothing there is filtered (encargo 22 §7.1).
OOS2_STAGES = {"wfc", "wfm"}


def signed(project: str) -> tuple[str, dict] | str:
    """The study a project's searches are signed under, or why there is none.

    Returns:
        (study id, the registry row), or the sentence the window shows: a project without a
        template in `projects/registry.csv` has no family, so its filter is not logged — and,
        since a search the ledger does not count is the one thing it exists to prevent, not
        applied either.
    """
    family = where.family(project)
    if family is None:
        return (f"el proyecto {project} no tiene plantilla en projects/registry.csv: sin "
                "familia no hay estudio del ledger donde apuntar el filtro, así que no se aplica")
    row = where.enrolled(project)
    return studymod.study_id(row["symbol"], row["timeframe"], family), row


def placed(project: str, databank: str) -> tuple[float, str] | str:
    """The workflow step a filter on this databank belongs to, or why it has none.

    Returns:
        (step, SQX stage): the Python step that reads the stage whose task writes this
        databank (`Results`, the build's, → step 8), or the sentence why not — an OOS2
        stage, or a databank no task of the project's `project.cfx` writes.
    """
    same = databank.replace(" ", "_")
    task = next((t for t, out in layout.outputs(project).items()
                 if out.replace(" ", "_") == same), None)
    stage = next((s for s in STAGE.values() if task in titles(s)), None) if task else None
    if stage is None:
        return (f"ninguna tarea de {project} escribe {databank} (o ningún install tiene ya el "
                "proyecto): no sé a qué paso del workflow pertenece el filtro")
    if stage in OOS2_STAGES:
        return f"{databank} es de la etapa {stage}, que lee OOS2: no se filtra"
    step = next(s for s in STEPS if s["kind"] == "python" and isinstance(s["feeds"], tuple)
                and stage in s["feeds"])
    n = step["n"]
    return (float(n) if "." in n else int(n)), stage


def segment(read: set[str]) -> str:
    """The one segment the row names: `oos1` when the filter read anything out of sample
    (an OOS column, a study, a distribution), `build` when it read only IS columns."""
    return "build" if read == {"IS"} else "oos1"


def log(project: str, databank: str, step: float, read: set[str], n_in: int, n_out: int,
        criterion: str, origin: str, thresholds: list[dict] | None) -> dict:
    """Write the one ledger row, through `record.log` and so through the one-way door.

    Args:
        project: Project name.
        databank: Either spelling.
        step: What `placed` gave.
        read: The samples the filter read: `IS`, `OOS`, or '' for a study's column.
        n_in: Visible before.
        n_out: Visible after.
        criterion: The expression, in the window's words (`evaluate.expression`); the
            machine form is `thresholds`.
        origin: `filter` or `manual`.
        thresholds: The filter's rows; None for a manual deletion.

    Returns:
        The row as written. Raises `PermissionError` when the door refuses the segment.
    """
    study, row = signed(project)
    return record.log(study, {
        "step": step, "launched_by": "ventana", "symbol": row["symbol"],
        "timeframe": row["timeframe"], "segment": segment(read), "n_in": n_in,
        "n_out": n_out, "criterion": criterion, "thresholds": thresholds,
        "note": (f"{'filtro' if origin == 'filter' else 'borrado a mano'} en la ventana · "
                 f"proyecto {project} · databank {databank} · lee "
                 f"{', '.join(sorted(s or 'estudios' for s in read))}")})
