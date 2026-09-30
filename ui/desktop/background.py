"""Daemon calls off the window's thread: the answer lands in a callback on the GUI thread."""

from collections.abc import Callable
from itertools import count

import httpx
import shiboken6
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from ui.desktop import client

# 🔬 2026-09-28, owner's feedback «la UI se congela»: every poll and every reload waited on the
# daemon inside the GUI thread; a batch of 16 studies ending in one poll reloaded the panel
# (≈3 s) and the funnel (0.6 s) once per job — a minute frozen. The window now only paints.
POOL = QThreadPool()
POOL.setMaxThreadCount(4)
_SEQ = count(1)
_LATEST: dict[str, int] = {}


class _Relay(QObject):
    """Lives on the GUI thread for the whole run; a worker's emit is queued onto it."""

    landed = Signal(object, object, object)


def _deliver(done: Callable[[dict], None], got: dict, owner: QObject | None) -> None:
    """Call back on the GUI thread, unless its widget was deleted meanwhile."""
    owner = owner or getattr(done, "__self__", None)
    if not isinstance(owner, QObject) or shiboken6.isValid(owner):
        done(got)


RELAY = _Relay()
RELAY.landed.connect(_deliver)


class _Call(QRunnable):
    """One job for the pool: run `work` there, hand its dict to `done` here."""

    def __init__(self, work: Callable[[], dict], done: Callable[[dict], None], key: str,
                 seq: int, owner: QObject | None) -> None:
        """Keep what to run and where the answer goes."""
        super().__init__()
        self.work, self.done, self.key, self.seq, self.owner = work, done, key, seq, owner

    def run(self) -> None:
        """Worker thread: no widget is touched here, only the daemon."""
        try:
            got = self.work()
        except httpx.HTTPError as failed:
            got = {"error": f"El demonio no respondió: {failed}"}
        # A window closing while a call is out has already deleted the relay: drop the answer.
        if (not self.key or _LATEST.get(self.key) == self.seq) and shiboken6.isValid(RELAY):
            try:
                RELAY.landed.emit(self.done, got, self.owner)
            except RuntimeError:
                pass          # deleted between the check and the emit, at exit only


def run(work: Callable[[], dict], done: Callable[[dict], None], key: str = "",
        owner: QObject | None = None) -> None:
    """Run `work` on the pool and give its answer to `done` on the GUI thread.

    Args:
        work: Only daemon calls (`client.get`/`client.post`) and plain Python: never a widget.
        done: Receives the dict `work` returned, or `{"error": sentence}` when the daemon did
            not answer. A bound method of a deleted widget is not called.
        key: When given, only the newest call under this key answers: a slow old reload
            never paints over a newer one.
        owner: The widget `done` paints; its deletion drops the answer (a bound method's own
            widget counts without it, a lambda needs it).
    """
    seq = next(_SEQ)
    if key:
        _LATEST[key] = seq
    POOL.start(_Call(work, done, key, seq, owner))


def get(path: str, done: Callable[[dict], None], key: str = "", owner: QObject | None = None,
        **params: str) -> None:
    """`client.get` off the GUI thread; see `run`."""
    run(lambda: client.get(path, **params), done, key, owner)


def post(path: str, body: dict, done: Callable[[dict], None], key: str = "",
         owner: QObject | None = None) -> None:
    """`client.post` off the GUI thread; see `run`."""
    run(lambda: client.post(path, body), done, key, owner)
