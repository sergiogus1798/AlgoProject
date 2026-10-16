"""Encargo 66, the Python↔SQX bugs of the 2026-10-13 hunt, worker script, variants and exports: one test per fix, fakes only."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import worker
from sqx.export import export_metrics, export_retest, export_trades
from sqx.variants import execute, harness, legs as legmod, varianttrades
from tests.test_worker_lifecycle import ROOT, fake_root, reap, script


def _lock(w: Path, holder: str) -> None:
    """Write an OWNER lock by hand, as another session's `start` would."""
    (w / "user/log/OWNER").write_text(
        json.dumps({"holder": holder, "pid": 1, "since": "x"})
    )


def test_stop_drops_its_lock_before_the_export_and_keeps_a_newer_one(
    tmp_path: Path,
) -> None:
    """P1: the export finds no lock, and the lock another `start` wrote meanwhile survives the stop."""
    sh, w = fake_root(tmp_path, "serve")
    loader = sh.parents[1] / "ui/daemon/loader"
    loader.mkdir(parents=True)
    (
        loader / "afterrun.py"
    ).write_text(  # the export, during which another session starts
        "import json, pathlib\n"
        f"lock = pathlib.Path({str(w / 'user/log/OWNER')!r})\n"
        f"pathlib.Path({str(tmp_path / 'seen')!r}).write_text(str(lock.exists()))\n"
        "lock.write_text(json.dumps({'holder': 'other', 'pid': 1, 'since': 'x'}))\n"
    )
    try:
        assert script(sh, "start").returncode == 0
        got = script(sh, "stop")
        assert got.returncode == 0, got.stdout + got.stderr
    finally:
        reap(w)
    assert (tmp_path / "seen").read_text() == "False"
    assert json.loads((w / "user/log/OWNER").read_text())["holder"] == "other"


def test_a_lock_is_dropped_only_while_it_is_the_one_captured(tmp_path: Path) -> None:
    """P1, the «not running» branch: another lock, or a start in progress, is never removed."""
    w = tmp_path / "SQX_fake"
    (w / "user/log").mkdir(parents=True)
    lock = w / "user/log/OWNER"

    def drop(prepare: str) -> None:
        """Capture the lock's id, run `prepare`, then drop the lock if it is still that one."""
        subprocess.run(
            [
                "bash",
                "-c",
                f'WORKER="{w}"; running() {{ false; }}; '
                f'source "{ROOT}/bin/sqx-lock.sh"; ID=$(lock_id); {prepare}; '
                'drop_lock_if_same "$ID"; wait',
            ],
            check=True,
            timeout=30,
        )

    _lock(w, "mine")
    drop(f"""echo '{{"holder": "other", "pid": 2}}' > "{lock}" """)
    assert json.loads(lock.read_text())["holder"] == "other"
    _lock(w, "mine")
    drop(f'(flock 7; sleep 2) 7>"{w}/user/log/.start.lock" & sleep 0.5')
    assert lock.exists(), (
        "a start in progress holds .start.lock: the lock is its to write"
    )
    drop("true")
    assert not lock.exists()


def test_worker_run_exits_with_sqcli_code_and_stderr_is_not_a_path(
    tmp_path: Path,
) -> None:
    """P12: `run` returns sqcli's own code, and a Python warning on stderr is not read as MASTER."""
    sh, w = fake_root(tmp_path, "serve")
    paths = sh.parents[1] / "core/paths.py"
    paths.write_text(
        paths.read_text() + "import sys\nprint('UserWarning: x', file=sys.stderr)\n"
    )
    env = {"PATH": "/usr/bin:/bin", "HOME": os.environ["HOME"]}
    for code in (0, 3):
        (w / "sqcli").write_text(f"#!/bin/bash\necho DEBUG noise only\nexit {code}\n")
        got = subprocess.run(
            [str(sh), "run", "-project", "action=list"],
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )
        assert got.returncode == code, got.stdout + got.stderr
    assert (
        w / "user/data/data.db"
    ).read_text() == "bars"  # copied from the real MASTER


def test_export_retest_starts_from_an_empty_staging(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """P2: what a failed same-day export left staged is not packed into this batch."""
    work = tmp_path / "_staging" / "variants"
    for name in ("strategies/0__old.sqx", "raw/0__old.csv", "0/old.csv"):
        (work / name).parent.mkdir(parents=True, exist_ok=True)
        (work / name).write_text("stale")
    staged, packed = [], []

    def stage(
        project: str, db: str, dest: Path, limit: int, install: Path, prefix: str
    ) -> dict:
        """One strategy of the databank, copied as the real `stage` does."""
        dest.mkdir(parents=True, exist_ok=True)
        (dest / f"{prefix}new.sqx").write_text("n")
        return {"new": "H1"}

    def trades(sqx: Path, raw: Path, data: str) -> None:
        """orderstocsv: one CSV per staged file."""
        staged.extend(sorted(f.name for f in sqx.iterdir()))
        raw.mkdir()
        (raw / "0__new.csv").write_text("x")

    monkeypatch.setattr(
        export_retest, "export_dir", lambda p, db, day, batch="": tmp_path / db / batch
    )
    monkeypatch.setattr(export_retest, "worker_dir", lambda role: tmp_path)
    monkeypatch.setattr(export_retest, "stage", stage)
    monkeypatch.setattr(export_retest.exportdrv, "trades", trades)
    monkeypatch.setattr(
        export_retest,
        "pack",
        lambda raw, *a: packed.extend(sorted(f.name for f in raw.iterdir())),
    )
    monkeypatch.setattr(export_retest, "sign", lambda *a: 0)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "x",
            "--project",
            "Test_X",
            "--databank",
            "A",
            "--role",
            "custodian",
            "--batch",
            "variants",
        ],
    )
    export_retest.main()
    assert staged == ["0__new.sqx"] and packed == ["new.csv"]


def test_restart_route_ends_on_project_finished_and_checks_its_replies(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """P4: fewer retests than loaded end with the log's «Project finished»; a refused start or sync raises."""
    logs = tmp_path / "user/log/StrategyQuant"
    logs.mkdir(parents=True)
    log = logs / "log_2026_01_01.log"
    log.write_text("an earlier run: Project finished\n")
    cfg = {"role": "custodian", "project": "Test_X", "poll_seconds": 0, "sync_tries": 1}
    replies = {
        "start": "10:00:00 Starting project 'Test_X'",
        "status": iter(["In databank 10", "In databank 12"]),
    }

    def call(command: str, role: str = "conductor") -> str:
        """The start ends the project in the log at once; every status is the next scripted count."""
        if "action=start" in command:
            with log.open("a") as f:
                f.write("ProgressEngine - Project finished\n")
            return replies["start"]
        if "synctofiles" in command:
            return "Error: Databank 'D' doesn't exist."
        return next(replies["status"])

    monkeypatch.setattr(worker, "call", call)
    monkeypatch.setattr(execute, "worker_dir", lambda role: tmp_path)
    monkeypatch.setattr(execute.time, "sleep", lambda s: None)
    assert execute.run(4, cfg, lambda pct, line: None) == 2
    replies.update(
        start="Error: Project has unresolved resources", status=iter(["In databank 10"])
    )
    with pytest.raises(SystemExit, match="rechazó"):
        execute.run(4, cfg, lambda pct, line: None)
    with pytest.raises(SystemExit, match="rechazó"):
        execute.synced(2, cfg, "D")


def test_variant_trades_refuse_no_export_and_another_batchs_export(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """P7: no export names the project; an export older than the batch's retest is not this batch's."""
    monkeypatch.setattr(
        varianttrades,
        "export_dir",
        lambda p, db, day, tag="": tmp_path / db / day / tag if day else tmp_path / db,
    )
    monkeypatch.setattr(varianttrades, "main_feed", lambda p: "F")
    work = tmp_path / "work"
    work.mkdir()
    with pytest.raises(SystemExit, match="Test_X: ningún export"):
        varianttrades.gather(work, "Test_X")
    for leg in legmod.legs():
        old = (
            tmp_path
            / leg["databank"]
            / "2000-01-02"
            / varianttrades.TAG
            / "trades.parquet"
        )
        old.parent.mkdir(parents=True)
        pd.DataFrame({"Symbol": ["F"], "strategy": ["a"]}).to_parquet(old)
        os.utime(old, (1e9, 1e9))
    (work / "ran.json").write_text("{}")
    with pytest.raises(SystemExit, match="anterior al retest"):
        varianttrades.gather(work, "Test_X")
    assert not (work / varianttrades.OUT).exists() and old.exists()


def test_export_trades_refuses_an_empty_databank_and_finds_a_bracketed_name(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """P12: nothing is written for an empty databank; a `[1]` in a file name is not a glob class."""
    (tmp_path / "db").mkdir()
    monkeypatch.setattr(
        export_trades, "databank_dir", lambda p, db, install: tmp_path / "db"
    )
    monkeypatch.setattr(
        export_trades, "export_dir", lambda p, db, day: tmp_path / "out"
    )
    monkeypatch.setattr(
        sys, "argv", ["x", "--project", "Test_X", "--databank", "A", "--symbol", "S"]
    )
    with pytest.raises(SystemExit, match="Test_X/A: ningún .sqx"):
        export_trades.main()
    assert not (tmp_path / "out").exists()

    for folder in ("staged", "databanks/B"):
        (tmp_path / folder).mkdir(parents=True)
        (tmp_path / folder / "S [1].sqx").write_text("x")
    monkeypatch.setattr(export_trades, "project_dir", lambda p, install: tmp_path)
    monkeypatch.setattr(export_trades.sqxfile, "identity", lambda f: f.parent.name)
    monkeypatch.setattr(export_trades, "_LINEAGE", ("Test_X", "A", tmp_path))
    assert export_trades._mother(tmp_path / "staged/S [1].sqx") == ("staged", "B")


def test_export_metrics_leaves_a_subfolder_alone(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """P12: another export's folder inside the metrics folder no longer ends it in IsADirectoryError."""
    out = tmp_path / "out"
    (out / "sub").mkdir(parents=True)
    (out / "old.csv").write_text("x")
    monkeypatch.setattr(export_metrics, "metrics_export", lambda p, db: out)
    monkeypatch.setattr(
        export_metrics, "databank_dir", lambda p, db, install: tmp_path / "db"
    )
    monkeypatch.setattr(export_metrics.sqxview, "frame", lambda files: pd.DataFrame())
    monkeypatch.setattr(export_metrics.manifest, "write", lambda *a, **k: None)
    monkeypatch.setattr(sys, "argv", ["x", "--project", "Test_X", "--databank", "A"])
    export_metrics.main()
    assert sorted(f.name for f in out.iterdir()) == ["metrics.csv", "sub"]


def test_an_spp_tag_the_task_lacks_is_a_refusal() -> None:
    """P12: `harness.spp` on a task without Steps (the donor's «Retest») raises, never half-configures."""
    task = (
        '<CrossChecks use="true"><OptProfileSysParamPermutation use="false"><MaxTests>5</MaxTests>'
        "</OptProfileSysParamPermutation></CrossChecks>"
    )
    with pytest.raises(SystemExit, match="DistributionUp"):
        harness.spp(task, 35, 4.0, 15000)
