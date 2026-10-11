"""bin/sqx-worker.sh's start/stop lifecycle, without ever touching a real worker.

Each test runs a COPY of bin/sqx-worker.sh and bin/sqx-lock.sh inside a fake project root whose
`core/paths.py` points at a fake master and a fake install, with a small Python program named
`sqcli` standing in for StrategyQuant on a free ephemeral port.
→ knowhow/sqx-drive/worker-process-lifecycle.md
"""

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# SQX_TEST_BIN points the tests at a candidate copy of the scripts before it replaces bin/.
BIN = Path(os.environ.get("SQX_TEST_BIN", ROOT / "bin"))

# The stand-in for StrategyQuant. Its first line is an absolute interpreter, not `env`, so
# the kernel names the process `sqcli` and `pgrep -x sqcli` finds it as it finds the real one.
FAKE_SQCLI = """#!{python}
import http.server, os, pathlib, signal, sys, time
here = pathlib.Path.cwd()
mode = (here / "mode").read_text().strip()      # noport | serve | deaf
(here / "launched.pid").write_text(str(os.getpid()))
(here / "inherited-fd9").write_text(str(os.path.exists("/proc/self/fd/9")))
signal.signal(signal.SIGTERM, lambda *_: os._exit(0))
if mode == "noport":
    while True:
        time.sleep(0.2)
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
        if "-exit" in self.path and mode == "serve":
            os._exit(0)
srv = http.server.HTTPServer(("127.0.0.1", {port}), H)
print("SQX CLI is now ready. Execute a command or type -h for assistance", flush=True)
srv.serve_forever()
"""


def fake_root(root: Path, mode: str) -> tuple[Path, Path]:
    """Build a throwaway project root, master and install that bin/sqx-worker.sh can drive.

    Args:
        root: The test's scratch folder.
        mode: What the fake `sqcli` does — "noport" never opens its port, "serve" opens it
            and exits on `-exit`, "deaf" opens it and ignores `-exit`.

    Returns:
        The copied script and the fake install's top folder.
    """
    with socket.socket() as s:                    # a free port, never one of SQX's
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    proj, master, worker = root / "proj", root / "SQX_master", root / "SQX_fake"
    (proj / "bin").mkdir(parents=True)
    (proj / "core").mkdir()
    for name in ("sqx-worker.sh", "sqx-lock.sh"):
        shutil.copy2(BIN / name, proj / "bin" / name)
    prune = proj / "bin" / "sqx-log-prune.sh"
    prune.write_text("#!/bin/bash\nexit 0\n")
    prune.chmod(0o755)
    (proj / "core" / "__init__.py").write_text("")
    (proj / "core" / "paths.py").write_text(
        f"MASTER = {str(master)!r}\n"
        f"WORKERS = {{'conductor': {{'path': {str(worker)!r}, 'port': {port}}}}}\n")
    (master / "user" / "data").mkdir(parents=True)
    (master / "user" / "data" / "data.db").write_text("bars")
    for sub in ("user/log", "user/data", "user/settings", "internal"):
        (worker / sub).mkdir(parents=True)
    (worker / "internal" / "AppSettings.txt").write_text(
        f"<AppWebServerPortSQUANT>{port}</AppWebServerPortSQUANT>")
    (worker / "mode").write_text(mode)
    sqcli = worker / "sqcli"
    sqcli.write_text(FAKE_SQCLI.format(python=sys.executable, port=port))
    sqcli.chmod(0o755)
    return proj / "bin" / "sqx-worker.sh", worker


def script(sh: Path, verb: str, **env: str) -> subprocess.CompletedProcess:
    """Run the copied bin/sqx-worker.sh with one verb, as holder "tester"."""
    return subprocess.run(
        [str(sh), verb], capture_output=True, text=True, timeout=120,
        env={"PATH": "/usr/bin:/bin", "HOME": os.environ["HOME"], "SQX_OWNER": "tester", **env})


def alive(pid: int) -> bool:
    """True while `pid` exists and is not a zombie waiting to be reaped."""
    try:
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0] != "Z"
    except OSError:
        return False


def reap(worker: Path) -> None:
    """Kill whatever fake sqcli a test left behind — by the PID it wrote, never by name."""
    f = worker / "launched.pid"
    if f.exists() and alive(int(f.read_text())):
        os.kill(int(f.read_text()), signal.SIGKILL)


def test_start_and_stop_succeed_as_before(root: Path) -> None:
    """The success path: the same lines and exit 0, the lock written at launch with the
    daemon's PID, the start flock NOT inherited by the daemon, and a stale XVFB file (its PID
    is a `sleep`, not an Xvfb) removed by a non-GUI start and by `stop` without killing it."""
    sh, w = fake_root(root, "serve")
    bystander = subprocess.Popen(["sleep", "60"])
    xvfb = w / "user" / "log" / "XVFB"
    try:
        xvfb.write_text(str(bystander.pid))
        got = script(sh, "start")
        assert got.returncode == 0, got.stdout + got.stderr
        for line in ("bars synced", "starting conductor", "worker up:", "owner:      tester"):
            assert line in got.stdout, got.stdout
        assert not xvfb.exists(), "a non-GUI start must clear a stale XVFB file"
        pid = int((w / "launched.pid").read_text())
        lock = json.loads((w / "user" / "log" / "OWNER").read_text())
        assert lock["holder"] == "tester" and lock["pid"] == pid, lock
        assert (w / "inherited-fd9").read_text() == "False", "the daemon holds the start flock"
        assert "already running" in script(sh, "start").stdout

        xvfb.write_text(str(bystander.pid))
        got = script(sh, "stop")
        assert got.returncode == 0, got.stdout + got.stderr
        assert "stale" in got.stdout and "conductor stopped" in got.stdout, got.stdout
        assert not alive(pid) and not xvfb.exists()
        assert bystander.poll() is None, "stop killed a PID that was never its Xvfb"
        assert not (w / "user" / "log" / "OWNER").exists()
        got = script(sh, "stop")
        assert got.returncode == 0 and "conductor not running" in got.stdout, got.stdout
    finally:
        bystander.kill()
        bystander.wait()
        reap(w)


def test_concurrent_start_is_refused(root: Path) -> None:
    """While another start holds user/log/.start.lock, `start` exits 1 and launches nothing."""
    sh, w = fake_root(root, "serve")
    holder = subprocess.Popen(["flock", str(w / "user" / "log" / ".start.lock"), "sleep", "60"])
    try:
        time.sleep(0.5)
        got = script(sh, "start")
        assert got.returncode == 1 and "in progress" in got.stdout, got.stdout + got.stderr
        assert got.stdout.startswith("REFUSING"), got.stdout
        assert not (w / "launched.pid").exists(), "the refused start still launched sqcli"
        assert not (w / "user" / "log" / "OWNER").exists()
    finally:
        holder.kill()
        holder.wait()
        reap(w)


def test_start_that_never_opens_its_port_is_killed(root: Path) -> None:
    """A start whose port never opens exits 1, kills the sqcli it launched by PID and leaves
    no owner lock — it used to leave the process alive and unowned."""
    sh, w = fake_root(root, "noport")
    try:
        got = script(sh, "start", SQX_START_WAIT="4")
        assert got.returncode == 1 and "worker failed to start" in got.stdout, got.stdout
        pid = int((w / "launched.pid").read_text())
        assert f"(PID {pid})" in got.stdout, got.stdout
        assert not alive(pid), "the sqcli of a failed start is still alive"
        assert not (w / "user" / "log" / "OWNER").exists()
    finally:
        reap(w)


def test_stop_exits_1_when_the_worker_survives(root: Path) -> None:
    """A worker that takes the -exit and stays up: since 2026-10-06 `stop` kills it by PID once
    it has been silent (SIGTERM, then SIGKILL), says so, and exits 0 — it used to leave it up.
    "STILL RUNNING" and exit 1 are left for a kill that does not land (not reproducible here)."""
    sh, w = fake_root(root, "deaf")
    try:
        assert script(sh, "start").returncode == 0
        pid = int((w / "launched.pid").read_text())
        got = script(sh, "stop", SQX_STOP_WAIT="3")
        assert got.returncode == 0 and "killing by PID" in got.stdout, got.stdout + got.stderr
        assert str(pid) in got.stdout, got.stdout
        assert not alive(pid), "the deaf worker survived the kill"
    finally:
        reap(w)


def test_stop_sees_a_worker_whose_port_is_down(root: Path) -> None:
    """A live sqcli with no port (still booting, or hung): `stop` does not call it "not
    running": it says it could not reach it, then (since 2026-10-06) kills it by PID once it
    has been silent, and does not wait five minutes."""
    sh, w = fake_root(root, "noport")
    log = w / "user" / "log" / "worker-daemon.log"
    log.write_text("SQX CLI is now ready\n")      # skip the 30 s boot wait
    booting = subprocess.Popen(["./sqcli"], cwd=w)
    try:
        time.sleep(1)
        (w / "user" / "log" / "OWNER").write_text(
            json.dumps({"holder": "tester", "pid": booting.pid, "since": "now"}))
        began = time.time()
        got = script(sh, "stop")
        assert got.returncode == 0, got.stdout + got.stderr
        assert "not running" not in got.stdout and "could not reach" in got.stdout, got.stdout
        assert "killing by PID" in got.stdout, got.stdout
        assert time.time() - began < 120
        assert booting.wait(timeout=10) is not None
    finally:
        booting.kill()
        booting.wait()


if __name__ == "__main__":
    for test in (test_start_and_stop_succeed_as_before, test_concurrent_start_is_refused,
                 test_start_that_never_opens_its_port_is_killed,
                 test_stop_exits_1_when_the_worker_survives,
                 test_stop_sees_a_worker_whose_port_is_down):
        with tempfile.TemporaryDirectory() as scratch:
            began = time.time()
            test(Path(scratch))
        print(f"ok  {test.__name__}  {time.time() - began:.1f} s")
