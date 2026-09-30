"""The rail's watch over its project's jobs: polled off the GUI thread, repaints grouped."""

import time

from PySide6.QtWidgets import QWidget

from ui.desktop import background
from ui.desktop.theme import C
from ui.text.numbers import num

POLL_MS = 3000
# While a batch runs, what its ended jobs changed is repainted at most this often, and once
# more when the last one ends: each repaint reads the panel, the funnel and the rail again.
# 🔬 2026-09-28: one repaint per ended job, 16 per poll, froze the window for a minute.
REPAINT_S = 20


def poll(rail: QWidget) -> None:
    """Ask for the job list off the GUI thread; `polled` reads it.

    Args:
        rail: The `Rail` (its `project`, `timer`, `live`, `ended`, `painted`, `said`).
    """
    rail.timer.stop()                     # restarted by `polled`: never two asks in flight
    project = rail.project
    background.get("jobs", lambda got: polled(rail, project, got),
                   key=f"railjobs:{id(rail)}", owner=rail)


def polled(rail: QWidget, project: str, got: dict) -> None:
    """Gather the jobs that ended; repaint what they changed at most every REPAINT_S while
    others run, and once when none is left — one `finished` per repaint, not per job.

    Args:
        rail: The `Rail`.
        project: The project the list was asked for; another one on screen now drops it.
        got: GET /api/jobs's answer, or `{"error": …}`.
    """
    if project != rail.project:
        return
    if "error" in got:
        if rail.live and rail.isVisible():
            rail.timer.start(POLL_MS)
        return
    mine = {j["id"]: j for j in got["jobs"] if j.get("project") == rail.project}
    rail.ended += [j for i, j in mine.items() if i in rail.live and j["rc"] is not None]
    rail.live = {i: j for i, j in mine.items() if j["rc"] is None}
    if rail.ended and (not rail.live or time.monotonic() - rail.painted >= REPAINT_S):
        repaint(rail)
    elif rail.live:
        done = sum(j.get("percent", 0) for j in rail.live.values()) / len(rail.live)
        rail.said.setText(f"{num(len(rail.live))} en marcha ({done:.0f}% de media)"
                          + (f", {num(len(rail.ended))} terminados desde la última "
                             "recarga" if rail.ended else ""))
    if rail.live and rail.isVisible():
        rail.timer.start(POLL_MS)


def repaint(rail: QWidget) -> None:
    """Reload the rail and emit one `finished` for the jobs gathered since the last repaint.

    Args:
        rail: The `Rail`; `finished(study, databank)` carries the study and databank the
            jobs share, '' for either when they do not (every databank is read again).
    """
    ended, rail.ended, rail.painted = rail.ended, [], time.monotonic()
    banks = {j.get("databank") or "" for j in ended}
    studies = {j["study"] for j in ended}
    rail.finished.emit(studies.pop() if len(studies) == 1 else "",
                       banks.pop() if len(banks) == 1 else "")
    rail.load(rail.project)
    failed = [j["label"] for j in ended if j["rc"] != 0]
    left = [j["state"].split(" · ⚠ ")[-1] for j in ended if "sigue arrancado" in j["state"]]
    rail.said.setText(f"{num(len(ended))} terminados, {num(len(rail.live))} en marcha"
                      + (f"   ·   fallaron: {', '.join(failed)} (ver Trabajos)"
                         if failed else "") + "".join(f"   ·   ⚠ {w}" for w in left))
    rail.said.setStyleSheet(f"color: {C['dead']};" if left else "")
