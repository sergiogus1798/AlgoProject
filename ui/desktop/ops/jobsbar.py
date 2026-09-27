"""The status-bar strip of jobs: what runs, how far, what waits, and a cancel for each."""

import httpx
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from ui.desktop import client
from ui.desktop.theme import C, MONO, T

POLL_MS = 2000
SHOWN = 5                   # chips beyond this collapse into «+N»


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
        `study · 45% · state`, or `en cola #2` for a waiting one.
    """
    name = job.get("study") or job["label"]
    if waiting(job):
        return f"{name} · en cola #{job['queued']}"
    percent = job.get("percent")
    parts = [name, f"{percent}%" if percent is not None else "…", job.get("state") or ""]
    return " · ".join(p for p in parts if p)


class JobsBar(QWidget):
    """A thin strip for the window's status bar, fed by `/api/jobs` every two seconds."""

    def __init__(self) -> None:
        """Build the empty strip and start polling."""
        super().__init__()
        self.lay = QHBoxLayout(self)
        self.lay.setContentsMargins(6, 0, 6, 0)
        self.lay.setSpacing(6)
        self.setStyleSheet(f"font-family: {MONO}; font-size: 12px;")
        self.poll = QTimer(self)
        self.poll.setInterval(POLL_MS)
        self.poll.timeout.connect(self.refresh)
        self.poll.start()
        self.show_jobs([])

    def refresh(self) -> None:
        """Read the job list, or say the daemon is not answering."""
        try:
            self.show_jobs(client.get("jobs")["jobs"])
        except httpx.HTTPError as down:
            self.show_message(f"demonio no responde: {type(down).__name__}", C["dead"])

    def clear(self) -> None:
        """Remove every widget of the strip."""
        while self.lay.count():
            item = self.lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def show_message(self, text: str, colour: str) -> None:
        """Replace the strip with one sentence.

        Args:
            text: What to say.
            colour: Its colour.
        """
        self.clear()
        self.lay.addWidget(QLabel(text, styleSheet=f"color: {colour};"))
        self.lay.addStretch(1)

    def show_jobs(self, jobs: list[dict]) -> None:
        """Redraw the strip.

        Args:
            jobs: `/api/jobs` records, oldest first. Finished ones (`rc` set) are counted,
                not shown: the job zone keeps their logs.
        """
        self.clear()
        live = [j for j in jobs if j.get("rc") is None]
        running = [j for j in live if not waiting(j)]
        queued = sorted((j for j in live if waiting(j)), key=lambda j: j["queued"])
        failed = sum(1 for j in jobs if j.get("rc") not in (None, 0))
        self.lay.addWidget(QLabel("TRABAJOS", styleSheet=f"color: {T['faint']}; "
                                                          "font-weight: 700;"))
        head = f"{len(running)} en marcha · {len(queued)} en cola"
        self.lay.addWidget(QLabel(head, styleSheet=f"color: {T['text']};"))
        for job in (running + queued)[:SHOWN]:
            self.lay.addWidget(self.chip(job))
        if len(live) > SHOWN:
            self.lay.addWidget(QLabel(f"+{len(live) - SHOWN}"))
        self.lay.addStretch(1)
        if failed:
            self.lay.addWidget(QLabel(f"{failed} terminaron con error",
                                      styleSheet=f"color: {C['dead']};"))

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
        text = QLabel(chip_text(job), styleSheet=f"color: {colour}; border: 1px solid "
                                                  f"{colour}; border-radius: 3px; padding: 1px 6px;")
        text.setToolTip(f"{job['label']} · {job.get('lane') or 'python'} · empezó "
                        f"{job['started']}\n{job.get('project') or ''} "
                        f"{job.get('databank') or ''}\n" + "\n".join(job.get("tail", [])[-4:]))
        stop = QPushButton("✕", toolTip="Cancelar este trabajo", fixedWidth=24,
                           styleSheet="padding: 0;")
        stop.clicked.connect(lambda: self.cancel(job["id"]))
        row.addWidget(text)
        row.addWidget(stop)
        return box

    def cancel(self, job_id: str) -> None:
        """Ask the daemon to cancel one job, then redraw.

        Args:
            job_id: Its `id`.
        """
        try:
            ok = client.post(f"jobs/{job_id}/cancel", {}).get("ok")
        except httpx.HTTPError as refused:
            self.show_message(f"no se pudo cancelar {job_id}: {refused}", C["dead"])
            return
        if not ok:
            self.show_message(f"el demonio no canceló {job_id}", C["weak"])
            return
        self.refresh()
