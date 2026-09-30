"""The owner's column choice per databank table: `AlgoData/filters/<P>/<D>/columns.json`."""

import json
import os
import threading
from pathlib import Path

from ui.daemon.filters import discards

# FastAPI runs these routes on a thread pool: two saves at once must not interleave their
# read-modify-write.
LOCK = threading.Lock()


def file(project: str, databank: str) -> Path:
    """The databank's `columns.json`, beside its filter log, whether or not it exists yet."""
    return discards.folder(project, databank) / "columns.json"


def views(project: str, databank: str) -> dict[str, dict]:
    """Every table's saved choice of one databank.

    Returns:
        table («tab › sub») → {hidden, added, order}, what the owner changed against the
        table's default; {} while nothing was chosen, and for a file that is not a JSON
        object (hand-edited, half-written): the next save overwrites it.
    """
    path = file(project, databank)
    try:
        got = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except ValueError:
        return {}
    return got if isinstance(got, dict) else {}


def save(project: str, databank: str, table: str, view: dict | None) -> dict:
    """Keep one table's choice, or drop it (`view` None: «restaurar vista por defecto»).

    Args:
        project: Project name.
        databank: Either spelling.
        table: «tab › sub», as the panel names the table.
        view: {hidden, added, order} against the table's default.

    Returns:
        Every choice of the databank after the write, which is atomic (a temporary file
        renamed over the old one).
    """
    with LOCK:
        kept = views(project, databank)
        if view is None:
            kept.pop(table, None)
        else:
            kept[table] = view
        path = file(project, databank)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(kept, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, path)
    return kept
