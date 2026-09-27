"""The search ledger as the window reads it: searches, funnel and history spent, one study at a time."""

import pandas as pd

from ledger import gate, record, spend, study as studymod, trials


def plain(frame: pd.DataFrame) -> list[dict]:
    """A frame as JSON-safe records.

    Args:
        frame: Any ledger frame.

    Returns:
        One dict per row, NaN as None — JSON has no NaN and the window would choke on it.
    """
    return frame.astype(object).where(frame.notna(), None).to_dict("records")


def newest() -> str | None:
    """The study whose ledger was written last, or None when there is none."""
    ids = studymod.studies()
    return max(ids, key=lambda s: studymod.path(s).stat().st_mtime) if ids else None


def spent_block(frame: pd.DataFrame) -> dict:
    """What history this study has already spent, and what that costs.

    Args:
        frame: What `ledger.study.read` returned, not empty.

    Returns:
        `segments` (reads per segment and by which steps), `virgin` (each declared segment
        with its window, reads and reservation), `blind` (steps 17-19 done, and whether step
        20 may read them), `trials` (N and pooled sigma, or the reason there is none).
        The asset lookup and the pooling can refuse; the refusal is shown, not raised,
        because this is the window.
    """
    segments = spend.spent(frame)
    segments["steps"] = segments["steps"].apply(lambda s: [float(x) for x in s])
    try:
        virgin = spend.virgin(frame, frame["symbol"].iloc[0])
    except FileNotFoundError as missing:
        virgin = {"error": f"activo sin ficha: {missing}"}
    done = gate.done(frame)
    try:
        gate.allow_read(frame)
        blind = {"done": {str(k): v for k, v in done.items()}, "open": True,
                 "text": "17, 18 y 19 hechos: el paso 20 puede leerlos"}
    except PermissionError as refusal:
        blind = {"done": {str(k): v for k, v in done.items()}, "open": False,
                 "text": str(refusal)}
    try:
        counted = trials.accumulated(frame)
        pooled = counted if counted["n"] else {"error": "ninguna búsqueda registró la "
                                                        "distribución de sus candidatos"}
    except ValueError as refusal:
        pooled = {"error": str(refusal)}
    return {"segments": plain(segments), "virgin": virgin, "blind": blind, "trials": pooled}


def ledger(study: str | None) -> dict:
    """Everything the ledger zone draws.

    Args:
        study: A study id, or None for the one written last.

    Returns:
        `studies` (every id), `study` (the one shown), `rows` (its searches, oldest first),
        `funnel` (in and out per search, with the share kept) and `spent` (see
        `spent_block`; empty when the study has no search yet).
    """
    chosen = study or newest()
    frame = studymod.read(chosen) if chosen else pd.DataFrame(columns=list(studymod.COLUMNS))
    return {"studies": studymod.studies(), "study": chosen, "rows": plain(frame),
            "funnel": plain(record.funnel(frame)) if len(frame) else [],
            "spent": spent_block(frame) if len(frame) else {}}
