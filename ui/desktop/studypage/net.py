"""The study page's calls to the daemon, with a daemon that does not answer turned into a sentence."""

import httpx

from ui.desktop import client


def fetch(path: str, **params: str) -> dict:
    """GET a route, never raising.

    Args:
        path: Route under /api, without the prefix.
        params: Query parameters.

    Returns:
        The JSON body, or `{"error": sentence}` when the daemon is down or answered an
        error — the boundary with a person, where one failure must not close the window.
    """
    try:
        return client.get(path, **params)
    except httpx.HTTPError as e:
        return {"error": f"El demonio no respondió a /api/{path}: {e}"}


def send(path: str, body: dict) -> dict:
    """POST a route, never raising.

    Args:
        path: Route under /api, without the prefix.
        body: The JSON payload.

    Returns:
        As `fetch`.
    """
    try:
        return client.post(path, body)
    except httpx.HTTPError as e:
        return {"error": f"El demonio no respondió a /api/{path}: {e}"}
