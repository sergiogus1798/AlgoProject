"""Encargo 66: what bin/workflow.sh, bin/sqx-worker.sh and runner/batchrun.py say when something fails.

Real scripts, copied into a temp root, run against a fake `python3` (and a fake `sqcli`) on PATH:
no SQX, no install is touched."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAKE_PY_WORKFLOW = """#!/bin/bash
case "$1 $2" in
  "-c "*) echo "$FAKE/project.cfx" ;;
  "-m pipeline.autopilot.run") mkdir -p "$FAKE/out"; echo "carpeta del run: $FAKE/out"
      echo "10:00:00 FIN" > "$FAKE/out/estado.txt"; exit "${RUN_RC:-0}" ;;
  "-m sqx.projects.retire") echo "retire $*" >> "$FAKE/calls"; exit "${RETIRE_RC:-0}" ;;
esac
"""
FAKE_WORKER = '#!/bin/bash\necho "stop $*" >> "$FAKE/calls"\n'


def workflow(tmp_path: Path, project: str, run_rc: int = 0, retire_rc: int = 0,
             extra: tuple = ()) -> tuple[subprocess.CompletedProcess, list[str]]:
    """`workflow.sh run <project>` on fakes; returns (completed process, the calls it made)."""
    root = tmp_path / "root"
    (root / "bin").mkdir(parents=True)
    shutil.copy(ROOT / "bin/workflow.sh", root / "bin/workflow.sh")
    fake = tmp_path / "fake"
    (fake / "bin").mkdir(parents=True)
    (fake / "project.cfx").write_text("x")
    for path, body in ((fake / "bin/python3", FAKE_PY_WORKFLOW), (root / "bin/sqx-worker.sh", FAKE_WORKER)):
        path.write_text(body)
        path.chmod(0o755)
    env = os.environ | {"PATH": f"{fake / 'bin'}:{os.environ['PATH']}", "FAKE": str(fake),
                        "RUN_RC": str(run_rc), "RETIRE_RC": str(retire_rc)}
    done = subprocess.run(["bash", str(root / "bin/workflow.sh"), "run", project, *extra],
                          capture_output=True, text=True, env=env, timeout=60)
    calls = (fake / "calls").read_text().splitlines() if (fake / "calls").exists() else []
    return done, calls


def test_test_project_is_stopped_then_retired_after_a_good_run(tmp_path: Path) -> None:
    """A good run of a Test_ project stops the worker, then retires the project."""
    done, calls = workflow(tmp_path, "Test_a")
    assert done.returncode == 0, done.stderr
    assert [c.split()[0] for c in calls] == ["stop", "retire"]
    assert "Test_a --role custodian --yes" in calls[1] and "--drop-unsaved" not in calls[1]


def test_retire_argv_of_the_script_passes_the_real_freshness_refusal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The argv workflow.sh sends, fed to the REAL retire.main on a project changed seconds ago."""
    import zipfile

    from sqx.projects import retire as rt
    _, calls = workflow(tmp_path, "Test_a")
    argv = calls[1].split()[1:]
    assert argv[:1] == ["-m"] and "--own" in argv
    inst = tmp_path / "inst"
    proj = inst / "user/projects/Test_a"
    proj.mkdir(parents=True)
    with zipfile.ZipFile(proj / "project.cfx", "w") as z:
        z.writestr("config.xml", "<c><Tasks><T/></Tasks></c>")
    monkeypatch.setattr(rt, "installs", lambda: {"custodian": inst})
    monkeypatch.setattr(rt.cfxio, "held", lambda f: False)
    monkeypatch.setattr(rt.save, "unsaved", lambda n: [])
    monkeypatch.setattr(rt, "retired_project", lambda i, n, d: tmp_path / "arch" / f"{n}.tar.gz")
    monkeypatch.setattr(rt.registry, "mark_retired", lambda *a: None)
    monkeypatch.setattr(sys, "argv", ["retire", *argv[2:]])
    rt.main()
    assert not proj.exists()
    proj.mkdir()
    with zipfile.ZipFile(proj / "project.cfx", "w") as z:
        z.writestr("config.xml", "<c><Tasks><T/></Tasks></c>")
    monkeypatch.setattr(sys, "argv", ["retire", *[a for a in argv[2:] if a != "--own"]])
    with pytest.raises(SystemExit):     # without --own the same fresh project is refused
        rt.main()


def test_until_run_is_not_retired(tmp_path: Path) -> None:
    """--until leaves a partial run alone."""
    done, calls = workflow(tmp_path, "Test_a", extra=("--until", "wfm"))
    assert done.returncode == 0 and calls == []
    assert "--until" in done.stderr


def test_failed_run_keeps_the_test_project_and_says_so(tmp_path: Path) -> None:
    """A failed run retires nothing and says so."""
    done, calls = workflow(tmp_path, "Test_a", run_rc=1)
    assert done.returncode == 1 and calls == []
    assert "NO se retira" in done.stderr


def test_retire_refusing_ends_non_zero_pointing_at_store_save(tmp_path: Path) -> None:
    """A refused retire exits non-zero and names store-save."""
    done, calls = workflow(tmp_path, "Test_a", retire_rc=1)
    assert done.returncode != 0
    assert "/store-save" in done.stderr


@pytest.mark.parametrize("project", ["Trade_a", "Research_a"])
def test_other_projects_are_never_retired(tmp_path: Path, project: str) -> None:
    """Only Test_ projects are retired."""
    done, calls = workflow(tmp_path, project)
    assert done.returncode == 0 and calls == []


FAKE_PY_WORKER = """#!/bin/bash
case "$1" in
  -c) printf '%s\\n' "$FAKE/master" "$FAKE/worker" 59999 ;;
  -m) [ "$2" = ui.daemon.loader.afterrun ] && exit 1 ;;
esac
exit 0
"""


@pytest.mark.parametrize("blocked", [False, True])
def test_stop_survives_a_failed_export_but_says_it(tmp_path: Path, blocked: bool) -> None:
    """Fake `sqcli` alive for 1 s in the install: the stop waits it out, the export fails.

    `blocked`: FALLO-export.txt is a directory, so the append fails too -- still exit 0."""
    fake = tmp_path / "fake"
    root = tmp_path / "root"
    (root / "bin").mkdir(parents=True)
    for name in ("sqx-worker.sh", "sqx-lock.sh"):
        shutil.copy(ROOT / "bin" / name, root / "bin" / name)
    (root / "bin/sqx-log-prune.sh").write_text("#!/bin/bash\n")
    (root / "bin/sqx-log-prune.sh").chmod(0o755)
    worker = fake / "worker"
    (worker / "user/log").mkdir(parents=True)
    (worker / "user/log/worker-daemon.log").write_text("CLI is now ready\n")
    if blocked:
        (worker / "user/log/FALLO-export.txt").mkdir()
    run = fake / "data/autopilot/Test_a/20261013-100000"
    run.mkdir(parents=True)
    (run / "estado.txt").write_text("10:00:00 FIN\n")
    (fake / "bin").mkdir()
    for name, body in (("python3", FAKE_PY_WORKER), ("sqcli", "#!/bin/bash\nsleep 1.5\n")):
        (fake / "bin" / name).write_text(body)
        (fake / "bin" / name).chmod(0o755)
    env = os.environ | {"PATH": f"{fake / 'bin'}:{os.environ['PATH']}", "FAKE": str(fake),
                        "CLAUDE_CODE_SESSION_ID": "t"}
    proc = subprocess.Popen([str(fake / "bin/sqcli")], cwd=worker)
    try:
        done = subprocess.run(["bash", str(root / "bin/sqx-worker.sh"), "--role", "custodian", "stop"],
                              capture_output=True, text=True, env=env, timeout=90)
    finally:
        proc.kill()
    assert done.returncode == 0, done.stdout + done.stderr
    assert "FALLO" in done.stderr
    if not blocked:
        assert "FALLO" in (worker / "user/log/FALLO-export.txt").read_text()
    assert "FALLO" not in (run / "estado.txt").read_text(), "a run of another role must stay untouched"


def test_batchrun_names_the_failed_and_exits_zero_unless_all_fail(tmp_path: Path) -> None:
    """The batch runner exits 0 unless every strategy fails, naming the failed ones."""
    mod = tmp_path / "failer_mod.py"
    mod.write_text("import sys\nif __name__ == '__main__':\n    sys.exit(int(sys.argv[1]))\n")

    def batch(codes: list[int]) -> subprocess.CompletedProcess:
        """Run a plan whose strategies exit with `codes`."""
        plan = tmp_path / f"plan{len(codes)}{sum(codes)}.json"
        plan.write_text(json.dumps([{"strategy": f"S{i}", "argv": ["-m", "failer_mod", str(c)]}
                                    for i, c in enumerate(codes)]))
        env = os.environ | {"PYTHONPATH": f"{tmp_path}:{ROOT}"}
        return subprocess.run([sys.executable, "-m", "ui.daemon.runner.batchrun", "--plan", str(plan),
                               "--workers", "2"], capture_output=True, text=True, cwd=ROOT, env=env, timeout=120)

    some = batch([0, 1, 0, 1, 0])
    assert some.returncode == 0, some.stderr
    assert "S1" in some.stderr and "S3" in some.stderr and "S0" not in some.stderr
    assert batch([1, 1]).returncode == 1


def _settle(alive_body: str, secs: int) -> subprocess.CompletedProcess:
    """Run `settle_wait` (cut out of the real script) against a fake `alive`."""
    fn = subprocess.run(["sed", "-n", "/^settle_wait()/,/^}/p", str(ROOT / "bin/sqx-worker.sh")],
                        capture_output=True, text=True).stdout
    return subprocess.run(["bash", "-c", f"ROLE=w; alive() {{ {alive_body}; }}\n{fn}\nsettle_wait {secs}"],
                          capture_output=True, text=True, timeout=30)


def test_settle_wait_returns_at_once_when_the_process_is_gone_and_fails_loud_at_timeout() -> None:
    """The 15 s sleep is a condition: gone -> exit 0 immediately; still there -> exit 1 naming it."""
    import time
    t0 = time.time()
    assert _settle("false", 15).returncode == 0 and time.time() - t0 < 3
    late = _settle("true", 2)
    assert late.returncode != 0 and "still waiting for the w process to exit" in late.stderr


def _xvfb_fn(name: str, extra: str, env: dict) -> subprocess.CompletedProcess:
    """Run functions cut out of the real script (`name`, plus `xvfb_wait`) with `extra` shell after them."""
    src = ROOT / "bin/sqx-worker.sh"
    fns = subprocess.run(["sed", "-n", r"/^XSOCK_DIR=/,/^}/p;/^xvfb_display()/p", str(src)],
                         capture_output=True, text=True).stdout
    return subprocess.run(["bash", "-c", f"CLI_PORT=5060\n{fns}\n{extra}"], capture_output=True, text=True,
                          timeout=30, env=os.environ | env)


def test_xvfb_wait_ignores_a_stale_socket_of_a_dead_xvfb_and_accepts_a_live_one(tmp_path: Path) -> None:
    """Socket present + PID dead -> fail at once; socket present + PID alive -> ok; alive but no socket -> times out."""
    import socket
    sock = socket.socket(socket.AF_UNIX)
    sock.bind(str(tmp_path / "X506"))                      # display :506 = port 5060 / 10
    env = {"SQX_X_SOCKET_DIR": str(tmp_path)}
    dead = _xvfb_fn("xvfb_wait", 'xvfb_wait :506 5 999999', env)
    assert dead.returncode == 1 and "died" in dead.stderr
    live = _xvfb_fn("xvfb_wait", 'sleep 30 & P=$!; xvfb_wait :506 5 $P; rc=$?; kill $P; exit $rc', env)
    assert live.returncode == 0
    (tmp_path / "X506").unlink()
    none = _xvfb_fn("xvfb_wait", 'sleep 30 & P=$!; xvfb_wait :506 2 $P; rc=$?; kill $P; exit $rc', env)
    assert none.returncode == 1 and "no socket" in none.stderr
    sock.close()
