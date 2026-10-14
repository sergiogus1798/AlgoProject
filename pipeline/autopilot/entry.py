"""What a new autopilot run settles before it starts: alone on its worker, on a session of its own."""

import fcntl
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager

from core import worker
from core.paths import WORKERS
from core.researchpaths import autopilot_runs
from sqx.projects import live

HELD = []  # the open lock files: a flock lasts while its file is open, so as long as this process


def alone(role: str) -> None:
    """Take the worker's autopilot lock for the life of this process, or exit saying who is there.

    `role`: the project's worker. Two refusals `advance.busy` does not make (2026-10-13): a second autopilot on the same
    worker — both would read one log and the first `finally` would stop the session under the
    other — and a GUI session already up. `busy` lets this holder's own session through, which
    whoever continues a live session between its steps needs; a NEW run adopting one plans
    from disk while memory holds more, and stops at its end a session it did not start. The
    holder is «owner» for two terminals, cron and the window alike, so it tells nobody apart.
    """
    autopilot_runs().mkdir(parents=True, exist_ok=True)
    lock = (autopilot_runs() / f"{role}.lock").open("w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        sys.exit(f"ya hay un autopiloto en el {role}: uno por worker, este no arranca")
    HELD.append(lock)
    if live.gui_up(role):
        held = worker.lock(WORKERS[role]["path"]) or {}
        sys.exit(
            f"el {role} ya tiene una sesión GUI arriba que este run no arrancó (la tiene "
            f"{held.get('holder', '?')} desde {held.get('since', '?')}, PID "
            f"{held.get('pid', '?')}): un autopiloto nuevo no la adopta. Si es de un run "
            "muerto, el dueño decide cómo cerrarla; no se ha tocado nada"
        )


def unstarted(role: str, failed: BaseException) -> str:
    """estado.txt's line for a `live.start` that failed: its own words, and what is left up."""
    said = str(failed).splitlines()[0] if str(failed) else type(failed).__name__
    left = (
        f" — la sesión GUI del {role} SIGUE ARRIBA con la memoria incompleta: no la pares con "
        "un `stop` normal (su exitapp sincroniza al salir y borraría del disco lo que no "
        "llegó a cargarse, regla 1): `live.start` la mata por PID y aquí no lo logró"
        if live.gui_up(role)
        else ""
    )
    return f"FALLO en el arranque de la sesión GUI: {said}{left}"


@contextmanager
def told(tell: Callable[[str], None]) -> Iterator[None]:
    """The closing sync, export and stop: a failure there is written to `estado.txt` too.

    Without it a failed export after the last action left the run with neither FIN nor FALLO
    (reviewed 2026-10-13); the session is stopped by then, `liverun.close` sees to it."""
    try:
        yield
    except BaseException as late:
        tell(
            f"FALLO en la parada y export final: {str(late).splitlines()[0] if str(late) else repr(late)}"
        )
        raise
