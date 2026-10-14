"""Encargo 66 §5.6/§5.7: fixed sleeps became waits on the real condition, polled every second at most."""

import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqx.projects import live
from sqx.variants import execute
from tests.test_perf66_sqxprojects import SAVED
from ui.daemon.launch import chain


def _fn(name: str, call: str) -> subprocess.CompletedProcess:
    """Run one function cut out of the real bin/sqx-worker.sh."""
    body = subprocess.run(
        ["sed", "-n", f"/^{name}()/,/^}}/p", str(ROOT / "bin/sqx-worker.sh")],
        capture_output=True,
        text=True,
    ).stdout
    return subprocess.run(
        ["bash", "-c", f"{body}\n{call}"], capture_output=True, text=True, timeout=30
    )


def test_pid_wait_returns_when_the_process_is_gone_and_fails_loud_at_timeout() -> None:
    """A dead PID: exit 0 at once. A live one: exit 1 naming the PID."""
    t0 = time.time()
    assert (
        _fn("pid_wait", "pid_wait 99999999 10").returncode == 0 and time.time() - t0 < 3
    )
    late = _fn("pid_wait", "pid_wait $$ 2")
    assert late.returncode != 0 and "still there after 2 s" in late.stderr


def test_xvfb_wait_returns_when_the_socket_exists_and_fails_loud_at_timeout(
    tmp_path: Path,
) -> None:
    """The X socket is the condition: present -> 0 at once; absent -> 1 naming the display."""
    n = 9000 + (time.time_ns() % 900)
    sock = Path(f"/tmp/.X11-unix/X{n}")
    sock.parent.mkdir(exist_ok=True)
    missing = _fn("xvfb_wait", f"XSOCK_DIR=/tmp/.X11-unix; xvfb_wait :{n} 2 $$")
    assert (
        missing.returncode != 0
        and f"display :{n} has no socket after 2 s" in missing.stderr
    )
    proc = subprocess.Popen(
        [
            sys.executable,
            "-c",
            f"import socket,time;s=socket.socket(socket.AF_UNIX);"
            f"s.bind('{sock}');time.sleep(10)",
        ]
    )
    try:
        for _ in range(50):
            if sock.exists():
                break
            time.sleep(0.1)
        t0 = time.time()
        assert (
            _fn(
                "xvfb_wait", f"XSOCK_DIR=/tmp/.X11-unix; xvfb_wait :{n} 10 $$"
            ).returncode
            == 0
            and time.time() - t0 < 3
        )
    finally:
        proc.kill()
        sock.unlink(missing_ok=True)


def test_awake_polls_every_second_and_fails_at_the_same_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The CLI answers on the 3rd poll -> True after 3 one-second sleeps; never -> SystemExit naming the bound."""
    sleeps: list[float] = []
    cfg = {"role": "custodian", "ready_tries": 5, "poll_seconds": 2}
    monkeypatch.setattr(execute.time, "sleep", sleeps.append)
    monkeypatch.setattr(execute.worker, "start", lambda role: None)

    def script(ready_at: int) -> Callable[[str, dict], str]:
        """First probe: port down (OSError). Then 'not ready' until the `ready_at`-th sleep."""

        def call(c: str, cfg: dict) -> str:
            """Down, then not ready, then ready."""
            if not sleeps:
                raise OSError
            return (
                "projects: []" if len(sleeps) >= ready_at else "Error: CLI not ready."
            )

        return call

    monkeypatch.setattr(execute, "_call", script(3))
    assert execute.awake(cfg) is True and sleeps == [1, 1, 1]
    sleeps.clear()
    monkeypatch.setattr(execute, "_call", script(10**6))
    with pytest.raises(SystemExit, match="no respondio tras 10 s"):
        execute.awake(cfg)
    assert len(sleeps) == 10


def test_the_core_gate_takes_a_freed_slot_within_a_second(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A heavy job that does not fit sleeps 1 s at most between looks, then runs once the room is free."""
    sleeps: list[float] = []
    free = iter([0.0, 1e12])
    monkeypatch.setattr(chain.time, "sleep", sleeps.append)
    monkeypatch.setattr(
        chain.psutil,
        "virtual_memory",
        lambda: type("M", (), {"available": next(free)})(),
    )
    monkeypatch.setattr(chain, "command", lambda argv: (0, "ok"))
    monkeypatch.setitem(chain._RUNNING, "n", 1)
    assert chain.floored(["x"], "") == (0, "ok") and sleeps == [1]


@pytest.mark.parametrize("poll,polls", [(0, 1), (0.5, 1), (1.5, 3)])
def test_awake_polls_at_least_once_with_zero_or_float_poll_seconds(
    monkeypatch: pytest.MonkeyPatch, poll: float, polls: int
) -> None:
    """`ready_tries * poll_seconds` of 0 still polls once; a float rounds up instead of raising TypeError."""
    sleeps: list[float] = []
    monkeypatch.setattr(execute.time, "sleep", sleeps.append)
    monkeypatch.setattr(execute.worker, "start", lambda role: None)
    monkeypatch.setattr(
        execute,
        "_call",
        lambda c, cfg: (
            "Error: CLI not ready." if sleeps else (_ for _ in ()).throw(OSError)
        ),
    )
    with pytest.raises(SystemExit, match="no respondio"):
        execute.awake(
            {
                "role": "custodian",
                "ready_tries": 1 if poll < 1 else 2,
                "poll_seconds": poll,
            }
        )
    assert len(sleeps) == polls


def test_load_has_no_sleep_after_clear_and_waits_for_the_line_written_after_its_own_load(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """🔬 2026-10-13: `clear` is synchronous (no sleep); `load` ends on «Strategies loaded» past the mark, else fails loudly."""
    from sqx.projects import live

    log = tmp_path / "log_2026_01_01.log"
    log.write_text("Strategies loaded: an earlier session's\n")
    monkeypatch.setattr(live, "_log", lambda role: log)
    monkeypatch.setattr(live, "_top", lambda role: tmp_path)
    sent, slept, write = [], [], [True]

    def call(command: str, cfg: dict) -> str:
        """Every command ok; the load logs its line (or not)."""
        sent.append(command)
        if "action=load" in command and write[0]:
            log.open("a").write("ProjectServlet - Strategies loaded\n")
        return "ok"

    monkeypatch.setattr(execute, "_call", call)
    monkeypatch.setattr(execute.loadwait.time, "sleep", slept.append)
    cfg = {"role": "custodian", "project": "Test_X"}
    execute.load(Path("/batch"), cfg)
    assert (
        sent[-1].startswith("-databank action=load")
        and sum("action=clear" in c for c in sent) >= 2
        and not slept
    )
    write[0] = False
    monkeypatch.setattr(execute, "LOAD_S", 0)
    with pytest.raises(SystemExit, match="Strategies loaded"):
        execute.load(Path("/batch"), cfg)


def _sync_world(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, files: int, line: bool
) -> list:
    """`Results` holds 2 in memory and `files` on disk; a sync writes the «saved» line only when `line`."""
    bank = tmp_path / "user/projects/Test_X/databanks/Results"
    bank.mkdir(parents=True)
    for n in range(files):
        (bank / f"{n}.sqx").write_text("x")
    log, sent = tmp_path / "log_2026_01_01.log", []
    log.write_text("")

    def call(role: str, action: str, **p: str) -> dict:
        """databankList; a sync that completes the files and logs (or not)."""
        if action == "databankList":
            return {
                "databanks": [
                    {
                        "name": "Results",
                        "records": 2,
                        "syncType": "Auto-sync every 1 hour",
                    }
                ]
            }
        sent.append(1)
        for n in range(2):
            (bank / f"{n}.sqx").write_text("x")
        if line:
            log.open("a").write(
                SAVED.format(
                    "Results", "API request project/synchronizeDatabank Test_X/Results."
                )
            )
        return {}

    monkeypatch.setattr(live, "_top", lambda role: tmp_path)
    monkeypatch.setattr(live, "_log", lambda role: log)
    monkeypatch.setattr(live, "call", call)
    return sent


def test_forced_sync_needs_its_line_even_when_files_match_and_waits_for_a_queued_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """M1: files == memory and silent: loud (SQX's saver is serial; no quiet shortcut). A line arriving late is fine."""
    import shutil

    ticks = []

    def late_line(_: float) -> None:
        """The queued save finishes after 50 polls and logs its line."""
        ticks.append(1)
        if len(ticks) == 50:
            (tmp_path / "log_2026_01_01.log").open("a").write(
                SAVED.format(
                    "Results", "API request project/synchronizeDatabank Test_X/Results."
                )
            )

    _sync_world(monkeypatch, tmp_path, 2, line=False)
    monkeypatch.setattr(live.time, "sleep", late_line)
    assert (
        live.sync("custodian", "Test_X", force={"Results"}) == {"Results": 2}
        and len(ticks) >= 50
    )
    shutil.rmtree(tmp_path / "user")
    _sync_world(monkeypatch, tmp_path, 2, line=False)
    monkeypatch.setattr(
        live.time, "sleep", lambda s: None
    )  # the 600 idle polls pass at once
    with pytest.raises(SystemExit, match="sin «saved»"):
        live.sync("custodian", "Test_X", force={"Results"})
    shutil.rmtree(tmp_path / "user")
    _sync_world(monkeypatch, tmp_path, 1, line=True)
    assert live.sync("custodian", "Test_X", force={"Results"}) == {"Results": 2}


def test_loaded_reads_the_next_days_log_whole_and_ignores_a_line_before_the_mark(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """F5: past midnight `since` names yesterday's log; a line before its offset never counts, one in today's does."""
    from sqx.projects import loadwait

    old, new = tmp_path / "log_old.log", tmp_path / "log_new.log"
    old.write_text("ProjectServlet - Strategies loaded\n")
    since, new_text = (old, old.stat().st_size), "other\n"
    new.write_text(new_text)
    monkeypatch.setattr(live, "_log", lambda role: new)
    monkeypatch.setattr(loadwait.time, "sleep", lambda s: None)
    with pytest.raises(SystemExit, match="Strategies loaded"):
        loadwait.loaded("custodian", since, 0, 0, "B")
    new.write_text(new_text + "ProjectServlet - Strategies loaded\n")
    loadwait.loaded("custodian", since, 5, 0, "B")


def _boot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, written: str
) -> tuple[list, list]:
    """`live.start` over a log that already holds an «APP LOADED»; the script stub writes `written` (or nothing)."""
    log, calls, killed = tmp_path / "log_2026_01_01.log", [], []
    log.write_text("BrowserGUI - APP LOADED\n")  # an earlier session's line
    monkeypatch.setattr(live, "_log", lambda role: log)
    monkeypatch.setattr(
        live.subprocess, "run", lambda *a, **k: log.open("a").write(written)
    )
    monkeypatch.setattr(
        live, "call", lambda role, action, **k: calls.append(action) or {"projects": []}
    )
    monkeypatch.setattr(live, "kill", killed.append)
    monkeypatch.setattr(live.loadwait.time, "sleep", lambda s: None)
    monkeypatch.setattr(live.worker, "holding", lambda top: [])
    return calls, killed


def test_start_returns_only_after_app_loaded_written_after_the_mark(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The line after the start counts and the session's databanks are then asked; one before the mark does not."""
    calls, killed = _boot(monkeypatch, tmp_path, "BrowserGUI - APP LOADED\n")
    live.start("custodian")
    assert calls == ["list"] and not killed
    calls, killed = _boot(monkeypatch, tmp_path, "")
    with pytest.raises(SystemExit, match="APP LOADED"):
        live.start("custodian")
    assert calls == [] and killed == ["custodian"]  # no task, no query: killed by PID


def test_start_refuses_an_install_somebody_holds_and_kills_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The script would answer «already running» and `booted` would kill that session after 300 s: refused before."""
    calls, killed = _boot(monkeypatch, tmp_path, "")
    monkeypatch.setattr(live.worker, "holding", lambda top: [4242])
    with pytest.raises(SystemExit, match="ya está arrancado"):
        live.start("custodian")
    assert calls == [] and killed == []
