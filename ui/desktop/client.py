"""The window's only way to reach the daemon. No view opens a file or a CSV itself."""

import httpx

from core.paths import UI_PORT

BASE = f"http://127.0.0.1:{UI_PORT}"
_HTTP = httpx.Client(base_url=BASE, timeout=20.0)


def aim(port: int) -> None:
    """Talk to the daemon on another loopback port — a scratch daemon for shots and walks.

    Args:
        port: Its port; the default is `ui_port` of `config/machine.yaml`.
    """
    global BASE, _HTTP
    BASE = f"http://127.0.0.1:{port}"
    _HTTP = httpx.Client(base_url=BASE, timeout=20.0)


def get(path: str, wait: float | None = None, **params: str) -> dict:
    """Read something from the daemon.

    Args:
        path: Route under /api, without the prefix.
        wait: Seconds to wait instead of the client's 20, for a read that runs off the GUI
            thread and can be slow the first time (the gallery hashes every install).
        params: Query parameters.

    Returns:
        The decoded JSON body. A non-2xx raises: the daemon is on loopback and started by
        this same process, so a failure there is a bug to see, not a state to render.
    """
    r = _HTTP.get(f"/api/{path}", params=params,
                  **({"timeout": wait} if wait is not None else {}))
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


def health(port: int) -> dict | None:
    """What the daemon on this port says about itself, or None when nothing answers.

    Args:
        port: Loopback port to probe.

    Returns:
        The /api/health body: `code` (the fingerprint of the daemon code it runs), `pid`
        and `busy` (jobs running or queued). A daemon older than those fields lacks them.
    """
    try:
        return httpx.get(f"http://127.0.0.1:{port}/api/health", timeout=1.0).json()
    except httpx.HTTPError:
        return None
