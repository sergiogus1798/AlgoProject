"""The gate every request to the daemon passes: its own Host, no foreign Origin, the session token."""

import os
import secrets

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from core import uitoken

ENV = "ALGO_UI_PORT"            # set by `serve` before the app is imported: the port it holds
OPEN = ("/api/health",)         # GET only: how a window learns a daemon is there at all
# Unarmed (port None) only when the app is imported without `serve` — a test's TestClient,
# which binds no socket. `serve` is the one thing that listens, and it arms first.
STATE: dict = {"port": None, "token": ""}


def arm(port: int) -> None:
    """Hold the port and the token `serve` minted for it; a daemon without one does not start."""
    token = uitoken.read(port)
    if not token:
        raise SystemExit(f"no hay token de sesión para el puerto {port}: arranca el demonio con "
                         "python3 -m ui.daemon.serve")
    STATE.update(port=port, token=token)


def refusal(method: str, path: str, headers: dict) -> str | None:
    """Why this request is not served, or None.

    Args:
        method: The HTTP method.
        path: The URL path.
        headers: The request's headers, names in lower case.

    Returns:
        "host" for a Host that is not this daemon on loopback (a DNS-rebound name), "origin"
        for a browser page of any other origin (a cross-origin POST always carries it),
        "token" for a missing or wrong session token. Only `GET /api/health` needs no token.
    """
    if STATE["port"] is None:
        return None
    hosts = (f"127.0.0.1:{STATE['port']}", f"localhost:{STATE['port']}")
    if headers.get("host") not in hosts:
        return "host"
    if "origin" in headers and headers["origin"] not in [f"http://{h}" for h in hosts]:
        return "origin"
    if method == "GET" and path in OPEN:
        return None
    sent = headers.get(uitoken.HEADER.lower(), "")
    return None if secrets.compare_digest(sent.encode(), STATE["token"].encode()) else "token"


def install(app: FastAPI) -> None:
    """Put the gate in front of every route of `app`, armed when `serve` started this process."""
    if os.environ.get(ENV):
        arm(int(os.environ[ENV]))

    @app.middleware("http")
    async def gate(request: Request, call_next: object) -> Response:
        """403 with the reason's one word, or the route's own answer."""
        why = refusal(request.method, request.url.path, dict(request.headers))
        if why:
            return JSONResponse({"error": f"petición rechazada: {why}"}, status_code=403)
        return await call_next(request)
