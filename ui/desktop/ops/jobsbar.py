"""The status-bar strip of jobs: what runs, a 0-100 % bar for each, what waits, and a cancel."""


from typing import Any
import time

import httpx
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton, QSizePolicy, QWidget

from ui.desktop import background, client, jobsfeed
from ui.desktop.durations import share
from ui.text.numbers import num
from ui.desktop.ops.progressbar import bar
from ui.desktop.theme import C, MONO, T, clear

POLL_MS = 2000
SQX_EVERY = 8               # the SQX runs are read every 8th poll (16 s): each read may ask a
#                             running worker for its status line, and a task moves slowly
SHOWN = 4                   # chips beyond this collapse into «+N»
BAR_PX = 64
ROLE = {"custodian": "custodio", "conductor": "conductor"}
SQX_JOBS = ("launch", "advance", "crear proyecto", "crear plantilla")   # ✕ asks before these


def waiting(job: dict) -> bool:
    """Whether a job is still in the queue rather than running.

    Args:
        job: One `/api/jobs` record; `queued` may be absent on a daemon without the queue.

    Returns:
        True when it has a queue position.
    """
    return job.get("queued") not in (None, 0, False)


def chip_text(job: dict) -> str:
    """What one job's chip says.

    Args:
        job: One `/api/jobs` record, with or without `percent`, `state`, `study`, `lane`.

    Returns:
        `study · state` (the percentage is the chip's bar), or `en cola #2` for a waiting one.
    """
    name = job.get("study") or job["label"]
    if waiting(job):
        return f"{name} · en cola #{job['queued']}"
    return f"{name} · {job.get('state') or '…'}" if job.get("state") else name


def sqx_text(run: dict) -> str:
    """What one SQX run's chip says.

    Args:
        run: One `/api/ops/sqx` record.

    Returns:
        `SQX custodio · MCR 3 Slippage · 7 / 20`, the count only when the worker gave one.
    """
    count = (f" · {num(run['done'])} / {num(run['total']) if run['total'] else '·'}"
             if run.get("done") is not None else "")
    return f"SQX {ROLE.get(run['role'], run['role'])} · {run.get('task') or '…'}{count}"


class JobsBar(QWidget):
    """A thin strip for the window's status bar, fed by `/api/jobs` every two seconds."""

    def __init__(self) -> None:
        """Build the empty strip and start polling."""
        super().__init__()
        self.lay = QHBoxLayout(self)
        self.lay.setContentsMargins(6, 0, 6, 0)
        self.lay.setSpacing(6)
        self.setStyleSheet(f"font-family: {MONO}; font-size: 12px;")  # never widens the window:
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)  # 4 long chips made it 3.8k px
        self.poll = QTimer(self)
        self.poll.timeout.connect(self.refresh)
        self.poll.start(POLL_MS)
        self.sqx: list[dict] = []           # the SQX runs as last read
        self.last: list | None = None       # the job list last drawn
        self.ticks = 0
        self.show_jobs([])

    def refresh(self) -> None:
        """Read the job list (and every few polls the SQX runs) off the GUI thread for `landed`."""
        sqx = self.ticks % SQX_EVERY == 0
        self.ticks += 1

        def read() -> dict[str, Any]:
            """Both reads, on the pool's thread."""
            return {"at": time.monotonic(), "jobs": client.get("jobs")["jobs"],
                    "sqx": client.get("ops/sqx")["runs"] if sqx else None}
        background.run(read, self.landed, key=f"jobsbar:{id(self)}")

    def landed(self, got: dict) -> None:
        """Redraw from the daemon's answer, or say it is down."""
        if "error" in got:
            self.show_message("demonio no responde", C["dead"])
            self.last = None
            return
        jobsfeed.store({"jobs": got["jobs"]}, got["at"])
        moved = got["sqx"] is not None and got["sqx"] != self.sqx
        if got["sqx"] is not None:
            self.sqx = got["sqx"]
        if got["jobs"] == self.last and not moved:
            return                          # nothing moved: no rebuild of the strip every 2 s
        self.last = got["jobs"]
        self.show_jobs(got["jobs"])

    def show_message(self, text: str, colour: str) -> None:
        """Replace the strip with one sentence.

        Args:
            text: What to say.
            colour: Its colour.
        """
        clear(self.lay)
        self.lay.addWidget(QLabel(text, styleSheet=f"color: {colour};"))  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        self.lay.addStretch(1)

    def show_jobs(self, jobs: list[dict]) -> None:
        """Redraw the strip.

        Args:
            jobs: `/api/jobs` records, oldest first. Finished ones (`rc` set) are counted,
                not shown: the job zone keeps their logs.
        """
        clear(self.lay)
        live = [j for j in jobs if j.get("rc") is None]
        # The furthest first: a job that prints no PROGRESS sits at 0 % until it ends, and
        # four of those must not hide the one whose bar moves.
        running = sorted((j for j in live if not waiting(j)),
                         key=lambda j: -(j.get("percent") or 0))
        queued = sorted((j for j in live if waiting(j)), key=lambda j: j["queued"])
        # §4.3/§16 (owner, 2026-09-30): «un trabajo terminó con error» said nothing about which
        # one or why. Newest first, since that is the one the owner just watched fail.
        failed = sorted((j for j in jobs if j.get("rc") not in (None, 0)),
                        key=lambda j: j["started"], reverse=True)
        self.lay.addWidget(QLabel("Trabajos", styleSheet=f"color: {T['faint']}; "  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
                                                          "font-weight: 700;"))
        head = f"{num(len(running) + len(self.sqx))} en marcha · {num(len(queued))} en cola"
        self.lay.addWidget(QLabel(head, styleSheet=f"color: {T['text']};"))  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        for run in self.sqx:
            self.lay.addWidget(self.sqx_chip(run))
        for job in (running + queued)[:SHOWN]:
            self.lay.addWidget(self.chip(job))
        if len(live) > SHOWN:
            self.lay.addWidget(QLabel(f"+{num(len(live) - SHOWN)}"))
        self.lay.addStretch(1)
        for job in failed[:SHOWN]:
            self.lay.addWidget(self.failed_chip(job))
        if len(failed) > SHOWN:
            self.lay.addWidget(QLabel(f"+{num(len(failed) - SHOWN)} más con error",  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
                                      styleSheet=f"color: {C['dead']};"))

    def failed_chip(self, job: dict) -> QWidget:
        """One failed job on the strip itself: study, asset/market and why (§4.3/§16).

        Args:
            job: One `/api/jobs` record with `rc` not in (None, 0).

        Returns:
            The chip.
        """
        where = job.get("asset") or job.get("databank") or ""
        why = next((t for t in reversed(job.get("tail") or []) if t.strip()), job.get("state", ""))
        head = f"{job.get('study') or job['label']}" + (f" · {where}" if where else "")
        text = QLabel(f"⚠ {head}: {why}"[:60], styleSheet=f"color: {C['dead']}; border: 1px "  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
                     f"solid {C['dead']}; border-radius: 3px; padding: 1px 6px;")
        text.setToolTip(f"{job['label']} · {job.get('lane') or 'python'} · {job.get('state', '')}"
                        f"\n{job.get('project') or ''} {where}\n"
                        + "\n".join(job.get("tail", [])[-8:]))
        return text

    def chip(self, job: dict) -> QWidget:
        """One job: its text, coloured by lane state, and its cancel button.

        Args:
            job: One live `/api/jobs` record.

        Returns:
            The chip.
        """
        box = QWidget()
        row = QHBoxLayout(box)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(2)
        colour = C["pending"] if waiting(job) else C["accent"]
        text = QLabel(chip_text(job), styleSheet=f"color: {colour}; border: 1px solid "  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
                                                  f"{colour}; border-radius: 3px; padding: 1px 6px;")
        text.setToolTip(f"{job['label']} · {job.get('lane') or 'python'} · empezó "
                        f"{job['started']}\n{job.get('project') or ''} "
                        f"{job.get('databank') or ''}\n" + "\n".join(job.get("tail", [])[-4:]))
        stop = QPushButton("✕", toolTip="Cancelar este trabajo", fixedWidth=24,  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
                           styleSheet="padding: 0;")
        stop.clicked.connect(lambda: self.cancel(job["id"], job["label"]))
        row.addWidget(text)
        if not waiting(job):
            progress = bar(job.get("percent"), BAR_PX, colour)
            progress.setToolTip("Avance del trabajo: la última línea «PROGRESS <0-100>» que "
                                "imprimió; 100 % al acabar bien.")
            row.addWidget(progress)
        row.addWidget(stop)
        return box

    def sqx_chip(self, run: dict) -> QWidget:
        """One SQX run on a worker: its task, count and bar. No ✕: the window never stops SQX.

        Args:
            run: One `/api/ops/sqx` record.

        Returns:
            The chip.
        """
        box = QWidget()
        row = QHBoxLayout(box)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(2)
        colour = C["weak"]
        text = QLabel(sqx_text(run), styleSheet=f"color: {colour}; border: 1px solid "  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
                                                 f"{colour}; border-radius: 3px; padding: 1px 6px;")
        text.setToolTip(f"{run['project']} en el {ROLE.get(run['role'], run['role'])}: la tarea "
                        "que su log da por empezada. El avance es el que SQX escribe en su log, "
                        "o hechas ÷ total del estado del worker. Detalle en «En marcha».")
        row.addWidget(text)
        row.addWidget(bar(share(run.get("done"), run.get("total"), run.get("percent")),
                          BAR_PX, colour))
        return box

    def cancel(self, job_id: str, label: str = "") -> None:
        """Ask the daemon to cancel one job, then redraw.

        Args:
            job_id: Its `id`.
            label: Its `label`. A job that drives SQX asks first: one click stopped a
                custodian hours into an MC Retest (📓 2026-09-29).
        """
        if label in SQX_JOBS and QMessageBox.question(  # pyright: ignore[reportCallIssue]  # PySide6 stub wants button0/button1 for the 3-arg form
                self, "Cancelar", "Este trabajo maneja SQX: cancelarlo para el worker a media "
                "tarea, y lo que no se haya guardado se pierde. ¿Cancelar?") != QMessageBox.StandardButton.Yes:
            return
        try:
            ok = client.post(f"jobs/{job_id}/cancel", {}).get("ok")
        except httpx.HTTPError as refused:
            self.show_message(f"no se pudo cancelar {job_id}: {refused}", C["dead"])
            return
        if not ok:
            self.show_message(f"el demonio no canceló {job_id}", C["weak"])
            return
        self.refresh()
