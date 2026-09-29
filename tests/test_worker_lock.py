"""bin/sqx-lock.sh's owner lock (OPEN.md #32): a fake install dir, no real worker touched."""

import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_SH = ROOT / "bin" / "sqx-lock.sh"


def run(worker: Path, script: str, env: dict | None = None, running: bool = False) -> str:
    """Source sqx-lock.sh with WORKER pointed at a fake install, and run `script`.

    Args:
        worker: The fake install's top folder (never a real SQX install).
        script: Shell commands to run after sourcing, using the library's functions.
        env: Extra environment variables (e.g. CLAUDE_CODE_SESSION_ID, OWNER_ARG, FORCE_STOP).
        running: The value `running()` reports — a fake install has nothing to listen on a
            real port, so the library's caller-supplied `running()` is stubbed here.

    Returns:
        Combined stdout, raising on a non-zero exit unless the script itself checks $?.
    """
    body = (f'WORKER={worker}\nrunning() {{ {"return 0" if running else "return 1"}; }}\n'
            f'source "{LOCK_SH}"\n{script}\n')
    got = subprocess.run(["bash", "-c", body], capture_output=True, text=True,
                         env={**({} if env is None else env), "PATH": "/usr/bin:/bin"})
    assert got.returncode == 0, f"{got.stderr}\n(exit {got.returncode})"
    return got.stdout


def test_resolve_holder_precedence(root: Path) -> None:
    """CLAUDE_CODE_SESSION_ID wins over --owner/$SQX_OWNER, which wins over the "owner" default."""
    w = root / "SQX_fake"
    assert run(w, "resolve_holder") == "owner"          # printf, no trailing newline
    assert run(w, "resolve_holder", env={"SQX_OWNER": "human"}) == "human"
    assert run(w, "resolve_holder", env={"OWNER_ARG": "cli-flag"}) == "cli-flag"
    assert run(w, "resolve_holder",
              env={"OWNER_ARG": "cli-flag", "CLAUDE_CODE_SESSION_ID": "sess-1"}) == "sess-1"


def test_write_and_read_lock(root: Path) -> None:
    """`write_lock` records holder, PID and a timestamp; `owner_field` reads each back."""
    w = root / "SQX_fake"
    out = run(w, 'write_lock 4242\necho "$(owner_field holder)|$(owner_field pid)"',
              env={"CLAUDE_CODE_SESSION_ID": "sess-2"})
    assert out.strip() == "sess-2|4242", out
    assert (w / "user" / "log" / "OWNER").exists()
    since = run(w, "owner_field since").strip()
    assert since, "since must be set"


def test_stale_lock_cleared(root: Path) -> None:
    """A dead PID and a down port: the lock is stale and `clear_stale_lock` removes it."""
    w = root / "SQX_fake"
    p = subprocess.Popen(["sleep", "60"])
    p.terminate()
    p.wait()
    run(w, f"write_lock {p.pid}")
    assert (w / "user" / "log" / "OWNER").exists()
    run(w, "clear_stale_lock", running=False)
    assert not (w / "user" / "log" / "OWNER").exists(), "a dead PID + down port must clear"


def test_live_pid_keeps_the_lock(root: Path) -> None:
    """A live PID (port down) is not stale: `clear_stale_lock` leaves the lock alone."""
    w = root / "SQX_fake"
    p = subprocess.Popen(["sleep", "5"])
    try:
        run(w, f"write_lock {p.pid}")
        run(w, "clear_stale_lock", running=False)
        assert (w / "user" / "log" / "OWNER").exists(), "a live PID must not be cleared"
    finally:
        p.terminate()
        p.wait()


def test_port_up_keeps_the_lock_even_with_a_dead_pid(root: Path) -> None:
    """`running()` true (the port answers) keeps the lock even if the PID it names is dead —
    a worker whose PID bookkeeping drifted is still a live worker."""
    w = root / "SQX_fake"
    p = subprocess.Popen(["sleep", "60"])
    p.terminate()
    p.wait()
    run(w, f"write_lock {p.pid}")
    run(w, "clear_stale_lock", running=True)
    assert (w / "user" / "log" / "OWNER").exists()


def test_stop_refused_by_a_different_holder(root: Path) -> None:
    """`refuse_stop_if_held` exits 1 for a holder that is not the caller, names who and since
    when, and --force (FORCE_STOP=1) overrides it."""
    w = root / "SQX_fake"
    run(w, "write_lock 1", env={"CLAUDE_CODE_SESSION_ID": "session-A"})
    body = (f'WORKER={w}\nrunning() {{ return 1; }}\nsource "{LOCK_SH}"\n'
            'refuse_stop_if_held; echo "rc=$?"')
    got = subprocess.run(["bash", "-c", body], capture_output=True, text=True,
                         env={"CLAUDE_CODE_SESSION_ID": "session-B", "PATH": "/usr/bin:/bin"})
    assert "rc=1" in got.stdout, got.stdout
    assert "held by session-A" in got.stdout and "you are session-B" in got.stdout, got.stdout

    got = subprocess.run(["bash", "-c", body], capture_output=True, text=True,
                         env={"CLAUDE_CODE_SESSION_ID": "session-B", "FORCE_STOP": "1",
                              "PATH": "/usr/bin:/bin"})
    assert "rc=0" in got.stdout, got.stdout


def test_stop_by_the_same_holder_is_never_refused(root: Path) -> None:
    """The lock's own holder stopping its own worker is never refused, no --force needed."""
    w = root / "SQX_fake"
    run(w, "write_lock 1", env={"CLAUDE_CODE_SESSION_ID": "session-A"})
    out = run(w, 'refuse_stop_if_held; echo "rc=$?"', env={"CLAUDE_CODE_SESSION_ID": "session-A"})
    assert "rc=0" in out, out


def test_no_lock_is_never_refused(root: Path) -> None:
    """No OWNER file at all (nothing ever started this fake install): nothing to refuse."""
    w = root / "SQX_fake"
    out = run(w, 'refuse_stop_if_held; echo "rc=$?"')
    assert "rc=0" in out, out


if __name__ == "__main__":
    for test in (test_resolve_holder_precedence, test_write_and_read_lock,
                 test_stale_lock_cleared, test_live_pid_keeps_the_lock,
                 test_port_up_keeps_the_lock_even_with_a_dead_pid,
                 test_stop_refused_by_a_different_holder,
                 test_stop_by_the_same_holder_is_never_refused, test_no_lock_is_never_refused):
        with tempfile.TemporaryDirectory() as scratch:
            began = time.time()
            test(Path(scratch))
        print(f"ok  {test.__name__}  {time.time() - began:.1f} s")
