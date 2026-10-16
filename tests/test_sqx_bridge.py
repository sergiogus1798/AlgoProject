"""`core.worker` and `sqx.variants.execute` waiting for and talking to SQX, on fakes: no HTTP, no install."""

import contextlib
import io
import json
import os
import sys
import tempfile
import time
import urllib.request
from collections.abc import Callable, Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import worker  # noqa: E402
from sqx.variants import banks, execute  # noqa: E402

CFG = {"role": "custodian", "project": "Test_X", "poll_seconds": 0, "ready_tries": 2}
ABORT = "07:00 Error while running project Test_X\n"


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


def test_call_has_a_timeout_and_checked_refuses_an_error_body() -> None:
    """`worker.call` passes its timeout to urlopen and still returns text; `checked` raises on `Error:`."""
    seen = {}

    def urlopen(url: str, timeout: float | None = None) -> io.BytesIO:
        """urllib's urlopen: record what it was given, answer as a CLI still loading."""
        seen.update(url=url, timeout=timeout)
        return io.BytesIO(b"Error: CLI not ready.")

    with patched((urllib.request, "urlopen", urlopen)):
        reply = worker.call("-project action=list", "custodian")
        assert (
            seen["timeout"] == worker.TIMEOUT == 600 and "%20action=list" in seen["url"]
        )
        worker.call("-project action=list", "custodian", timeout=5)
        assert seen["timeout"] == 5
    assert reply == "Error: CLI not ready."  # the return type did not change
    raises("CLI not ready", worker.checked, reply, "-project action=list")
    assert worker.checked("Loaded", "x") == "Loaded"


def test_awake_refuses_a_running_install_that_is_not_this_holders() -> None:
    """Up with no lock, or another holder's: SystemExit and nothing started; this holder's: False."""
    top, started = install(), []
    lock = top / "user/log/OWNER"
    with patched(
        (worker, "call", lambda command, role="conductor": "Projects: Test_X"),
        (worker, "start", lambda role: started.append(role)),
        (worker, "holder", lambda: "me"),
        (execute, "worker_dir", lambda role: top),
    ):
        raises("no hay OWNER", execute.awake, CFG)
        lock.write_text(json.dumps({"holder": "calib-queue", "pid": 1, "since": "x"}))
        raises("calib-queue", execute.awake, CFG)
        lock.write_text(json.dumps({"holder": "me", "pid": 1, "since": "x"}))
        assert execute.awake(CFG) is False
    assert started == []


def test_awake_starts_an_install_that_is_down() -> None:
    """A refused connection is an install that is down: it is started, and awake says so."""
    state = {"up": False}

    def call(command: str, role: str = "conductor") -> str:
        """core.worker.call: refused until the start."""
        if not state["up"]:
            raise ConnectionRefusedError
        return "Projects: Test_X"

    with patched(
        (worker, "call", call),
        (worker, "start", lambda role: state.update(up=True)),
        (time, "sleep", lambda s: None),
    ):
        assert execute.awake(CFG) is True


def test_holder_resolves_as_the_lock_does() -> None:
    """Session id, then $SQX_OWNER, then «owner»: bin/sqx-lock.sh's order."""
    with patched((os, "environ", {"SQX_OWNER": "human"})):
        assert worker.holder() == "human"
    with patched(
        (os, "environ", {"SQX_OWNER": "human", "CLAUDE_CODE_SESSION_ID": "s1"})
    ):
        assert worker.holder() == "s1"
    with patched((os, "environ", {})):
        assert worker.holder() == "owner"


def test_aborted_follows_every_log_and_reads_each_byte_once() -> None:
    """An abort before the mark is not this run's; a half line waits; the next day's log is read."""
    logs = install() / "user/log/StrategyQuant"
    day1, day2 = logs / "log_2026_01_01.log", logs / "log_2026_01_02.log"
    day1.write_text(ABORT)  # an earlier run's abort
    seen = banks.mark(logs)
    assert not banks.aborted(logs, seen)
    day2.write_text("00:00 Starting\n07:00 Error while runn")  # half a line
    assert not banks.aborted(logs, seen) and seen[day2] == len("00:00 Starting\n")
    with day2.open("a") as f:
        f.write("ing project Test_X\n")
    assert banks.aborted(logs, seen)
    assert not banks.aborted(logs, seen)  # read once, not again


def run_with(
    status: list[str],
    top: Path,
    step: float = 0.0,
    started: Callable[[], object] = lambda: None,
) -> int:
    """`execute.run` for 4 retests against a scripted `action=status`; `started` runs at the start."""
    replies = iter(status)

    def call(command: str, role: str = "conductor") -> str:
        """core.worker.call: the start, or the next scripted status."""
        if "action=start" in command:
            started()
            return "10:00:00 Starting project 'Test_X'"
        return next(replies)

    with patched(
        (worker, "call", call),
        (execute, "worker_dir", lambda role: top),
        (time, "sleep", lambda s: None),
        (time, "monotonic", clock(step)),
    ):
        return execute.run(4, CFG, lambda pct, line: None)


def test_run_counts_from_its_base_and_names_a_reply_without_a_count() -> None:
    """The count is «In databank» minus its base; a reply with none ends naming the reply."""
    top = install()
    assert run_with(["In databank 10", "In databank 12", "In databank 14"], top) == 4
    raises("Error: CLI not ready.", run_with, ["Error: CLI not ready."], top)
    raises(
        "Error: Project 'Test_X'",
        run_with,
        ["In databank 10", "Error: Project 'Test_X' gone"],
        top,
    )


def test_run_sees_an_abort_in_the_next_days_log_and_is_bounded() -> None:
    """An abort written to a log opened after the start ends the wait, and so does MAX_HOURS."""
    top = install()
    logs = top / "user/log/StrategyQuant"
    (logs / "log_2026_01_01.log").write_text("23:59 Starting\n")
    day2 = logs / "log_2026_01_02.log"  # opened after the mark: midnight
    raises(
        "abortó Test_X",
        run_with,
        ["In databank 10"] * 50,
        top,
        0.0,
        lambda: day2.write_text(ABORT),
    )
    day2.unlink()
    raises(
        f"tras {worker.MAX_HOURS} h",
        run_with,
        ["In databank 10"] * 50,
        top,
        3600 * 30.0,
    )


def test_load_refuses_an_error_reply_on_clear_and_load() -> None:
    """`Error:` to a clear, a load or an export is fatal."""

    def call(command: str, role: str = "conductor") -> str:
        """core.worker.call: every reply an error body."""
        return (
            "Error: Databank 'X' doesn't exist."
            if "action=load" in command
            else "Error: odd"
        )

    with patched((worker, "call", call), (time, "sleep", lambda s: None)):
        raises("action=clear", execute.load, Path("/nowhere"), CFG)
        raises(
            "action=export", execute.panel, Path("/nowhere"), CFG, "WFC", "retest_oos1"
        )


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            began = time.time()
            test()
            print(f"ok  {name}  {time.time() - began:.1f} s")
