"""The variant-batch routes: one mother's batch for the parallel coordinates, and whether it has one."""

from fastapi import APIRouter

from ui.daemon.batch import panel

ROUTER = APIRouter()


def leaks(value: object) -> bool:
    """Whether any key or text inside a response names the reserved segment.

    Args:
        value: The response, or any part of it.

    Returns:
        True at the first sealed key or string.
    """
    if isinstance(value, dict):
        return any(panel.sealed(str(k)) or leaks(v) for k, v in value.items())
    if isinstance(value, list):
        return any(leaks(v) for v in value if isinstance(v, (dict, list, str)))
    return isinstance(value, str) and panel.sealed(value)


@ROUTER.get("/api/batch")
def get_batch(project: str, strategy: str) -> dict:
    """One mother's variant batch: each variant's parameters and NetProfit in build and oos1.

    Args:
        project: Project name.
        strategy: The mother, "Strategy 18.13.59" or its folder's "Strategy_18.13.59".

    Returns:
        What `panel.batch` builds. Sealed columns are never read; should anything sealed
        reach this point anyway (a project or parameter named so), the whole answer is
        refused rather than trimmed.
    """
    out = panel.batch(project, strategy)
    if leaks(out):
        return {"has_batch": out["has_batch"],
                "error": "la respuesta nombraba el tramo reservado y se ha retenido entera"}
    return out


@ROUTER.get("/api/batch/has")
def get_has(project: str, strategy: str) -> dict:
    """Whether a mother has a batch folder at all, without opening it.

    Args:
        project: Project name.
        strategy: As in `get_batch`.

    Returns:
        `{"has_batch": bool}`, for the strategy page to decide whether to show «Lote».
    """
    return {"has_batch": bool(panel.folders(project, strategy))}
