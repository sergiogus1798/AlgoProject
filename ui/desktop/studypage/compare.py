"""The two results a comparison puts side by side: two runs of one strategy, or two strategies."""

from typing import TYPE_CHECKING

from ui.desktop.blocks.states import colour
from ui.desktop.studypage.net import fetch

if TYPE_CHECKING:
    from ui.desktop.studypage.page import StudyPage


def query(where: dict, study: str) -> dict:
    """The query naming one study of the place on screen.

    Args:
        where: project, databank, strategy ("" for the population), identity.
        study: Study key.

    Returns:
        The parameters `/api/result` and `/api/history` take.
    """
    return {"project": where["project"], "databank": where["databank"], "study": study,
            "strategy": where["strategy"] or "", "identity": where["identity"] or ""}


def runs(where: dict, study: str, left: str, right: str) -> tuple[list, tuple[str, str]]:
    """Two runs of the study on screen.

    Args:
        where: project, databank, strategy ("" for the population), identity.
        study: Study key.
        left, right: The two days.

    Returns:
        ([left result, right result], titles); a side is None when it holds no result.
    """
    got = [fetch("result", **query(where, study), day=d).get("result") for d in (left, right)]
    return got, (f"Run {left}", f"Run {right}")


def strategies(where: dict, study: str, strategy: str,
               identity: str) -> tuple[list, tuple[str, str]]:
    """The study for the strategy on screen and for another of the same databank.

    Args:
        where: As in `runs`, with a strategy.
        study: Study key.
        strategy, identity: The other strategy — of this databank, so its identity is its own.

    Returns:
        As `runs`: the strategy on screen left, the other right.
    """
    mine = fetch("result", **query(where, study)).get("result")
    other = fetch("result", **query(where, study) | {"strategy": strategy,
                                                     "identity": identity}).get("result")
    return [mine, other], (where["strategy"], strategy)


def paint(page: "StudyPage", results: list[dict | None], titles: tuple[str, str]) -> None:
    """Draw two results side by side on the page, or say which side has none.

    Args:
        page: The study page (`view`, `note`, `back`).
        results, titles: As `runs`/`strategies` returned them.
    """
    missing = [t for r, t in zip(results, titles) if r is None]
    if missing:
        page.note.setText(f'<span style="color:{colour("fail")}">No se puede comparar: '
                          f"{', '.join(missing)} no tiene resultado de este estudio aquí.</span>")
        return
    page.view.compare(results[0], results[1], titles)
    page.note.setText(f"Comparando {titles[0]} (izquierda) con {titles[1]} (derecha).")
    page.back.show()
