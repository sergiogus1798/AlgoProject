"""The window's only way to reach the daemon. No view opens a file or a CSV itself."""

import httpx

from core.paths import UI_PORT

BASE = f"http://127.0.0.1:{UI_PORT}"
_HTTP = httpx.Client(base_url=BASE, timeout=20.0)


def get(path: str, **params: str) -> dict:
    """Read something from the daemon.

    Args:
        path: Route under /api, without the prefix.
        params: Query parameters.

    Returns:
        The decoded JSON body. A non-2xx raises: the daemon is on loopback and started by
        this same process, so a failure there is a bug to see, not a state to render.
    """
    r = _HTTP.get(f"/api/{path}", params=params)
    r.raise_for_status()
    return r.json()


def post(path: str, body: dict) -> dict:
    """Change something through the daemon.

    Args:
        path: Route under /api, without the prefix.
        body: The JSON payload.

    Returns:
        The decoded JSON body.
    """
    r = _HTTP.post(f"/api/{path}", json=body)
    r.raise_for_status()
    return r.json()


def awake(port: int) -> bool:
    """Whether a daemon is already answering on this port.

    Args:
        port: Loopback port to probe.

    Returns:
        True when /api/health answers. Used before spawning a second daemon: two of them
        writing the same CSVs is how a row gets lost.
    """
    try:
        return httpx.get(f"http://127.0.0.1:{port}/api/health", timeout=1.0).json()["ok"]
    except httpx.HTTPError:
        return False
