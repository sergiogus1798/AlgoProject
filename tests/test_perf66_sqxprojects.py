"""Encargo 66, the Python↔SQX bugs of the 2026-10-13 hunt, sqx/projects: one test per fix, fakes only."""

import json
import os
import sys
import zipfile
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.projects import (
    crosstfload,
    exiting,
    live,
    patch,
    registry,
    registryxml,
    retire,
    sessiondb,
    taskcap,
)
from sqx.projects.workflow import CROSSTF

SAVED = (
    "Databank 'Test_X/{}' saved - files before sync 2 / after sync 2 / saved 2 / removed 0 in "
    "0.1 s. Sync triggered by '{}'.\n"
)


def test_task_durations_merge_by_max_and_are_written_whole(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """P5: a second wait that never saw a title's record does not lower it, nor drop the other's titles."""
    f = tmp_path / "task-durations.json"
    monkeypatch.setattr(taskcap, "_history", lambda: f)
    a, b = taskcap.fresh(), taskcap.fresh()
    taskcap.note(a, "ProgressEngine - WFM : Task finished in 3623.00 s.")
    taskcap.note(b, "ProgressEngine - OOS : Task finished in 21.10 s.")
    taskcap.note(b, "ProgressEngine - WFM : Task finished in 10.00 s.")
    assert json.loads(f.read_text()) == {"WFM": 3623.0, "OOS": 21.1} == b["longest"]
    assert list(tmp_path.iterdir()) == [f]


def test_session_cache_is_refreshed_when_truncated(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """P6: a cut copy — newer than the source, shorter — is copied again, through a temporary."""
    source, cache = tmp_path / "data.db", tmp_path / "cache"
    source.write_bytes(b"x" * 100)
    cache.mkdir()
    (cache / "data.db").write_bytes(b"x" * 10)
    os.utime(cache / "data.db", (source.stat().st_mtime + 60,) * 2)
    monkeypatch.setattr(sessiondb, "SOURCE", source)
    monkeypatch.setattr(sessiondb, "cache_dir", lambda name: cache)
    assert sessiondb.copy().read_bytes() == b"x" * 100
    assert [f.name for f in cache.iterdir()] == ["data.db"]


def test_live_start_names_the_databanks_that_did_not_load(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """C1: the 5-minute refusal says which databank, with its files and its records."""
    monkeypatch.setattr(
        live.worker, "holding", lambda top: []
    )  # not the real custodian
    monkeypatch.setattr(live.subprocess, "run", lambda *a, **k: None)
    monkeypatch.setattr(live.loadwait, "booted", lambda role, launch, *a: launch())
    monkeypatch.setattr(
        live,
        "call",
        lambda role, action: {"projects": [{"name": "Test_A"}, {"name": "Builder"}]},
    )
    monkeypatch.setattr(live, "records", lambda role, p: {"Results": 5, "OOS": 2})
    monkeypatch.setattr(live, "_files", lambda p, role, b: {"Results": 5, "OOS": 0}[b])
    monkeypatch.setattr(live.time, "sleep", lambda s: None)
    killed = []
    monkeypatch.setattr(
        live, "kill", killed.append
    )  # the half-loaded session goes by PID
    with pytest.raises(SystemExit) as e:
        live.start("custodian")
    assert "Test_A/OOS: 0 ficheros, 2 en memoria" in str(
        e.value
    ) and "Results" not in str(e.value)
    assert killed == ["custodian"]


def test_a_half_loaded_session_is_killed_by_pid_and_never_asked_to_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """D32: SIGTERM, then SIGKILL to what is left, then the script's cleanup once nothing runs."""
    from sqx.projects import liveapi

    alive, sent, stopped = [[7, 8]], [], []
    monkeypatch.setattr(liveapi.worker, "holding", lambda top: list(alive[0]))
    monkeypatch.setattr(liveapi.time, "sleep", lambda s: None)

    def gone(pid: int, sig: int) -> None:
        """PID 7 dies on SIGTERM, PID 8 only on SIGKILL."""
        sent.append((pid, sig))
        alive[0] = [
            p
            for p in alive[0]
            if p != pid or (pid == 8 and sig == liveapi.signal.SIGTERM)
        ]

    monkeypatch.setattr(liveapi.os, "kill", gone)
    monkeypatch.setattr(
        liveapi.worker, "stop", lambda role, export: stopped.append((role, export))
    )
    liveapi.kill("custodian")
    assert sent == [
        (7, liveapi.signal.SIGTERM),
        (8, liveapi.signal.SIGTERM),
        (8, liveapi.signal.SIGKILL),
    ]
    assert stopped == [("custodian", False)]


def test_live_sync_forces_a_full_databank_and_refuses_an_unknown_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """P8: `force` syncs at equal counts and waits for SQX's «saved» line; a name SQX lacks raises."""
    bank = tmp_path / "user/projects/Test_X/databanks/Results"
    bank.mkdir(parents=True)
    for n in "ab":
        (bank / f"{n}.sqx").write_text(n)
    log, sent, logged = tmp_path / "log_2026_01_01.log", [], [True]
    log.write_text("")

    def call(role: str, action: str, **p: str) -> dict:
        """databankList, or one synchronizeDatabank that SQX logs when it ends."""
        if action == "databankList":
            return {
                "databanks": [
                    {
                        "name": "Results",
                        "records": 2,
                        "syncType": "Auto-sync every 1 hour",
                    },
                    {"name": "Pool", "records": 9, "syncType": "Auto-sync never"},
                ]
            }
        sent.append(p["databankName"])
        if logged[0]:
            with log.open("a") as f:
                f.write(
                    SAVED.format(
                        p["databankName"],
                        "API request project/synchronizeDatabank Test_X/Results.",
                    )
                )
        return {}

    monkeypatch.setattr(live, "_top", lambda role: tmp_path)
    monkeypatch.setattr(live, "_log", lambda role: log)
    monkeypatch.setattr(live, "call", call)
    monkeypatch.setattr(live.time, "sleep", lambda s: None)
    assert live.sync("custodian", "Test_X") == {"Results": 2} and sent == []
    assert live.sync("custodian", "Test_X", force={"Results", "Pool"}) == {"Results": 2}
    assert sent == ["Results"]  # «Auto-sync never» is left out, as before
    for wrong in ({"banks": ["Nope"]}, {"force": {"Nope"}}):
        with pytest.raises(SystemExit, match="Nope"):
            live.sync("custodian", "Test_X", **wrong)
    logged[0] = False
    with pytest.raises(SystemExit, match=r"sin «saved» en el log \['Results'\]"):
        live.sync("custodian", "Test_X", force={"Results"})


def test_a_source_changed_during_an_export_reads_stale(tmp_path: Path) -> None:
    """The judge cut the databank while the window exported it: the manifest is dated at the
    export's start, so the loader does not sign that export as fresh."""
    import time

    from core import manifest
    from ui.daemon.loader import state

    bank, out = tmp_path / "bank", tmp_path / "out"
    bank.mkdir(), out.mkdir()
    (bank / "a.sqx").write_text("a")
    began = time.time()
    time.sleep(0.05)
    (bank / "b.sqx").write_text("b")  # lands while the export runs
    late = manifest.write(out, {}, "x", {}, since=began)
    assert state.age(late, sorted(bank.glob("*.sqx"))) == "stale"
    assert (
        state.age(
            manifest.write(out, {}, "x", {}, since=time.time()),
            sorted(bank.glob("*.sqx")),
        )
        == "fresh"
    )


def test_exit_wait_follows_the_log_past_midnight(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """P9: a save logged in the next day's file is seen, so the session is killed and not left."""
    day1, day2 = tmp_path / "log_2026_01_01.log", tmp_path / "log_2026_01_02.log"
    day1.write_text("23:59 exiting\n")
    day2.write_text(SAVED.format("B", "Save all strategies before exiting"))
    killed = []
    monkeypatch.setattr(live, "mark", lambda role: (day1, 0))
    monkeypatch.setattr(live, "_log", lambda role: day2)
    monkeypatch.setattr(live, "_setting", lambda role, key: "1")
    monkeypatch.setattr(
        exiting.urllib.request, "urlopen", lambda *a, **k: open(os.devnull, "rb")
    )
    monkeypatch.setattr(exiting, "banks", lambda role, running: {("Test_X", "B")})
    monkeypatch.setattr(
        exiting.worker, "holding", lambda top: [] if killed else [4194999]
    )
    monkeypatch.setattr(
        exiting.os, "kill", lambda pid, sig: killed.append(pid)
    )  # never a real kill
    monkeypatch.setattr(exiting.time, "sleep", lambda s: None)
    monkeypatch.setattr(exiting, "PATIENCE", 5)
    assert "se mató por PID" in exiting.stop("custodian", "Test_Y") and killed == [
        4194999
    ]


def test_crosstf_refill_copies_first_and_refuses_an_empty_batch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """P10: a failed copy leaves the databank as it was; no sibling at all leaves it untouched."""
    bank, src = tmp_path / "db/CrossTF_Input", tmp_path / "src"
    for folder, names in ((bank, ("old", "keep")), (src, ("keep", "new"))):
        folder.mkdir(parents=True)
        for n in names:
            (folder / f"{n}.sqx").write_text(folder.name)
    with pytest.raises(FileNotFoundError):
        crosstfload.refill(bank, [src / "missing.sqx"])
    assert sorted(f.name for f in bank.iterdir()) == ["keep.sqx", "old.sqx"]

    for name, fake in (
        ("worker_dir", lambda role: tmp_path),
        ("members_of", lambda cfx: {"config.xml": b"", "T.xml": b""}),
        ("banks", lambda m: {}),
        ("feeders", lambda b: {}),
        ("member_of", lambda cfg, title: "T.xml"),
        ("doctrine", lambda: {"crosstf": {"timeframes": {"H1": ["H4"]}}}),
        ("crosstf_dir", lambda p, day: tmp_path / "batch"),
        ("databank_dir", lambda p, b, install: tmp_path / "db" / b),
    ):
        monkeypatch.setattr(crosstfload, name, fake)
    monkeypatch.setattr(crosstfload.crosstf, "main_chart", lambda t: ("S", "H1"))
    monkeypatch.setattr(crosstfload.crosstf, "wire", lambda *a: {"databanks": []})
    monkeypatch.setattr(
        crosstfload.registry, "rows", lambda: [{"name": "Test_X", "symbol": "S"}]
    )
    monkeypatch.setattr(
        crosstfload.scale, "fabricate", lambda *a: pd.DataFrame()
    )  # scaled nothing
    assert CROSSTF["input"] == bank.name
    with pytest.raises(SystemExit, match="ninguna hermana"):
        crosstfload.load_input("Test_X", "custodian", "2026-01-01", folder=src)
    assert sorted(f.name for f in bank.iterdir()) == ["keep.sqx", "old.sqx"]

    assert crosstfload.refill(bank, sorted(src.glob("*.sqx"))) == 2
    assert {f.name: f.read_text() for f in bank.iterdir()} == {
        "keep.sqx": "src",
        "new.sqx": "src",
    }


def test_install_template_is_whole_or_untouched(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """P11: a template that fails half-way leaves the installed one as it was, and no temporary."""
    target = tmp_path / "t.sqx"
    target.write_bytes(b"old")
    monkeypatch.setattr(
        patch.cfxio, "members", lambda f: {"a.xml": b"<x/>", "b.xml": b"\xff"}
    )
    with pytest.raises(UnicodeDecodeError):
        patch.install_template(tmp_path / "in.sqx", target)
    assert target.read_bytes() == b"old" and list(tmp_path.iterdir()) == [target]
    monkeypatch.setattr(
        patch.cfxio, "members", lambda f: {"a.xml": b"<x/>", "b.bin": b"\x00"}
    )
    patch.install_template(tmp_path / "in.sqx", target)
    assert zipfile.ZipFile(target).read("b.bin") == b"\x00" and list(
        tmp_path.iterdir()
    ) == [target]


def test_a_project_name_with_a_trailing_newline_is_refused() -> None:
    """C3: `$` matched before a final newline, and the HTTP command splits on whitespace."""
    assert registry.check_name("Test_x") is None
    assert registry.check_name("Test_x\n") is not None


def test_a_second_retire_the_same_day_keeps_the_first_archive(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """P12: the same name retired twice in a day gets a suffixed archive, not the first one's file."""
    folder, marks = tmp_path / "inst/user/projects/Test_X", []
    monkeypatch.setattr(retire, "installs", lambda: {"conductor": tmp_path / "inst"})
    monkeypatch.setattr(retire.cfxio, "held", lambda cfx: None)
    monkeypatch.setattr(
        retire, "describe", lambda f: {"tasks": 3, "mb": 1.0, "mtime": 0}
    )
    monkeypatch.setattr(retire.save, "unsaved", lambda name: [])
    monkeypatch.setattr(
        retire,
        "retired_project",
        lambda inst, name, day: tmp_path / "retired" / f"{name}-{day}.tar.gz",
    )
    monkeypatch.setattr(
        retire.registry, "mark_retired", lambda name, inst, out: marks.append(out)
    )
    for content in ("first", "second"):
        folder.mkdir(parents=True)
        (folder / "project.cfx").write_text(content)
        retire.retire("Test_X", "conductor", [], apply=True)
    assert len(set(marks)) == 2 and marks[1].endswith("_2.tar.gz")
    assert all(Path(m).exists() for m in marks)


def test_a_feed_with_no_instrument_is_no_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    """P12: a <Symbol> the registry does not know and that names no instrument is no AttributeError."""
    monkeypatch.setattr(registryxml, "_registry", lambda sql, args: None)
    text = '<Symbol name="X_M1"></Symbol><Instruments><InstrumentInfo instrument="Gone" /></Instruments>'
    assert 'instrument="Gone"' not in registryxml.refresh(text)
