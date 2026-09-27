"""The two results a comparison puts side by side: two runs of one strategy, or two strategies."""

from ui.desktop.studypage.net import fetch


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
    return got, (f"corrida {left}", f"corrida {right}")


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
