"""One POST to a GUI session's `/project` servlet, with the port and token SQX wrote to settings.xml."""

import contextlib
import json
import os
import signal
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from core import worker
from core.paths import WORKERS
from core.xmlget import rx


def _file(role: str) -> Path:
    """The install's settings.xml."""
    return WORKERS[role]["path"] / "user/settings/settings.xml"


@lru_cache(maxsize=8)
def _settings(role: str, mtime_ns: int) -> str:
    """The install's settings.xml as of one modification time (SQX rewrites it at every GUI start)."""
    return _file(role).read_text(encoding="utf-8")


def _setting(role: str, key: str) -> str:
    """One value SQX wrote to the install's settings.xml (port and token: at every GUI start)."""
    return rx(
        rf"<{key}>([^<]*)", _settings(role, _file(role).stat().st_mtime_ns)
    ).group(1)


def call(role: str, action: str, **params: str) -> dict[str, Any]:
    """POST one /project/<action>; SystemExit with SQX's own words on an `error` answer."""
    port, token = _setting(role, "WebServerPortUsed"), _setting(role, "BrowserToken")
    got = json.loads(worker.post(port, token, action, params))
    if "error" in got:
        raise SystemExit(f"SQX /project/{action}: {got['error']}")
    return got


def kill(role: str) -> None:
    """End a session whose databanks did not finish loading: by PID, never asked to exit.

    Owner, 2026-10-13: `exitapp` would save that half-loaded memory over the files (hard rule
    1), and there is nothing to lose — what did load is on disk. Only for that case: a session
    that ran anything holds work a kill drops (`exiting.stop` is the one for those).
    """
    top = WORKERS[role]["path"]
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid in worker.holding(top):
            with contextlib.suppress(ProcessLookupError):
                os.kill(pid, sig)
        for _ in range(30):
            if not worker.holding(top):
                break
            time.sleep(1)
    if not worker.holding(top):
        worker.stop(
            role, export=False
        )  # nothing runs: the script only clears its lock and Xvfb
