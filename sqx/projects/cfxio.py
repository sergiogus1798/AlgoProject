"""The one door for rewriting a project.cfx: refuse while an install holds it, replace atomically.

SQX rewrites a project.cfx on save and exit, so a patch applied while an install is up (or
booting, or shutting down) is silently lost — hard rule 4. And a writer killed halfway through
`ZipFile(cfx, "w")` leaves a truncated project with no backup, so the zip is written beside the
file and moved over it.
"""

import os
import zipfile
from pathlib import Path

from core.paths import WORKERS
from core.worker import holding, installs, listening


def _installs() -> dict[str, tuple[Path, int | None]]:
    """Role to (install folder, port), the master included (it has no known port)."""
    return {
        role: (p.resolve(), WORKERS.get(role, {}).get("port"))
        for role, p in installs().items()
    }


def members(cfx: Path) -> dict[str, bytes]:
    """Every member of a project.cfx (or any zip), name to bytes, in archive order."""
    with zipfile.ZipFile(cfx) as z:
        return {n: z.read(n) for n in z.namelist()}


def held(cfx: Path) -> str | None:
    """The role whose install holds this file, when that install is up or starting.

    Args:
        cfx: Path of a project.cfx; relative and symlinked paths are resolved.

    Returns:
        Role (`master`, `conductor`, `custodian`) when the file lives inside that install and
        its port answers or a process runs from it — a JVM booting or shutting down has no
        port yet it is exactly when SQX rewrites the file. None for a file outside all three.
    """
    path = Path(cfx).resolve()
    for role, (install, port) in _installs().items():
        if install in path.parents and (
            (port is not None and listening(port)) or holding(install)
        ):
            return role
    return None


def write(cfx: Path, members: dict[str, bytes], *, force: bool = False) -> None:
    """Replace a project.cfx with these members, atomically.

    Args:
        cfx: Path of the project.cfx.
        members: Member name to bytes, written in this order, deflated.
        force: Skip the held-by-an-install refusal.

    Raises:
        SystemExit: An install holds the file (hard rule 4).
    """
    role = None if force else held(cfx)
    if role:
        raise SystemExit(
            f"el {role} tiene este proyecto abierto y reescribe el .cfx al salir. "
            f"Páralo: bin/sqx-worker.sh --role {role} stop"
        )
    cfx = Path(cfx)
    tmp = cfx.with_suffix(cfx.suffix + ".tmp")
    try:
        with open(tmp, "wb") as f:
            with zipfile.ZipFile(f, "w", zipfile.ZIP_DEFLATED) as z:
                for name, blob in members.items():
                    z.writestr(name, blob)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, cfx)
    finally:
        tmp.unlink(missing_ok=True)  # gone already after the replace
