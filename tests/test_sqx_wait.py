"""`.claude/skills/sqx-wait/wait.sh` on a scratch log folder and a scratch port: never a real install."""

import os
import socket
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WAIT_SH = ROOT / ".claude" / "skills" / "sqx-wait" / "wait.sh"


def wait(logs: Path, *args: str, port: int = 1) -> tuple[int, str]:
    """Run wait.sh with its log folder and port replaced; (exit code, its one line).

    Args:
        logs: The scratch folder standing in for `user/log/StrategyQuant`.
        args: The script's own arguments.
        port: What it asks `ss` about; 1 is a port nothing listens on.
    """
    got = subprocess.run(["bash", str(WAIT_SH), *args], capture_output=True, text=True, timeout=30,
                         env={**os.environ, "SQX_WAIT_LOGS": str(logs), "SQX_WAIT_PORT": str(port)})
    return got.returncode, got.stdout.strip()


def write(log: Path, lines: list[str], age: float) -> None:
    """Append lines to a log and date it `age` seconds ago, so «newer» never hangs on the clock."""
    with log.open("a", encoding="utf-8") as f:
        f.writelines(line + "\n" for line in lines)
    os.utime(log, (time.time() - age,) * 2)


def scratch() -> Path:
    """A log folder with yesterday's log: an earlier run, finished."""
    logs = Path(tempfile.mkdtemp(prefix="sqxwait_"))
    write(logs / "log_2026_01_01.log", ["Starting project 'Test_A'", "Project finished", "idle"], 600)
    return logs


def test_mark_names_the_file_and_the_next_line() -> None:
    """`mark` prints FILE:LINE, the line the next write will be."""
    logs = scratch()
    assert wait(logs, "mark") == (0, f"{logs / 'log_2026_01_01.log'}:4")


def test_only_what_follows_the_mark_counts() -> None:
    """The earlier run's «Project finished» is before the mark: with the port down, `gone`."""
    logs = scratch()
    mark = wait(logs, "mark")[1]
    code, line = wait(logs, "--from", mark)
    assert code == 2 and line.startswith("gone"), (code, line)
    write(logs / "log_2026_01_01.log", ["ProgressEngine - Project finished"], 500)
    assert wait(logs, "--from", mark) == (0, "finished: ProgressEngine - Project finished")


def test_an_aborted_run_is_a_failure_not_a_hang() -> None:
    """«Error while running project» after the mark: exit 1, with the port down or up."""
    logs = scratch()
    mark = wait(logs, "mark")[1]
    write(logs / "log_2026_01_01.log", ["07:00 Error while running project Test_A"], 500)
    code, line = wait(logs, "--from", mark)
    assert code == 1 and line == "failed: 07:00 Error while running project Test_A", (code, line)


def test_a_log_opened_after_the_mark_is_read_from_its_first_line() -> None:
    """Midnight between mark and wait: the finish is line 2 of the new log, the mark said line 4."""
    logs = scratch()
    mark = wait(logs, "mark")[1]
    write(logs / "log_2026_01_02.log", ["Starting project 'Test_A'", "Project finished"], 100)
    assert wait(logs, "--from", mark) == (0, "finished: Project finished")


def test_a_bare_number_keeps_the_old_reading() -> None:
    """The old mark, a line number: the newest log at wait time, from that line."""
    logs = scratch()
    assert wait(logs, "--from", "1") == (0, "finished: Project finished")
    code, line = wait(logs, "--from", "3")
    assert code == 2 and line.startswith("gone"), (code, line)


def test_max_hours_ends_a_wait_on_a_worker_still_up() -> None:
    """Port listening, no end in the log, `--max-hours 0`: exit 4, not a wait."""
    logs = scratch()
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        s.listen()
        code, line = wait(logs, "--max-hours", "0", port=s.getsockname()[1])
    assert code == 4 and line.startswith("timeout"), (code, line)


if __name__ == "__main__":
    for test in (test_mark_names_the_file_and_the_next_line, test_only_what_follows_the_mark_counts,
                 test_an_aborted_run_is_a_failure_not_a_hang,
                 test_a_log_opened_after_the_mark_is_read_from_its_first_line,
                 test_a_bare_number_keeps_the_old_reading,
                 test_max_hours_ends_a_wait_on_a_worker_still_up):
        began = time.time()
        test()
        print(f"ok  {test.__name__}  {time.time() - began:.1f} s")
