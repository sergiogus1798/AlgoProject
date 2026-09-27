"""The routes that load a databank's data when the window selects it."""

from fastapi import APIRouter
from pydantic import BaseModel

from ui.daemon.loader import state

ROUTER = APIRouter()


class Load(BaseModel):
    """A databank the window just selected."""

    project: str
    databank: str
    retry: bool = False


@ROUTER.get("/api/load")
def load_status(project: str, databank: str) -> dict[str, object]:
    """Where one databank's data stands, piece by piece, without starting anything."""
    try:
        return state.status(project, databank)
    except (OSError, KeyError, ValueError) as e:    # a file the owner's SQX is rewriting
        return {"error": f"no se pudo leer {project} / {databank}: {e}"}


@ROUTER.post("/api/load")
def load(req: Load) -> dict[str, object]:
    """Queue what the databank is missing or has stale, once; answer where it stands."""
    try:
        return state.load(req.project, req.databank, req.retry)
    except (OSError, KeyError, ValueError) as e:
        return {"error": f"no se pudo cargar {req.project} / {req.databank}: {e}"}
