"""The operation zone: /api/pulse, /api/ops/sqx and /api/ledger read-only, and its widgets offscreen."""

import os
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from PySide6.QtWidgets import QApplication

from core.paths import ROOT
from ui.daemon.ops import api, pulse, runs
from ui.desktop.durations import share

SHOTS = ROOT / "scratch" / "ui-plan" / "shots"
PULSE_KEYS = {"up", "project", "done", "total", "rate_per_min", "eta_min", "jvm_gb", "xmx_gb",
              "cpu_pct", "free_gb", "fits_more", "line", "warn"}


def http() -> TestClient:
    """A local app holding only the operation router; never the real daemon, never 8765."""
    app = FastAPI()
    app.include_router(api.ROUTER)
    return TestClient(app)


def fake_install(tmp: Path, done: int, total: int) -> Path:
    """An install folder, a job log and today's SQX log, as a running custodian leaves them."""
    install = tmp / "SQX_w2"
    log = install / "user" / "log" / "StrategyQuant"
    log.mkdir(parents=True)
    (install / "sqcli.config").write_text("option -Xms1g\noption -Xmx80g\n")
    start = datetime.now().replace(microsecond=0)
    started = start.replace(hour=max(0, start.hour - 1))
    (log / f"log_{start:%Y_%m_%d}.log").write_text(
        "header\n" + f"{started:%H:%M:%S}.000 [x] INFO  c.s.t.project.ProjectEngine - "
                     "Starting project 'Test_pulse'\n")
    (tmp / "jobs").mkdir()
    (tmp / "jobs" / "20260926-1-variants.log").write_text(
        f"PROGRESS 5 cargando\nPROGRESS 40 {done} de {total} reteseadas\n")
    return install


@contextmanager
def running(done: int, total: int) -> Iterator[None]:
    """The pulse module pointed at a fake custodian whose ./sqcli is this very process."""
    with tempfile.TemporaryDirectory() as tmp:
        install = fake_install(Path(tmp), done, total)
        with mock.patch.object(pulse, "WORKERS", {"custodian": {"path": install, "port": 0}}), \
                mock.patch.object(pulse.worker, "holding", lambda _: [os.getpid()]), \
                mock.patch.object(pulse, "LOGS", Path(tmp) / "jobs"), \
                mock.patch.object(pulse, "free_gb", lambda: 12.0):
            pulse.READINGS.clear()
            yield


def test_pulse_route_answers_whatever_the_custodian_is_doing() -> None:
    """The real reading: up or down, the block has every field and one line."""
    got = http().get("/api/pulse").json()["custodian"]
    assert PULSE_KEYS <= set(got)
    assert got["free_gb"] > 0 and isinstance(got["line"], str)


def test_pulse_up_reads_proc_and_logs() -> None:
    """With this test process standing in for ./sqcli, every figure comes out and warns."""
    with running(3987, 15000):
        p = pulse.custodian()
    assert p["up"] and p["project"] == "Test_pulse" and p["xmx_gb"] == 80
    assert (p["done"], p["total"]) == (3987, 15000) and p["rate_per_min"] > 0
    assert p["jvm_gb"] > 0 and p["cpu_pct"] >= 0 and not p["slope_measured"]
    assert " 3 987 de 15 000 | JVM " in p["line"] and "libre 12 GB" in p["line"]
    assert any("por debajo de 15 GB" in w for w in p["warn"])
    assert any("faltan 11013" in w for w in p["warn"])     # 12 GB at 10 MB fits ~1228


def test_slope_is_measured_once_the_run_has_moved() -> None:
    """Two readings 1,000 backtests apart and 10 GB apart give ~10 MB per backtest."""
    pulse.READINGS.clear()
    pulse.slope_mb("P", 1000, 20.0)
    slope, measured = pulse.slope_mb("P", 2000, 30.0)
    assert measured and abs(slope - 10.24) < 1e-9
    assert pulse.slope_mb("Q", None, 5.0) == (pulse.SLOPE_MB, False)


def test_runs_say_nothing_unless_a_project_runs() -> None:
    """A worker down, a finished run and a retired project give None; a running task counts."""
    workers = {"custodian": {"path": Path("/nowhere"), "port": 0}}
    started = ["10:00:00.000 x ProjectEngine - Starting project 'Test_X'",
               "10:00:01.000 x ProgressEngine - MCR 3 : Loading backtest data"]
    live = {"run": {"percent": None}, "tasks": [
        {"status": "done", "title": "MCR 1"},
        {"status": "running", "title": "MCR 3", "done": 7, "total": 20}]}
    with mock.patch.object(runs, "WORKERS", workers), \
            mock.patch.object(runs.progress, "projects", lambda _: ["Test_X"]), \
            mock.patch.object(runs.progress, "state", lambda r, p: live):
        with mock.patch.object(runs.worker, "holding", lambda _: []):
            assert runs.running("custodian") is None and runs.runs() == []
        with mock.patch.object(runs.worker, "holding", lambda _: [1]):
            ended = started + ["10:05:00.000 x ProgressEngine - Project finished"]
            with mock.patch.object(runs.progress, "log_lines", lambda _: (ended, 0.0)):
                assert runs.running("custodian") is None
            with mock.patch.object(runs.progress, "log_lines", lambda _: (started, 0.0)):
                got = runs.running("custodian")
                assert (got["project"], got["task"], got["done"], got["total"],
                        got["percent"]) == ("Test_X", "MCR 3", 7, 20, 35)
                with mock.patch.object(runs.progress, "projects", lambda _: []):
                    assert runs.count("custodian", "Test_X") is None
                    assert runs.running("custodian")["done"] is None


def test_pulse_counts_an_outside_run_by_its_task() -> None:
    """No job log with PROGRESS: the worker's task count shows, without rate or ETA."""
    with running(0, 0):
        with mock.patch.object(pulse, "job_progress", lambda *_: None), \
                mock.patch.object(pulse.runs, "count",
                                  lambda r, p: {"task": "MCR 3", "done": 1234, "total": 5000,
                                                "percent": 25}):
            p = pulse.custodian()
        assert (p["done"], p["total"]) == (1234, 5000)
        assert p["rate_per_min"] is None and p["eta_min"] is None
        assert p["progress_from"] == "estado del custodio · MCR 3"
        assert " 1 234 de 5 000 | JVM " in p["line"]
        with mock.patch.object(pulse, "job_progress", lambda *_: None), \
                mock.patch.object(pulse.runs, "count",
                                  lambda r, p: {"task": "Build", "done": 1400, "total": None,
                                                "percent": None}):
            p = pulse.custodian()
        assert " 1 400 hechos | JVM " in p["line"] and p["eta_min"] is None


def test_share() -> None:
    """SQX's own percent wins; else done over total, capped; no total means no figure."""
    assert share(7, 20) == 35 and share(7, 20, 60) == 60 and share(30, 20) == 100
    assert share(None, 20) is None and share(140, None) is None and share(5, 0) is None


def test_ledger_route_over_the_real_ledger() -> None:
    """Every study answers with rows, a funnel and the history spent; an unknown one is refused."""
    client = http()
    first = client.get("/api/ledger").json()
    assert first["study"] in first["studies"]
    for study in first["studies"]:
        got = client.get("/api/ledger", params={"study": study}).json()
        assert len(got["funnel"]) == len(got["rows"]) > 0
        assert {"segments", "virgin", "blind", "trials"} <= set(got["spent"])
    assert "error" in client.get("/api/ledger", params={"study": "nope"}).json()


def test_widgets_paint_offscreen() -> None:
    """The three widgets draw real and fake readings; the grabs land in scratch for a look."""
    from ui.desktop.theme import QSS
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(QSS)
    client = http()
    from PySide6.QtWidgets import QLabel, QProgressBar, QPushButton
    from ui.desktop.ops.jobsbar import JobsBar, sqx_text
    from ui.desktop.ops.ledger import Ledger
    from ui.desktop.ops.pulse import Pulse
    SHOTS.mkdir(parents=True, exist_ok=True)
    bar = JobsBar()
    bar.poll.stop()
    bar.show_jobs([
        {"id": "1", "label": "profitShape", "study": "profitShape", "percent": 45,
         "state": "bootstrap", "lane": "python", "started": "21:00:00", "rc": None, "tail": []},
        {"id": "2", "label": "cscv", "started": "21:00:05", "rc": None, "tail": []},
        {"id": "3", "label": "gate", "study": "gate", "queued": 1, "started": "21:00:09",
         "rc": None, "tail": []},
        {"id": "0", "label": "wfc", "started": "20:00:00", "rc": 1, "tail": []}])
    bar.sqx = [{"role": "custodian", "project": "Test_X", "task": "MCR 3", "done": 7,
                "total": 20, "percent": 35}]
    chip = bar.sqx_chip(bar.sqx[0])
    progress = chip.findChild(QProgressBar)
    assert progress.value() == 35 and chip.findChild(QPushButton) is None   # no ✕ for SQX
    assert sqx_text(bar.sqx[0]) == "SQX custodio · MCR 3 · 7 / 20"
    build = bar.sqx_chip({"role": "conductor", "project": "P", "task": "Build", "done": 9,
                          "total": None, "percent": None})
    assert build.findChild(QProgressBar).maximum() == 0                   # busy, no figure
    bar.show_jobs([])
    assert any("1 en marcha" in w.text() for w in bar.findChildren(QLabel))
    bar.resize(1100, 34)
    assert bar.grab().save(str(SHOTS / "D-jobsbar.png"))

    view = Pulse()
    view.poll.stop()
    view.show_pulse(client.get("/api/pulse").json()["custodian"])
    with running(3987, 15000):
        view.show_pulse(pulse.custodian())
    assert view.history.count() == 2
    view.resize(1100, 560)
    assert view.grab().save(str(SHOTS / "D-pulse.png"))

    book = Ledger()
    book.show_ledger(client.get("/api/ledger", params={"study": "USDJPY_H1_crossAboveHMA_v1"})
                     .json())
    book.resize(1200, 700)
    assert book.tabs.count() == 3
    assert book.grab().save(str(SHOTS / "D-ledger.png"))
    book.tabs.setCurrentIndex(1)
    assert book.grab().save(str(SHOTS / "D-ledger-spent.png"))


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
            print(f"ok  {name}")
