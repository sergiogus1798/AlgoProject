"""The ui daemon's session token: minted by `ui.daemon.serve`, kept in a 0600 file under the data root, read by every client."""

import os
import secrets
from pathlib import Path

from core.paths import DATA

FOLDER = DATA / "ui"
HEADER = "X-Algo-Token"


def path(port: int) -> Path:
    """Where the daemon on `port` keeps its token: one file per port, so a scratch daemon
    never replaces the token of the owner's."""
    return FOLDER / f"token-{port}"


def mint(port: int) -> str:
    """Write a fresh token for the daemon on `port` and return it.

    Called by `serve` only, and only once it holds the port: whoever can read the owner's
    files can read this one (mode 0600), and nobody else — a web page cannot.
    """
    token = secrets.token_urlsafe(32)
    FOLDER.mkdir(parents=True, exist_ok=True)
    fresh = path(port).with_suffix(".new")
    with os.fdopen(
        os.open(fresh, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w"
    ) as f:
        f.write(token)
    os.chmod(fresh, 0o600)  # a file left over from a crash keeps the mode it had
    os.replace(fresh, path(port))  # a reader never sees it half-written
    return token


def read(port: int) -> str:
    """The token of the daemon on `port`, or "" when no daemon has ever served there."""
    try:
        return path(port).read_text(encoding="utf-8").strip()
    except OSError:
        return ""
