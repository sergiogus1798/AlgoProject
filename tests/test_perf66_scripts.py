"""Encargo 66, the shell and process launchers: the clone script and the one-autopilot lock."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def test_clone_script_reads_paths_from_stdout_only(tmp_path: Path) -> None:
    """bin/clone-sqx-worker.sh: a Python warning on stderr is not the master's path (it stops at «master not found»)."""
    fake = tmp_path / "python3"
    fake.write_text('#!/bin/bash\necho "Warning: noisy" >&2\necho "$FAKE/master"; echo "$FAKE/worker"; echo 5060\n')
    fake.chmod(0o755)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}", "FAKE": str(tmp_path)}
    got = subprocess.run(["bash", str(ROOT / "bin/clone-sqx-worker.sh"), "conductor"],
                         env=env, capture_output=True, text=True)
    assert got.returncode == 1 and f"master not found: {tmp_path}/master\n" in got.stdout, got.stdout
    assert "Warning" in got.stderr and "Warning" not in got.stdout


CHILD_ALONE = """
import sys, time
from pathlib import Path
from pipeline.autopilot import entry
entry.autopilot_runs = lambda: Path(sys.argv[1])
entry.live.gui_up = lambda role: False
entry.alone("custodian")
print("held", flush=True)
if sys.argv[2] == "hold":
    time.sleep(60)
"""


def test_alone_refuses_a_second_process_until_the_first_dies(tmp_path: Path) -> None:
    """entry.alone: the flock is per process — a second one exits saying so while the first lives; killing the first frees it."""
    def child(mode: str, **kw) -> subprocess.Popen:
        """Start a python process that takes the lock and either holds it or exits."""
        return subprocess.Popen([sys.executable, "-c", CHILD_ALONE, str(tmp_path), mode], cwd=ROOT,
                                env={**os.environ, "PYTHONPATH": str(ROOT)}, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kw)
    first = child("hold")
    try:
        assert first.stdout.readline() == "held\n"
        second = child("exit")
        out, err = second.communicate(timeout=60)
        assert second.returncode == 1 and "ya hay un autopiloto en el custodian" in err, (out, err)
        first.kill()
        first.wait()
        third = child("exit")
        assert third.communicate(timeout=60)[0] == "held\n" and third.returncode == 0
    finally:
        first.kill()
