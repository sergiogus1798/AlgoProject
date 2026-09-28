"""The daemon's HTTP surface: everything the window knows, it asks for here.

This file holds the app and `/api/health`; every other route lives in a router listed in
`routers.py` (the library's own in `templates.py`).
"""

import os

from fastapi import FastAPI

from ui.daemon import jobs, progress, version
from ui.daemon.routers import ROUTERS

APP = FastAPI(title="AlgoDaemon", docs_url=None, redoc_url=None)
# Taken once at import: the code this process is actually running, not what is on disk now.
CODE = version.fingerprint()
for router in ROUTERS:
    APP.include_router(router)


@APP.get("/api/health")
def health() -> dict[str, object]:
    """Whether the daemon is up and what it is serving.

    Returns:
        A fixed marker the window polls on startup to know the daemon has bound its port,
        plus the code it serves, its pid and how many jobs it runs — what the launcher
        needs to replace a daemon left over from older code without killing a job — and
        `sqx.installs`, role → whether its folder exists here. None existing is the
        read-only mode: the window then disables what reaches SQX (encargo 22 §11).
    """
    busy = sum(j["rc"] is None for j in jobs.listing())
    installs = {role: top.is_dir() for role, top in progress.installs().items()}
    return {"ok": True, "module": "templates", "code": CODE, "pid": os.getpid(), "busy": busy,
            "sqx": {"installs": installs}}
