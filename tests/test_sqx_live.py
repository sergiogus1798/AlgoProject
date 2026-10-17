"""`sqx.projects.live` and `livexec` waiting for a GUI-mode run, on fakes: no HTTP, no install."""

import contextlib
import sys
import tempfile
import time
from collections.abc import Callable, Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import worker  # noqa: E402
from sqx.projects import live  # noqa: E402
from sqx.variants import livexec  # noqa: E402

CFG = {"role": "custodian", "project": "Test_X", "poll_seconds": 0, "ready_tries": 2}


@contextlib.contextmanager
def patched(*swaps: tuple[object, str, object]) -> Iterator[None]:
    """Set attributes for one test and put them back: (owner, name, value) each."""
    old = [(o, n, getattr(o, n)) for o, n, _ in swaps]
    for o, n, v in swaps:
        setattr(o, n, v)
    try:
        yield
    finally:
        for o, n, v in old:
            setattr(o, n, v)


def raises(text: str, fn: Callable, *args: object) -> None:
    """`fn(*args)` must end in a SystemExit whose message carries `text`."""
    try:
        fn(*args)
    except SystemExit as e:
        assert text in str(e), str(e)
        return
    raise AssertionError(f"no SystemExit («{text}»)")


def install() -> Path:
    """A fake install folder with an empty log folder."""
    top = Path(tempfile.mkdtemp(prefix="sqxbridge_"))
    (top / "user/log/StrategyQuant").mkdir(parents=True)
    return top


def clock(step: float) -> Callable[[], float]:
    """A monotonic clock that jumps `step` seconds a reading."""
    now = iter(range(10**6))
    return lambda: next(now) * step


def test_wait_reads_each_line_once_follows_midnight_and_returns_the_end() -> None:
    """The finish before the mark is skipped, a half line waits, and the next day's log is followed."""
    logs = install() / "user/log/StrategyQuant"
    day1, day2 = logs / "log_2026_01_01.log", logs / "log_2026_01_02.log"
    day1.write_text("old Project finished\n")
    since = (day1, day1.stat().st_size)
    polls = {"n": 0}

    def sleep(seconds: float) -> None:
        """SQX writes as the wait polls: a half line, its end, then the next day's file."""
        polls["n"] += 1
        if polls["n"] == 1:
            day1.open("a").write("23:59 Task fin")
        elif polls["n"] == 2:
            day1.open("a").write("ished\n")
        elif polls["n"] == 3:
            day2.write_text("00:01 ProgressEngine - Project finished\n")

    with patched(
        (live, "_up", lambda role: True),
        (time, "sleep", sleep),
        (live, "_log", lambda role: day2 if day2.exists() else day1),
    ):
        assert (
            live.wait("custodian", since) == "00:01 ProgressEngine - Project finished"
        )


def test_wait_ends_when_the_port_stays_down_or_the_bound_passes() -> None:
    """MISSES refused polls in a row end the wait; so does MAX_HOURS with the port up."""
    logs = install() / "user/log/StrategyQuant"
    day1 = logs / "log_2026_01_01.log"
    day1.write_text("23:59 Starting\n")
    since, polls = (day1, 0), []
    with patched(
        (live, "_up", lambda role: False),
        (time, "sleep", polls.append),
        (live, "_log", lambda role: day1),
    ):
        raises("dejó de escuchar", live.wait, "custodian", since)
    assert len(polls) == live.MISSES - 1  # one miss is not a dead session
    with patched(
        (live, "_up", lambda role: True),
        (time, "sleep", lambda s: None),
        (live, "_log", lambda role: day1),
        (time, "monotonic", clock(3600 * 30.0)),
    ):
        raises(f"tras {worker.MAX_HOURS} h", live.wait, "custodian", since)


def test_a_slow_load_raises_before_any_sync_and_keeps_its_copy() -> None:
    """2 of 3 in memory after the poll: no sync, the copy stays and is named; 3 of 3: synced, copy gone."""
    top = install()
    bank = top / "user/projects/Test_X/databanks/Results"
    bank.mkdir(parents=True)
    for name in ("a", "b", "c"):
        (bank / f"{name}.sqx").write_text(name)
    aside, synced = top / "aside", []
    aside.mkdir()
    fakes = [
        (live, "_top", lambda role: top),
        (live, "tmp_dir", lambda: aside),
        (live, "call", lambda role, action, **params: {"strategies": []}),
        (live, "sync", lambda role, project, banks=None: synced.append(banks)),
        (time, "sleep", lambda s: None),
    ]
    with patched(*fakes, (live, "records", lambda role, project: {"Results": 2})):
        raises(str(aside), live.load, "custodian", "Test_X", "Results")
    assert synced == []
    kept = sorted(p.name for p in next(aside.iterdir()).iterdir())
    assert kept == ["a.sqx", "b.sqx", "c.sqx"], kept
    for d in aside.iterdir():
        for f in d.iterdir():
            f.unlink()
        d.rmdir()
    with patched(*fakes, (live, "records", lambda role, project: {"Results": 3})):
        assert live.load("custodian", "Test_X", "Results") == 3
    assert synced == [["Results"]] and list(aside.iterdir()) == []


def test_a_stopped_project_is_not_a_finished_batch() -> None:
    """«Project stopped» and the abort line are failures; only «Project finished» returns the count."""
    fakes = [
        (live, "call", lambda role, action, **params: {"config": {"xml": "<x/>"}}),
        (livexec.stage, "only", lambda xml, titles: ("<x/>", [])),
        (
            live,
            "records",
            lambda role, project: {leg["databank"]: 2 for leg in livexec.legmod.legs()},
        ),
    ]
    for end, text in (
        ("10:00 Project stopped", "Project stopped"),
        ("10:00 Error while running project", "Error while running"),
    ):
        with patched(*fakes, (live, "run", lambda role, project, config, end=end: end)):
            raises(text, livexec.run, 6, CFG, lambda pct, line: None)
    with patched(
        *fakes, (live, "run", lambda role, project, config: "10:00 Project finished")
    ):
        assert livexec.run(6, CFG, lambda pct, line: None) == 2 * len(
            livexec.legmod.legs()
        )


def test_mark_and_wait_survive_yesterdays_log_deleted_at_start() -> None:
    """SQX deletes old logs while it starts: the vanished one is skipped, today's is read."""
    logs = install() / "user/log/StrategyQuant"
    gone, today = logs / "log_2026_01_01.log", logs / "log_2026_01_02.log"
    today.write_text("00:01 ProgressEngine - Project finished\n")
    answers = iter([gone, today])
    with patched(
        (time, "sleep", lambda seconds: None),
        (live, "_log", lambda role: next(answers, today)),
        (live, "_up", lambda role: True),
    ):
        assert live.mark("custodian") == (today, today.stat().st_size)
        assert live.wait("custodian", (gone, 0)).endswith("Project finished")


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            began = time.time()
            test()
            print(f"ok  {name}  {time.time() - began:.1f} s")
