"""Encargo 66 §7.1/7.4b: `live.start(project)` and the settle before any exit, over HTTP against the fake SQX."""

import threading
import time
from pathlib import Path

import pytest

from sqx.projects import live, presaving
from tests.test_perf66_fakesqx import FakeSqx, sqx  # noqa: F401  (the fixture)
from tests.test_perf66_sqxprojects import SAVED


class TwoProjects(FakeSqx):
    """The fake with a second project `Other` whose databank holds 2 strategies and has no file (still loading)."""

    sync_type = "Auto-sync every 1 hour"

    def answer(self, action: str, q: dict) -> dict:
        """`list` names both projects; `Other`'s databankList says 2 records."""
        if action == "list":
            return {"projects": [{"name": "Test_X"}, {"name": "Other"}]}
        if action == "databankList" and q["projectName"] == "Other":
            return {"databanks": [{"name": "O", "records": 2, "syncType": self.sync_type}]}
        if action == "synchronizeDatabank" and q["projectName"] == "Other":
            if getattr(self, "silent", False):
                if getattr(self, "drop", False):          # a dirty bank: the sync removes a file and writes no line
                    (self.top / "user/projects/Other/databanks/O/q.sqx").unlink()
                return {}
            with self.log.open("a") as f:
                f.write(SAVED.format("O", "API request").replace("Test_X", "Other"))
            return {}
        return super().answer(action, q)


@pytest.fixture
def two(sqx: FakeSqx, monkeypatch: pytest.MonkeyPatch) -> TwoProjects:  # noqa: F811
    """A TwoProjects serving the custodian, its script launch stubbed."""
    sqx.__class__ = TwoProjects
    monkeypatch.setattr(live.subprocess, "run", lambda *a, **k: None)
    return sqx


def load_other(two: TwoProjects) -> None:
    """`Other`'s two strategies reach the disk: it has finished loading."""
    (two.top / "user/projects/Other/databanks/O").mkdir(parents=True, exist_ok=True)
    for n in ("p", "q"):
        (two.top / "user/projects/Other/databanks/O" / f"{n}.sqx").write_text(n)


def test_start_waits_only_for_the_run_project_and_stop_waits_for_the_rest(
        two: TwoProjects, monkeypatch: pytest.MonkeyPatch) -> None:
    """7.4b: `start` returns with `Other` unloaded; a stop while it still is kills the session by PID, never exits it."""
    killed = []
    monkeypatch.setattr(presaving, "LOAD_S", 0)
    monkeypatch.setattr(presaving, "kill", killed.append)
    live.start("custodian", "Test_X")
    with pytest.raises(SystemExit, match="no cargaron"):
        live.stop("custodian")
    assert killed == ["custodian"] and not [c for c, _ in two.calls if c == "exitapp"]


def test_a_stale_unloaded_verdict_is_rechecked_at_the_stop(two: TwoProjects, monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail-before verified: `Other` timed out loading, then loaded; the stop finds it loaded -> no kill, normal exit."""
    killed, ran = [], []
    monkeypatch.setattr(presaving, "LOAD_S", 0)
    monkeypatch.setattr(presaving, "kill", killed.append)
    monkeypatch.setattr(live.subprocess, "run", lambda *a, **k: ran.append(a))
    live.start("custodian", "Test_X")
    presaving._RUNS["custodian"][0].join()
    assert "loaded_s" not in presaving._RUNS["custodian"][1]
    load_other(two)
    live.stop("custodian")
    assert not killed and ran[-1][0][-1] == "stop"


def test_the_run_own_project_diverging_mid_wait_gives_no_timeout_verdict(
        two: TwoProjects, monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail-before verified: a task fills the run's own databank (memory > files) while `Other` loads; all
    loaded at the stop -> no kill, no error. The project's own bank and «Auto-sync never» ones are not watched."""
    killed = []
    monkeypatch.setattr(presaving, "kill", killed.append)
    live.start("custodian", "Test_X")
    two.mem["B"].append("d")                       # memory ahead of the files, as a build does
    time.sleep(0.3)
    load_other(two)
    got = presaving.settle("custodian")
    assert not killed and "error" not in got


def test_an_auto_sync_never_bank_is_not_waited_for(two: TwoProjects, monkeypatch: pytest.MonkeyPatch) -> None:
    """`Other`'s only bank never reaches disk by design: the wait ends at once, no kill."""
    two.sync_type = "Auto-sync never"
    monkeypatch.setattr(presaving, "LOAD_S", 0)
    monkeypatch.setattr(presaving, "kill", lambda r: pytest.fail("killed"))
    live.start("custodian", "Test_X")
    assert "loaded_s" in presaving.settle("custodian")


def test_presave_syncs_only_the_other_projects_banks_and_waits_for_their_saved_lines(
        two: TwoProjects) -> None:
    """7.1: once `Other` has its file, ITS bank is synced and settled; the run's project is never synced."""
    load_other(two)
    live.start("custodian", "Test_X")
    got = presaving.settle("custodian")
    assert got["saved"]["banks"] == 1
    assert [(q["projectName"], q["databankName"]) for c, q in two.calls
            if c == "synchronizeDatabank"] == [("Other", "O")]


def test_presave_syncs_auto_sync_never_banks_without_blocking_on_a_missing_saved_line(
        two: TwoProjects, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    """A «never» bank of another project is saved too (files == memory); with no «saved» line the wait is bounded."""
    two.sync_type = "Auto-sync never"
    load_other(two)
    two.silent = True
    monkeypatch.setattr(presaving, "NEVER_S", 0.2)
    live.start("custodian", "Test_X")
    got = presaving.settle("custodian")
    assert got["saved"]["banks"] == 0 and "error" not in got and "sin «saved»" in capsys.readouterr().err
    assert [(q["projectName"], q["databankName"]) for c, q in two.calls
            if c == "synchronizeDatabank"] == [("Other", "O")]


@pytest.mark.parametrize("hang", [False, True])
def test_a_dead_or_hung_wait_never_exits_the_session_when_it_cannot_look(
        two: TwoProjects, monkeypatch: pytest.MonkeyPatch, hang: bool) -> None:
    """C1: the thread raising or hanging confirmed nothing; if the recheck cannot look either, no exit and no kill."""
    ran, killed, gate = [], [], threading.Event()

    def broken(role: str, project: str) -> dict:
        """An HTTP hiccup, or a call that never returns."""
        if hang:
            gate.wait(30)
        raise OSError("hiccup")

    monkeypatch.setattr(presaving, "_banks", broken)
    monkeypatch.setattr(presaving, "JOIN_S", 0.3)
    monkeypatch.setattr(presaving, "kill", killed.append)
    monkeypatch.setattr(live.subprocess, "run", lambda *a, **k: ran.append(a))
    live.start("custodian", "Test_X")
    with pytest.raises(OSError, match="hiccup"):
        live.stop("custodian")
    gate.set()
    assert not killed and not [a for a in ran if a[0][-1] == "stop"]


def test_a_dead_wait_with_another_project_still_unloaded_kills_by_pid(
        two: TwoProjects, monkeypatch: pytest.MonkeyPatch) -> None:
    """C1: the thread died on a hiccup; `Other` is still half-loaded at the stop -> kill by PID, never exitapp."""
    killed = []
    monkeypatch.setattr(presaving, "_work", lambda role, project, box, *a: box.update(error="hiccup"))
    monkeypatch.setattr(presaving, "kill", killed.append)
    live.start("custodian", "Test_X")
    with pytest.raises(SystemExit, match="hiccup"):
        live.stop("custodian")
    assert killed == ["custodian"] and not [c for c, _ in two.calls if c == "exitapp"]


def test_step_26_takes_a_synced_file_only_when_non_empty_and_unchanged_across_two_polls(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """11: a half-written .sqx (size 0, then growing) is not taken; the same size twice is."""
    from mt5.verify import sqxside
    cfg, sizes = {"sync_tries": 10, "poll_s": 0}, iter([5, 9, 9, 9])
    f = tmp_path / "a.sqx"
    f.write_text("")

    def grow(_: float) -> None:
        """SQX keeps writing: the file takes its next size at each poll."""
        f.write_text("x" * next(sizes, 9))

    monkeypatch.setattr(sqxside.time, "sleep", grow)
    assert sqxside.synced(tmp_path, cfg) and f.stat().st_size == 9
    assert not sqxside.synced(tmp_path / "empty", {"sync_tries": 3, "poll_s": 0})


def test_reconcile_and_verify_configs_carry_every_key_the_shared_sqx_side_reads() -> None:
    """4: `mt5.reconcile` hands its `sqx` block to `mt5.verify.sqxside.run`: both real files hold the keys it reads."""
    import re as _re
    import yaml
    from core.paths import ROOT
    keys = set(_re.findall(r'cfg\["(\w+)"\]|cfg\[\'(\w+)\'\]', (ROOT / "mt5/verify/sqxside.py").read_text()))
    keys = {a or b for a, b in keys}
    assert {"load_s", "sync_tries", "poll_s", "input"} <= keys
    for name in ("verify", "reconcile"):
        block = yaml.safe_load((ROOT / "mt5" / name / "config.yaml").read_text())["sqx"]
        assert keys <= set(block), (name, keys - set(block))
    assert "settle_s" not in yaml.safe_load((ROOT / "mt5/reconcile/config.yaml").read_text())["sqx"]


def test_presave_takes_a_silent_clean_bank_as_saved_and_a_silent_dirty_one_as_an_error(
        two: TwoProjects, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    """🔬 2026-10-13: nothing pending writes no line. files == memory after NEVER_S s: clean, logged; files differ: SAVE_S error."""
    load_other(two)
    two.silent = True
    monkeypatch.setattr(presaving, "NEVER_S", 0.2)
    live.start("custodian", "Test_X")
    got = presaving.settle("custodian")
    assert got["saved"]["banks"] == 0 and "error" not in got and "nada que guardar" in capsys.readouterr().err
    two.drop = True                                          # dirty: the sync leaves 1 file for 2 in memory
    load_other(two)
    monkeypatch.setattr(presaving, "SAVE_S", 0.6)
    live.start("custodian", "Test_X")
    assert "sin «saved»" in presaving.settle("custodian")["error"]
