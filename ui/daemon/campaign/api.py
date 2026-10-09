"""The campaign's four routes: `/api/campaign/list`, `show`, `open` and `extra` — files read, nothing run."""

from collections.abc import Callable

from fastapi import APIRouter

from ui.daemon.campaign import shelf

ROUTER = APIRouter()


def _answer(call: Callable[..., dict], *args: str) -> dict:
    """`call(*args)` or `{"error"}`, a sentence and never a 500."""
    try:
        return call(*args)
    except FileNotFoundError as e:
        return {"error": str(e)}
    except (OSError, ValueError, KeyError) as e:  # the boundary with a person
        return {"error": f"No pude leer el workflow: {type(e).__name__}: {e}"}


@ROUTER.get("/api/campaign/list")
def campaign_list() -> dict:
    """Every saved workflow, newest first: `{"workflows": [...]}`."""
    return _answer(lambda: {"workflows": shelf.workflows()})


@ROUTER.get("/api/campaign/show")
def campaign_show(workflow: str = "") -> dict:
    """One workflow's header, funnel, steps with seconds, strategies and what was not kept."""
    return _answer(shelf.show, workflow)


@ROUTER.get("/api/campaign/open")
def campaign_open(workflow: str = "", strategy: str = "") -> dict:
    """What the Estrategia page needs to open one finalist of the workflow, from the archive."""
    return _answer(shelf.opened, workflow, strategy)


@ROUTER.get("/api/campaign/extra")
def campaign_extra(workflow: str = "", key: str = "") -> dict:
    """One result kept in the workflow's folder (steps 17-24), as `/api/result` serves it."""
    return _answer(shelf.extra, workflow, key)
