"""«Continuar workflow» when things go wrong: every failure stops the worker it started."""

import shutil
import socket
import sys
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from tests.test_advance import CALLS, P, fakes, tree, write  # noqa: E402
from ui.daemon import progress  # noqa: E402
from ui.daemon.advance import api, preflight, run, sqxlog  # noqa: E402


def fails(built: dict, **how: object) -> str:
    """Run «Continuar» on a fake that goes wrong; it must fail AND stop the worker."""
    up = fakes(built, **how)
    try:
        run.advance(P, "Results")
    except (SystemExit, RuntimeError) as e:
        assert CALLS[-1] == ("stop", "conductor") and not up["on"], CALLS
        return str(e)
    raise AssertionError("it should have failed")


def test_start_refused(root: Path) -> None:
    """SQX answering `action=start` with an error: the job fails and the worker is stopped."""
    why = fails(tree(root), start_reply="Error: project not found")
    assert "rechazó `action=start`" in why, why


def test_start_never_logged(root: Path) -> None:
    """`action=start` accepted but no «Starting project» within the bound: fail, stop."""
    why = fails(tree(root), logs_start=False, within=0)
    assert "Starting project" in why, why


def test_start_fails_halfway(root: Path) -> None:
    """`worker.start` raising after the JVM came up still stops it (it is inside the try)."""
    why = fails(tree(root), start_fails=True)
    assert "failed to start" in why, why


def test_across_midnight(root: Path) -> None:
    """A run launched before midnight and finished after it: its start is in yesterday's
    file, its finish in today's, and an earlier finish in yesterday's file does not count."""
    top = root / "SQX_w1"
    yesterday = date.today() - timedelta(days=1)
    write(top, [f"22:00:00.000 Starting project '{P}'",
                "22:10:00.000 ProgressEngine - Project finished"], yesterday)
    offsets = sqxlog.mark(top)
    write(top, [f"23:59:00.000 Starting project '{P}'",
                "23:59:30.000 ProgressEngine - OOS : 10 %"], yesterday)
    kept: list[str] = []
    mid = progress.run_state(sqxlog.grow(top, offsets, kept))
    assert mid["project"] == P and not mid["finished"], mid
    write(top, ["00:20:00.000 ProgressEngine - OOS : Task finished",
                "00:20:01.000 ProgressEngine - Project finished"])
    end = progress.run_state(sqxlog.grow(top, offsets, kept))
    assert end["project"] == P and end["finished"] and end["events"] == {"OOS": "done"}, end


def test_no_template_skips_ledger(root: Path) -> None:
    """A project with no template in the registry is cut and run, and the ledger is skipped."""
    fakes(tree(root, template=""))
    run.advance(P, "Results")
    assert not any(c[0] == "ledger" for c in CALLS), CALLS
    assert CALLS[-1] == ("stop", "conductor"), CALLS


def test_second_refused_while_queued(root: Path) -> None:
    """A «Continuar» already queued or running refuses the next, and the POST starts nothing."""
    tree(root)
    queued, started = {"label": "advance", "rc": None, "project": P, "databank": "Results"}, []
    real, api.jobs = api.jobs, SimpleNamespace(
        listing=lambda: [queued], start=lambda *a, **k: started.append(a) or {"id": "x"})
    app = FastAPI()
    app.include_router(api.ROUTER)
    got = TestClient(app).post("/api/advance/run", json={"project": P, "databank": "Results"})
    api.jobs = real
    assert not got.json()["ok"] and any("ya hay" in r for r in got.json()["reasons"]), got.json()
    assert started == [], started


def test_copies_counted(root: Path) -> None:
    """One identity held under two names: the confirmation says how many files go."""
    built = tree(root)
    first = sorted(built["source"].glob("*.sqx"))[0]
    shutil.copy2(first, built["source"] / "Strategy copia(1).sqx")
    got = api.answer(P, "Results")
    assert got["ok"] and got["text"].endswith("(3 ficheros: SQX guarda algunas repetidas con "
                                              "otro nombre, y se borran todas las copias)"), got


def test_ready_waits_for_the_load(root: Path) -> None:
    """A task started while SQX still loads its databanks reads them empty (2026-09-29,
    «WFM : No strategies to retest»): `syncing` holds the start until the load is done."""
    f = sqxlog.path(root, date.today())
    f.parent.mkdir(parents=True)
    f.write_text("11:52:29 CLILogger - Syncing databank(s) from files\n"
                 "11:52:30 CLILogger - Loaded 21 strategies to databank Results\n")
    assert run.syncing(root), "loading: not ready"
    with f.open("a") as fh:
        fh.write("11:53:21 CLILogger - Synchronization finished.\n")
    assert not run.syncing(root), "loaded: ready"


def test_restore_after_sync_race(root: Path) -> None:
    """A strategy SQX logged «Cannot process strategy» for and then deleted comes back from the
    snapshot; one it did not name, and any in the run's own output, stay as they are."""
    from ui.daemon.launch import run as launch
    kept, live = root / "kept", root / "live"
    for top in (kept, live):
        for bank in ("Retest Markets - Family", "WFM"):
            (top / "databanks" / bank).mkdir(parents=True)
    for name in ("Strategy 9.11.67", "Strategy 1.1.1"):
        (kept / "databanks" / "Retest Markets - Family" / f"{name}.sqx").write_text("x")
    (kept / "databanks" / "WFM" / "Strategy 2.2.2.sqx").write_text("x")
    lines = ["13:04:05 ERROR StrategiesSaver - Cannot process strategy 'Strategy 9.11.67'",
             "13:04:06 ERROR StrategiesSaver - Cannot process strategy 'Strategy 2.2.2'"]
    back = launch.restore(live, kept, {"Retest Markets - Family": 2, "WFM": 1}, {"WFM"}, lines)
    assert back == ["Retest Markets - Family/Strategy 9.11.67"], back
    assert not (live / "databanks" / "Retest Markets - Family" / "Strategy 1.1.1.sqx").exists()


def test_busy_names_the_lock_holder(root: Path) -> None:
    """A port up with an owner lock on disk (OPEN.md §32) names who holds it, and since when."""
    built = tree(root)
    fakes(built)
    top = preflight.WORKERS["conductor"]["path"]
    owner = top / "user" / "log" / "OWNER"
    owner.parent.mkdir(parents=True, exist_ok=True)
    owner.write_text('{"holder": "sess-42", "pid": 1, "since": "2026-09-29T10:00:00"}',
                     encoding="utf-8")
    with socket.socket() as s:
        s.bind(("127.0.0.1", built["port"]))
        s.listen()
        reasons = preflight.busy("conductor", P)
    assert any("sess-42" in r and "2026-09-29T10:00:00" in r for r in reasons), reasons


def test_own_release(root: Path) -> None:
    """The 15-min quiet guard skips a log the window's own job last wrote (owner,
    2026-09-29), and only that: a write after the release is anyone's again."""
    from ui.daemon import workerguard
    workerguard.MARKS = root / "marks"
    assert not workerguard.own_last_write("custodian", time.time()), "no release yet"
    workerguard.mark("custodian", P)
    workerguard.release("custodian")
    assert not (workerguard.MARKS / "custodian.json").exists(), "the marker goes"
    assert workerguard.own_last_write("custodian", time.time() - 300), "written before"
    assert workerguard.own_last_write("custodian", time.time() + 30), "within the slack"
    assert not workerguard.own_last_write("custodian", time.time() + 120), "written after"
    assert workerguard.orphans(set()) == [], "a release is not an orphaned launch"


if __name__ == "__main__":
    for test in (test_start_refused, test_start_never_logged, test_start_fails_halfway,
                 test_across_midnight, test_no_template_skips_ledger,
                 test_second_refused_while_queued, test_copies_counted,
                 test_busy_names_the_lock_holder, test_own_release,
                 test_ready_waits_for_the_load, test_restore_after_sync_race):
        with tempfile.TemporaryDirectory() as scratch:
            began = time.time()
            test(Path(scratch))
        print(f"ok  {test.__name__}  {time.time() - began:.1f} s")
