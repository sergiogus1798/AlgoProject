"""The state dot on each study tab, and where the page reads those states from."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap

from ui.desktop.blocks.states import colour, label
from ui.desktop.studypage.net import fetch
from ui.desktop.theme import T

SIZE = 14


def dot(cell: dict | None) -> QIcon:
    """A filled dot in the stored verdict's colour, a ring when caducado, a grey ring when absent.

    Args:
        cell: `{"state", "stale", ...}` of the newest stored run here, None when none.

    Returns:
        The tab's icon.
    """
    pix = QPixmap(SIZE, SIZE)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    if cell is None:
        p.setPen(QPen(QColor(T["faint"]), 1.5))
        p.drawEllipse(3, 3, SIZE - 6, SIZE - 6)
    elif cell.get("stale"):
        p.setPen(QPen(QColor(colour(cell["state"])), 2.5))
        p.drawEllipse(2, 2, SIZE - 4, SIZE - 4)
    else:
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(colour(cell["state"])))
        p.drawEllipse(1, 1, SIZE - 2, SIZE - 2)
    p.end()
    return QIcon(pix)


def says(cell: dict | None) -> str:
    """The sentence the dot's tooltip carries.

    Args:
        cell: As in `dot`.

    Returns:
        Spanish, naming the state, the study's own word and the day.
    """
    if cell is None:
        return "Sin resultado en este databank (círculo gris): no ha corrido aquí."
    stale = " · CADUCADO: se calculó con otra configuración" if cell.get("stale") else ""
    return (f"{label(cell['state'])} — «{cell.get('label') or '—'}» · día "
            f"{cell.get('day') or '—'}{stale}")


def of_strategy(project: str, databank: str, identity: str | None) -> tuple[dict, list[dict]]:
    """Every study's stored state for one strategy, and the databank's strategies.

    Args:
        project, databank: Where.
        identity: The strategy's identity; the matrix is keyed by it, never by name.

    Returns:
        ({study: cell}, [{"strategy", "identity"}]) from `/api/matrix`, empty on an error.
    """
    got = fetch("matrix", project=project, databank=databank)
    if "error" in got:
        return {}, []
    return got["cells"].get(identity or "", {}), got["strategies"]


def of_population(project: str, databank: str, keys: list[str]) -> dict:
    """Every study's newest population run on one databank.

    Args:
        project, databank: Where.
        keys: Study keys.

    Returns:
        {study: cell} from `/api/history` without a strategy (~0.3 s for the 28), only for
        studies with a run here.
    """
    out = {}
    for k in keys:
        runs = fetch("history", project=project, databank=databank, study=k).get("runs") or []
        if runs:
            out[k] = runs[0]
    return out
