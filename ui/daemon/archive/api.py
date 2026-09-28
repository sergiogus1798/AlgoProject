"""PORTFOLIOS' two routes: `/api/archive/list` and `/api/archive/show` — files read, nothing run."""

from fastapi import APIRouter

from ui.daemon.archive import shelf

ROUTER = APIRouter()


@ROUTER.get("/api/archive/list")
def archive_list() -> dict:
    """Every archived strategy with its versions, newest archive first.

    Returns:
        `{"strategies": shelf.strategies()}`, or `{"error"}` when the archive cannot be
        read (a half-written manifest, a folder moved by hand) — a sentence, never a 500.
    """
    try:
        return {"strategies": shelf.strategies()}
    except (OSError, ValueError, KeyError) as e:  # the boundary with a person
        return {"error": f"No pude leer el archivo: {type(e).__name__}: {e}"}


@ROUTER.get("/api/archive/show")
def archive_show(identity: str = "", version: str = "") -> dict:
    """One archived version in full, for the detail beside the list.

    Args:
        identity: The strategy's identity.
        version: A version folder name; "" for the newest.

    Returns:
        As `shelf.show`, or `{"error"}` in Spanish.
    """
    if not identity:
        return {"error": "Elige una estrategia archivada."}
    try:
        return shelf.show(identity, version)
    except FileNotFoundError as e:
        return {"error": str(e)}
    except (OSError, ValueError, KeyError) as e:  # the boundary with a person
        return {"error": f"No pude leer esa versión: {type(e).__name__}: {e}"}
