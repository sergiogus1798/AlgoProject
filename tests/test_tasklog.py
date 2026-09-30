"""A project log SQX is still writing, and a run killed before its end: neither may stop a run or block a load."""

import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ui.daemon import progress, tasklog  # noqa: E402
from ui.daemon.loader import find  # noqa: E402

# What SQX had written of global_log_*.log one second into a build, 2026-09-28 12:07:15.
HALF = ("Project: P\nLog file: /global_log_x.log\n\n" + "-" * 40 + "\n"
        "TASK STARTED at {day} 12:07:15.643\nTask: CONSTRUCCION, Type: Build\n")


def test_half_written_log() -> None:
    """The start without «Databanks before start» is read, not a crash (it killed a build)."""
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "log"
        log.mkdir()
        (log / f"global_log_{datetime.now():%Y%m%d}_120715.log").write_text(
            HALF.format(day=f"{datetime.now():%Y.%m.%d}"), encoding="utf-8")
        runs = tasklog.task_runs(Path(tmp))
    assert [(r["title"], r["before"], r["finished"]) for r in runs] == [("CONSTRUCCION", {}, None)]


def test_start_survives_a_big_day() -> None:
    """The start stays read past 2 MB of syncs (🔬 2026-09-29: the old 2 MB tail lost it an
    hour into MCR 2 Spread, and every reader took the run for finished); growth is read
    incrementally and a later start replaces the earlier one."""
    with tempfile.TemporaryDirectory() as tmp:
        top = Path(tmp)
        f = top / "user" / "log" / "StrategyQuant" / f"log_{datetime.now():%Y_%m_%d}.log"
        f.parent.mkdir(parents=True)
        pe = "INFO  c.s.t.project.ProgressEngine - "
        noise = "08:00:00.000 [Thread-1] INFO  StrategiesSaver - Databank saved " + "x" * 200 + "\n"
        f.write_text(f"06:48:15 Starting project 'P'\n06:48:16 {pe}MCR 1 Bar : Starting\n"
                     f"06:57:58 {pe}MCR 1 Bar : Task finished\n" + noise * 12_000
                     + f"07:00 {pe}MCR 2 Spread : Starting strategies retesting...\n",
                     encoding="utf-8")
        assert f.stat().st_size > 2_500_000
        run = progress.run_state(progress.log_lines(top)[0])
        assert (run["project"], run["finished"], run["current"]) == ("P", False, "MCR 2 Spread")
        assert run["events"]["MCR 1 Bar"] == "done", run["events"]
        with f.open("a", encoding="utf-8") as fh:
            fh.write(f"09:00 {pe}Project finished\n09:01 Starting project 'Q'\n09:01 {pe}A : Go")
        run = progress.run_state(progress.log_lines(top)[0])
        assert (run["project"], run["current"]) == ("Q", None), "a half line waits"
        with f.open("a", encoding="utf-8") as fh:
            fh.write("\n")
        run = progress.run_state(progress.log_lines(top)[0])
        assert (run["project"], run["current"], list(run["events"])) == ("Q", "A", ["A"]), run


def test_watch_keeps_the_start() -> None:
    """A WFM writes a line per cell and step: bounding them must never drop the start, or the
    launch watcher reads «SQX did not start» and stops the worker mid-run (2026-09-29)."""
    pe = "INFO  c.s.t.project.ProgressEngine - "
    lines = ["06:00 Starting project 'P'", f"06:01 {pe}WFM : Starting"] + [
        f"06:02 {pe}WFM : Retesting strategy {i}" for i in range(30_000)]
    kept = progress.trim(lines, 20_000)
    run = progress.run_state(kept)
    assert len(kept) == 20_001 and (run["project"], run["finished"], run["current"]) == (
        "P", False, "WFM"), run
    flood = lines[:3] + ["[Blocking computeThread common #51 - WF: 8 runs : 20 % OOS WFO 4] "
                         "ERROR StatsComputer - Exception computing databank column X"] * 30_000
    run = progress.run_state(progress.trim(flood, 20_000))
    assert (run["current"], run["percent"]) == ("WFM", 20), "a flood of percent lines"


def test_durations() -> None:
    """Every duration SQX prints parses: past a minute per strategy /api/pulse raised."""
    assert [tasklog.to_ms(t) for t in ("850 ms.", "21 s.", "1 min. 10 s.", "1 hr. 15 min.")] \
        == [850, 21_000, 70_000, 4_500_000]
    got = tasklog.TESTED.search("Total tested: 21, Time per strategy: 1 min. 10 s., "
                                "Passed: 20, Failed: 1")
    assert got and got.groups() == ("21", "1 min. 10 s.", "20", "1")


def test_killed_run_is_not_writing() -> None:
    """A log that says «started» with no SQX process alive is not a project being written."""
    lines = ["12:07:15.538 Starting project 'P'", "12:07:15.647 CONSTRUCCION : Initializing"]
    progress.log_lines = lambda top: (lines, 0.0)
    find.worker.holding = lambda top: []
    assert not find.writing(Path("/nowhere"), "P")
    find.worker.holding = lambda top: [4242]
    assert find.writing(Path("/nowhere"), "P")


if __name__ == "__main__":
    for test in (test_half_written_log, test_start_survives_a_big_day, test_durations,
                 test_watch_keeps_the_start,
                 test_killed_run_is_not_writing):
        test()
        print(f"ok  {test.__name__}")
