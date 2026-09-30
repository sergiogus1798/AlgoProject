"""Cancelling a launcher: its worker stopped by itself, or by the daemon only when it started it."""

import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import worker  # noqa: E402
from tests.test_advance import P  # noqa: E402
from ui.daemon import jobs, winddown, workerguard  # noqa: E402
from ui.daemon.launch import chain, run  # noqa: E402


def record(job: dict) -> dict:
    """The daemon's own record of a job `jobs.start` returned."""
    return next(j for j in jobs.JOBS if j["id"] == job["id"])


def deaf_job(marks: Path, marked: bool) -> dict:
    """A `launch` job deaf to SIGTERM; `marked`: it wrote the marker of a worker it started."""
    mark = (f"from ui.daemon import workerguard\nworkerguard.MARKS = pathlib.Path({str(marks)!r})"
            f"\nworkerguard.mark('custodian', {P!r})\n" if marked else "")
    return jobs.start("launch", ["-c", "import pathlib, signal, time\n" + mark
                                 + "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                                 "time.sleep(60)\n"],
                      {"project": P, "role": "custodian"}, lane="conductor")


def test_cancel_winds_down(root: Path) -> None:
    """Cancelling a launcher: SIGTERM, its `finally` runs. One deaf to SIGTERM is killed after
    the grace; the daemon stops the worker only when the job's own marker says it started it —
    never someone else's — keeps the lane busy until that stop ends, and says what is left up."""
    jobs.LOGS, workerguard.MARKS = root / "logs", root / "marks"
    out = root / "finally.txt"
    polite = jobs.start("launch", ["-c", (
        "import signal, time, pathlib\nfrom ui.daemon.launch.run import graceful\n"
        "signal.signal(signal.SIGTERM, graceful)\ntry:\n    time.sleep(60)\nfinally:\n"
        f"    pathlib.Path({str(out)!r}).write_text('stopped')\n")],
        {"project": P, "role": "custodian"}, lane="conductor")
    time.sleep(1.5)
    assert jobs.cancel(polite["id"])
    record(polite)["_down"].join()
    assert out.read_text() == "stopped", "the job's finally must run"
    stopped = []
    winddown.WORKERS = {"custodian": {"path": root}}
    winddown.GRACE_S = 1
    worker.holding = lambda top: [7]            # someone's worker is up all along
    worker.stop = lambda role, **_: (time.sleep(1), stopped.append(role))   # export=False
    other = deaf_job(root / "marks", marked=False)
    time.sleep(1.5)
    assert jobs.cancel(other["id"])
    record(other)["_down"].join()
    assert stopped == [], "a job that started no worker never stops one"
    assert "sigue arrancado" not in next(j for j in jobs.listing() if j["id"] == other["id"])[
        "state"]
    mine = deaf_job(root / "marks", marked=True)
    time.sleep(1.5)
    assert jobs.cancel(mine["id"])
    job = record(mine)
    while job["_proc"].poll() is None:
        time.sleep(0.1)
    assert job["_down"].is_alive() and jobs.public(job)["rc"] is None, "lane busy while stopping"
    job["_down"].join()
    assert stopped == ["custodian"], stopped
    shown = next(j for j in jobs.listing() if j["id"] == mine["id"])
    assert shown["rc"] == jobs.CANCELLED and "sigue arrancado" in shown["state"], shown


def test_cancel_python_and_snapshot(root: Path) -> None:
    """A cancel during a Python step ends the running tests at once and starts no queued one;
    a snapshot cut short leaves nothing behind."""
    got = {}
    runner = threading.Thread(target=lambda: got.update(
        slow=chain.command(["-c", "import time; time.sleep(30)"])))
    began = time.time()
    runner.start()
    time.sleep(1)
    try:
        chain.cancelled(15, None)
    except SystemExit:
        pass
    runner.join()
    assert time.time() - began < 5 and got["slow"][0] != 0, got
    assert chain.floored(["-c", "pass"]) == (1, "cancelado")
    chain._RUNNING["stop"] = False
    folder = root / "P"
    (folder / "databanks").mkdir(parents=True)
    run.SNAPSHOTS = root / "snapshots"
    copy = run.shutil.copytree

    def cut(src: Path, dst: Path, **kw: object) -> None:
        """Half a copy, then the SIGTERM lands."""
        (Path(dst) / "databanks").mkdir(parents=True)
        raise SystemExit("cancelado")

    run.shutil.copytree = cut
    try:
        run.snapshot(folder)
    except SystemExit:
        pass
    run.shutil.copytree = copy
    assert not any((root / "snapshots" / "P").iterdir()), "a partial copy must go"
    assert not run.snapshot(folder).name.endswith(".partial")



if __name__ == "__main__":
    for test in (test_cancel_winds_down, test_cancel_python_and_snapshot):
        with tempfile.TemporaryDirectory() as tmp:
            began = time.time()
            test(Path(tmp))
        print(f"ok  {test.__name__}  {time.time() - began:.1f} s")
