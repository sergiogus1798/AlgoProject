"""Encargo 66, the Python↔SQX connection: one test per launcher bug fixed, on fakes — no SQX is contacted."""

import json
import os
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mt5.verify import sqxside
from pipeline.autopilot import blind, entry, run
from sqx.projects import live, taskcap
from ui.daemon.advance import preflight, run as advance_run
from ui.daemon.launch import liverun
from ui.daemon.loader import afterrun

P = "Test_x"


def marker(path: Path, mtime: float) -> Path:
    """A file with a set date, its folder's too: a manifest.json, or a minimal .sqx (a zip)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("strategy.xml", "<s/>")
    os.utime(path, (mtime, mtime))
    os.utime(path.parent, (mtime, mtime))
    return path


@pytest.mark.parametrize(
    "lines, said, hours",
    [
        (
            ["ProgressEngine - MCR 6 Exits : ================"],
            "SQX no avanza: «MCR 6 Exits»",
            48,
        ),
        (
            ["10:00:02 Exception in task X"],
            f"SQX abortó {P}: 10:00:02 Exception in task X",
            48,
        ),
        (["10:00:02 java.lang.OutOfMemoryError: heap"], f"SQX abortó {P}", 48),
        (
            ["ProgressEngine - Project stopped"],
            f"SQX abortó {P}",
            48,
        ),  # a stop this watcher did not send
        (["10:00:03 Starting project 'Other'"], "sigue sin «Project finished»", 0),
    ],
)
def test_watch_ends_on_a_hung_task_every_abort_line_and_its_hours(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    lines: list[str],
    said: str,
    hours: int,
) -> None:
    """The `--restart` route's watch has the live route's ends: a task past its deadline, each
    line of `live.BAD`, and MAX_HOURS even when another project's start took the log."""
    polls = iter(
        range(20)
    )  # a watch that never ends fails the test instead of hanging it
    monkeypatch.setattr(
        preflight, "WORKERS", {"custodian": {"path": tmp_path, "port": 1}}
    )
    monkeypatch.setattr(advance_run.worker, "holding", lambda top: [1])
    monkeypatch.setattr(
        advance_run.progress,
        "state",
        lambda role, project: {"status": None, "tasks": []},
    )
    monkeypatch.setattr(advance_run.time, "sleep", lambda s: next(polls))
    monkeypatch.setattr(advance_run, "MAX_HOURS", hours)
    monkeypatch.setattr(taskcap, "_history", lambda: tmp_path / "task-durations.json")
    monkeypatch.setattr(
        taskcap, "UNKNOWN", -1
    )  # a title never seen is past its deadline at once
    log = advance_run.sqxlog.path(tmp_path, advance_run.date.today())
    log.parent.mkdir(parents=True)
    log.write_text("\n".join([f"10:00:00 Starting project '{P}'", *lines]) + "\n")
    with pytest.raises(SystemExit) as end:
        advance_run.watch(P, "custodian", {})
    assert said in str(end.value), end.value


def autopilot_fakes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, todo: list[dict]
) -> list:
    """`run.autopilot` on a fake worker and a given plan; the calls to `liverun.close`."""
    closed = []
    monkeypatch.setattr(run.advance, "where", lambda p: {"role": "custodian"})
    monkeypatch.setattr(run.advance, "busy", lambda *a: [])
    monkeypatch.setattr(
        run.advance, "WORKERS", {"custodian": {"path": tmp_path, "port": 1}}
    )
    monkeypatch.setattr(run.workflow, "workflow", lambda p: {"asset": "X", "steps": []})
    monkeypatch.setattr(
        run.plan,
        "plan",
        lambda data, given: {"do": todo, "stop": {"n": "26", "why": "x"}},
    )
    monkeypatch.setattr(run.plan, "scanned", lambda *a: None)
    monkeypatch.setattr(run.judge, "settings", lambda: {"steps": {}})
    monkeypatch.setattr(run.liverun, "close", lambda *a: closed.append(a))
    return closed


def test_a_failed_start_is_a_clear_failure_and_stops_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`live.start` failing: estado.txt says FALLO with its words and that the session is still
    up with incomplete memory; no sync, no export, no stop."""
    why = "custodian: los databanks no terminaron de cargarse en 5 min; no se toca nada"
    closed = autopilot_fakes(monkeypatch, tmp_path, [])
    stopped = []
    monkeypatch.setattr(
        live, "start", lambda role, *a, **k: (_ for _ in ()).throw(SystemExit(why))
    )
    monkeypatch.setattr(live, "stop", lambda *a, **k: stopped.append(a))
    monkeypatch.setattr(live, "gui_up", lambda role: True)
    monkeypatch.setattr(live, "mine", lambda role: True)
    with pytest.raises(SystemExit) as end:
        run.autopilot(P, tmp_path, on_live=True)
    state = (tmp_path / "estado.txt").read_text()
    assert str(end.value) == why and "FALLO en el arranque" in state and why in state, (
        state
    )
    assert (
        "SIGUE ARRIBA con la memoria incompleta" in state and "`stop` normal" in state
    ), state
    assert closed == [] and stopped == []


def test_one_autopilot_per_worker_and_no_adopted_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A second autopilot on the role is refused by the flock; a GUI session already up is
    refused naming its holder — while `busy` still lets the same holder's launchers through."""
    monkeypatch.setattr(entry, "autopilot_runs", lambda: tmp_path / "autopilot")
    monkeypatch.setattr(entry, "WORKERS", {"custodian": {"path": tmp_path}})
    monkeypatch.setattr(entry, "HELD", [])
    monkeypatch.setattr(live, "gui_up", lambda role: False)
    entry.alone("custodian")
    with pytest.raises(SystemExit, match="ya hay un autopiloto en el custodian"):
        entry.alone("custodian")
    entry.HELD.pop().close()  # the first run ended: its lock goes with it
    (tmp_path / "user/log").mkdir(parents=True)
    (tmp_path / "user/log/OWNER").write_text(
        json.dumps({"holder": "owner", "pid": 7, "since": "ayer"})
    )
    monkeypatch.setattr(live, "gui_up", lambda role: True)
    with pytest.raises(
        SystemExit, match="la tiene owner desde ayer, PID 7.*no la adopta"
    ):
        entry.alone("custodian")
    monkeypatch.setattr(live, "mine", lambda role: True)
    assert preflight.busy("custodian", P) == []


FAKE_PYTHON = """#!/bin/bash
echo "$*" >> "$FAKE/calls"
case "$*" in
  -c*project_dir*) echo "$FAKE/proj/project.cfx" ;;
  *sqx.projects.builder*) mkdir -p "$FAKE/proj" && touch "$FAKE/proj/project.cfx" ;;
  *sqx.projects.buildingblocks*) exit 1 ;;
  *sqx.projects.retire*) [[ -e $FAKE/retire_fails ]] && exit 1; rm -r "$FAKE/proj" ;;
esac
"""


def test_a_palette_that_fails_retires_the_project(tmp_path: Path) -> None:
    """bin/workflow.sh: the palette failing after the builder retires the project, so a retry
    creates it again; when the retire refuses, a marker makes «run» refuse the project."""
    fake = tmp_path / "python3"
    fake.write_text(FAKE_PYTHON)
    fake.chmod(0o755)  # every `python3` of the script is this one: nothing real runs
    env = {
        **os.environ,
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
        "FAKE": str(tmp_path),
    }
    make = [
        "bash",
        str(ROOT / "bin/workflow.sh"),
        "template",
        P,
        "XAUUSD",
        "H1",
        str(fake),
        "ruptura",
        "p",
        "10",
        "5",
    ]
    got = subprocess.run(make, env=env, capture_output=True, text=True)
    calls = (tmp_path / "calls").read_text()
    assert (
        got.returncode == 1
        and "no se aplicó la paleta ruptura" in got.stderr
        and "retirado" in got.stderr
    ), got.stderr
    assert f"-m sqx.projects.retire {P} --role custodian --yes --own" in calls, calls
    assert not (tmp_path / "proj").exists() and "pipeline.autopilot.run" not in calls
    (tmp_path / "retire_fails").touch()
    got = subprocess.run(make, env=env, capture_output=True, text=True)
    assert got.returncode == 1 and "NO se pudo retirar" in got.stderr, got.stderr
    again = subprocess.run(
        ["bash", str(ROOT / "bin/workflow.sh"), "run", P],
        env=env,
        capture_output=True,
        text=True,
    )
    assert again.returncode == 1 and "a medio crear" in again.stderr, again.stderr
    assert "pipeline.autopilot.run" not in (tmp_path / "calls").read_text()


def test_a_failed_export_fails_and_a_stale_wfm_is_exported_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`afterrun` exits 1 when a piece failed (the live route runs it with check=True), and step
    19 re-exports a WFM whose newest export is older than the matrix on disk."""
    failed = [1]
    monkeypatch.setattr(afterrun, "export", lambda role, only: failed[0])
    monkeypatch.setattr(afterrun, "MARK", tmp_path / "mark")
    monkeypatch.setattr(
        afterrun.progress, "installs", lambda: {"custodian": tmp_path}
    )  # nothing holds it
    monkeypatch.setattr(
        sys, "argv", ["afterrun", "--role", "custodian", "--live", "--project", P]
    )
    monkeypatch.delenv("ALGO_NO_EXPORT", raising=False)
    with pytest.raises(SystemExit) as end:
        afterrun.main()
    assert end.value.code == 1
    failed[0] = 0
    afterrun.main()
    ran, now = [], time.time()
    monkeypatch.setattr(blind, "bank", lambda project: "WFM")
    monkeypatch.setattr(blind, "DATA", tmp_path)
    monkeypatch.setattr(blind, "worker_dir", lambda role: tmp_path)
    monkeypatch.setattr(
        blind, "databank_dir", lambda p, b, top: tmp_path / "databanks" / b
    )
    monkeypatch.setattr(blind.call, "run", lambda argv: ran.append(argv[1]))
    marker(tmp_path / "databanks/WFM/S1.sqx", now - 50)
    done = marker(tmp_path / "raw" / P / "WFM/2026-10-12/wfm/manifest.json", now - 100)
    blind.wfm(P, "custodian")
    assert ran == ["sqx.export.export_wfm", "studies.optimisation.wfm.report"], ran
    del ran[:]
    marker(done, now)
    blind.wfm(P, "custodian")
    assert ran == ["studies.optimisation.wfm.report"], ran


def test_a_load_or_a_sync_that_failed_is_not_an_empty_retest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Step 26's SQX half: SQX refusing the load, or nothing on disk after the sync, raises
    naming the databank — and the worker is stopped either way."""
    replies, stops = {"load": "Error: Databank 'In' doesn't exist."}, []
    strategy = tmp_path / "S.sqx"
    strategy.write_text("x")
    cfg = {"input": "In", "load_s": 0, "sync_tries": 2, "poll_s": 0}
    monkeypatch.setattr(
        sqxside, "WORKERS", {"conductor": {"path": tmp_path, "port": 1}}
    )
    monkeypatch.setattr(sqxside, "worker_dir", lambda role: tmp_path)
    monkeypatch.setattr(
        sqxside, "databank_dir", lambda p, b, top: tmp_path / "databanks" / b
    )
    for name in ("refuse_if_up", "mark", "stopped"):
        monkeypatch.setattr(sqxside.workerguard, name, lambda *a: None)
    monkeypatch.setattr(sqxside.worker, "start", lambda role: None)
    monkeypatch.setattr(sqxside.worker, "stop", lambda role, export: stops.append(role))
    monkeypatch.setattr(
        sqxside.worker,
        "call",
        lambda cmd, role: replies["load"] if "action=load" in cmd else "OK",
    )
    monkeypatch.setattr(sqxside.advance_run, "ready", lambda *a: None)
    monkeypatch.setattr(sqxside.advance_run, "watch", lambda *a: {})
    monkeypatch.setattr(sqxside.sqxlog, "mark", lambda top: {})
    monkeypatch.setattr(sqxside.live, "mark", lambda role: ())
    monkeypatch.setattr(sqxside.loadwait, "loaded", lambda *a: None)
    with pytest.raises(SystemExit, match="SQX rechazó `-databank action=load"):
        sqxside.run(
            P, "conductor", strategy, tmp_path / "work", {"ftmo": "Out FTMO"}, cfg
        )
    replies["load"] = "OK"
    with pytest.raises(
        SystemExit, match=r"Out FTMO \(ftmo\): nada en disco tras el sync"
    ):
        sqxside.run(
            P, "conductor", strategy, tmp_path / "work", {"ftmo": "Out FTMO"}, cfg
        )
    assert stops == ["conductor", "conductor"]


def test_close_after_a_failure_sets_aside_only_the_failed_actions_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`liverun.close` with no project log yet does not raise (it hid the real failure), a log
    older than the failed ACTION's start stays, and the autopilot passes that start, not the run's."""
    cfx = tmp_path / "project.cfx"
    (tmp_path / "log").mkdir()
    monkeypatch.setattr(liverun.exiting, "stop", lambda role, project: "fuera")
    monkeypatch.setattr(live, "stop", lambda *a, **k: None)
    monkeypatch.setattr(
        liverun.preflight, "tasks", lambda project: {"cfx": cfx, "tasks": []}
    )
    now = time.time()
    liverun.close(
        "custodian", P, {"n": "9", "steps": [], "since": now}
    )  # an empty glob
    old = marker(tmp_path / "log/global_log_1.log", now - 100)
    liverun.close("custodian", P, {"n": "9", "steps": [], "since": now})
    assert old.exists(), "the earlier step's log was set aside"
    liverun.close("custodian", P, {"n": "9", "steps": [], "since": now - 200})
    assert not old.exists() and (tmp_path / "log/global_log_1.log.descartado").exists()
    todo = [
        {"n": "11", "title": "t", "kind": "python", "tests": ["x"]},
        {"n": "13", "title": "s", "kind": "sqx", "tests": []},
    ]
    closed, first = autopilot_fakes(monkeypatch, tmp_path / "run", todo), []
    (tmp_path / "run").mkdir()
    monkeypatch.setattr(live, "start", lambda role, *a, **k: None)
    monkeypatch.setattr(live, "mine", lambda role: True)
    monkeypatch.setattr(
        run.chain,
        "python_step",
        lambda *a, **k: (time.sleep(0.05), first.append(time.time()), [])[2],
    )
    monkeypatch.setattr(run, "sqx_step", lambda *a: sys.exit("SQX no avanza"))
    with pytest.raises(SystemExit, match="SQX no avanza"):
        run.autopilot(P, tmp_path / "run", on_live=True)
    assert closed[0][2]["n"] == "13" and closed[0][2]["since"] >= first[0], closed


def test_the_newest_ingest_is_the_last_written_not_the_last_by_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The tenth MC ingest of a day (`<day>-10`) is the one compared with the databanks: by
    name `<day>-9` won, read as stale for ever, and the ingest was repeated at every step."""
    now = time.time()
    monkeypatch.setattr(afterrun, "DATA", tmp_path)
    marker(tmp_path / "user/projects" / P / "databanks/MCR 1 Bar/S1.sqx", now - 50)
    root = tmp_path / "raw" / P / "MCR_All"
    marker(root / "2026-10-13-9/manifest.json", now - 100)
    assert [n for n, _ in afterrun.extras(P, "custodian", tmp_path)] == [
        "ingesta MC Retest"
    ]
    marker(root / "2026-10-13-10/manifest.json", now)
    assert afterrun.extras(P, "custodian", tmp_path) == []


def run_live_execute(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    extra: list[str],
    fill: tuple = (),
    forced: list | None = None,
) -> set:
    """`liverun.execute` of step 11 on fakes; the banks handed to `export` (`forced` gets the sync's `force`)."""
    cfx = tmp_path / "project.cfx"
    cfx.write_bytes(b"x")
    pre = {
        "role": "custodian",
        "cfx": cfx,
        "row": {"symbol": "XAUUSD"},
        "fill": list(fill),
        "chosen": [{"title": "CrossTF", "output": "CrossTF", "type": "x"}],
    }
    exported: list = []
    for mod, name, fake in [
        (liverun, "say", lambda *a: None),
        (liverun, "assets", lambda *a: None),
        (liverun, "snapshot", lambda p: (None, {})),
        (liverun, "counts", lambda p: {}),
        (liverun, "compare", lambda *a: ""),
        (liverun, "export", lambda r, p, b: exported.append(b)),
        (liverun.configure, "run", lambda pre, say: []),
        (liverun.stage, "just", lambda *a: None),
        (liverun.crosstfload, "separate_titles", lambda staged: extra),
        (liverun.crosstfload, "fill", lambda *a: ""),
        (
            liverun.live,
            "sync",
            lambda *a, **k: (forced if forced is not None else []).append(
                k.get("force")
            ),
        ),
        (liverun.live, "added", lambda *a: False),
        (liverun.live, "load", lambda *a: 0),
        (liverun.live, "push", lambda *a: {}),
        (liverun.live, "run", lambda *a: None),
    ]:
        monkeypatch.setattr(mod, name, fake)
    liverun.execute(pre, P)
    return exported[0]


def test_step_11_exports_the_extra_timeframe_crosstf_banks_too(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Step 11 ran `CrossTF M30` and `CrossTF H4` but exported only `CrossTF`: step 11.5 then failed
    with «CrossTF_M30 no tiene export». The tasks are not in `chosen` (they exist after the fill)."""
    assert run_live_execute(monkeypatch, tmp_path, []) == {
        "CrossTF"
    }  # the old behaviour
    assert run_live_execute(monkeypatch, tmp_path, ["CrossTF M30", "CrossTF H4"]) == {
        "CrossTF",
        "CrossTF_M30",
        "CrossTF_H4",
    }


def test_step_11_syncs_the_bank_python_filled_before_its_dump(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`CrossTF_Input` is written by Python with a `<!--variant_id-->` stamp SQX drops on load: unless
    SQX rewrites it before the dump, memory and disk differ and the `.abk` is refused (🔬 2026-10-13)."""
    forced: list = []
    run_live_execute(monkeypatch, tmp_path, [], fill=("CrossTF_Input",), forced=forced)
    assert forced[-1] == {"CrossTF", "CrossTF_Input"}


def test_summary_lists_the_fallbacks_of_the_run(tmp_path: Path) -> None:
    """resumen.md ends with the heading and one line per `fallback` row; no rows, no heading."""
    from core import phases

    done = [{"n": "6", "kind": "sqx", "s": 1.0, "what": "x"}]
    stop = {"n": "", "why": "fin"}
    run.summary(tmp_path, "Test_X", done, stop)
    assert "Caídas" not in (tmp_path / "resumen.md").read_text()
    log = tmp_path / "fases.csv"
    log.write_text("")
    os.environ[phases.ENV] = str(log)
    try:
        phases.note("fallback", "Test_X/A: una")
        phases.note("fallback", "Test_X/B: dos")
    finally:
        del os.environ[phases.ENV]
    run.summary(tmp_path, "Test_X", done, stop)
    text = (tmp_path / "resumen.md").read_text()
    assert (
        "Caídas a la ruta lenta (2):" in text
        and "Test_X/A: una" in text
        and "Test_X/B: dos" in text
    )


def test_today_log_skips_a_log_sqx_deletes_while_starting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A log the glob listed and SQX deleted before its stat is skipped (gorilla, 2026-10-15)."""
    from pathlib import Path

    from sqx.projects import live

    logs = tmp_path / "user/log/StrategyQuant"
    logs.mkdir(parents=True)
    (logs / "log_2026_10_15.log").write_text("today")
    ghost = logs / "log_2026_10_12.log"
    real_glob = Path.glob
    monkeypatch.setattr(live, "_top", lambda role: tmp_path)
    monkeypatch.setattr(Path, "glob", lambda self, pat: [ghost, *real_glob(self, pat)])
    assert live._log("custodian").name == "log_2026_10_15.log"
