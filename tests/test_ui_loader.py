"""The databank loader: what it finds stale, the lane each piece takes, failures never retried alone."""

import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from ui.daemon import jobs  # noqa: E402
from ui.daemon.loader import api, find, state  # noqa: E402

# A build databank with its oos1 retest, and a cross-market one, both on the custodian. Since
# F13 (2026-09-28) the fixture is the USDJPY Donchian project; when an install no longer holds
# them (the custodian kept only its WFM that day) the tests that read them say so and skip.
BUILD = ("Test_USDJPY_donchianUpperCrossUp_M30", "Results")
CROSS = ("Test_USDJPY_donchianUpperCrossUp_M30", "Retest_Markets_-_Family")
SLEEPER = ["-c", "import time; time.sleep(30)"]


def fake_jobs(listed: list[dict]) -> list:
    """Point the loader at a job list of our own and record what it starts instead."""
    started = []
    state.jobs = SimpleNamespace(listing=lambda: listed,
                                 start=lambda *a, **k: started.append((a, k)))
    return started


def test_status_and_lanes() -> None:
    """A build databank pairs with OOS and needs the conductor for trades and cosecha only;
    a cross-market one exports with data=all; the metrics never touch SQX."""
    fake_jobs([])
    now = state.status(*BUILD)
    assert (now["partner"], now["role"]) == ("OOS", "custodian") and now["strategies"], now
    todo = state.commands(BUILD[0], {**now, "pieces": {k: {"state": "missing"} for k in state.PIECES}})
    assert {k: lane for k, (lane, _) in todo.items()} == {
        "metrics": "python", "trades": "conductor", "harvest": "conductor"}, todo
    assert "sqx.export.export_trades" in todo["trades"][1] and "--symbol" in todo["trades"][1]
    cross = state.status(*CROSS)
    assert cross["databank"] == "Retest Markets - Family" and cross["pieces"]["harvest"]["state"] == "none"
    todo = state.commands(CROSS[0], {**cross, "pieces": {k: {"state": "missing"} for k in state.PIECES}})
    assert "sqx.export.export_retest" in todo["trades"][1], todo


def test_failure_and_retry() -> None:
    """A failed load stays failed and is not queued again until the owner retries."""
    failed = {"loader": "trades", "project": BUILD[0], "databank": BUILD[1], "rc": 1,
              "cancelled": False, "tail": ["REFUSING: another sqcli already holds SQX_w1."]}
    started = fake_jobs([failed])
    got = state.load(*BUILD)
    assert got["pieces"]["trades"]["state"] == "failed" and "REFUSING" in got["pieces"]["trades"]["why"]
    assert "trades" not in {a[2]["loader"] for a, _ in started}, started
    started.clear()
    state.load(*BUILD, retry=True)
    assert "trades" in {a[2]["loader"] for a, _ in started}, started


def test_writing_waits() -> None:
    """While SQX writes the project nothing is read or queued, and the roster is empty."""
    started = fake_jobs([])
    real = find.writing
    find.writing = lambda top, project: True
    try:
        got = state.load(*BUILD)
        assert got["writing"] and not started and not find.roster(*BUILD)
    finally:
        find.writing = real


def test_route_and_roster() -> None:
    """The routes answer, an unknown databank is a sentence, and the roster lists the files."""
    fake_jobs([])
    app = FastAPI()
    app.include_router(api.ROUTER)
    http = TestClient(app)
    held = http.get("/api/load", params={"project": BUILD[0], "databank": BUILD[1]}).json()
    assert "error" in http.get("/api/load", params={"project": "nope", "databank": "x"}).json()
    assert len(find.roster(*BUILD)) == held["strategies"] > 0


def test_conductor_one_at_a_time() -> None:
    """Two conductor jobs: the first runs, the second waits; python jobs are not held back."""
    ids = [jobs.start("cargar trades", SLEEPER, {"project": "p", "databank": "d", "strategy": ""},
                      lane="conductor")["id"] for _ in range(2)]
    light = jobs.start("profitShape", SLEEPER, {"project": "p", "databank": "d", "strategy": "s"})["id"]
    time.sleep(0.5)
    now = {j["id"]: j for j in jobs.listing()}
    assert now[ids[0]]["queued"] is None and now[ids[1]]["queued"] is not None, now
    assert now[light]["queued"] is None
    for i in (*ids, light):
        jobs.cancel(i)


def held() -> bool:
    """Whether an install holds both fixture databanks today."""
    fake_jobs([])
    return not any(state.status(*bank).get("error") for bank in (BUILD, CROSS))


def test_resave_is_not_a_change() -> None:
    """SQX's periodic sync rewrites every .sqx with a new date inside: the export stays fresh.
    A different strategy makes it stale (📓 2026-09-29: every stop re-exported everything)."""
    import tempfile
    import zipfile

    def save(f: Path, body: bytes, when: tuple) -> None:
        """Write a one-entry .sqx whose entry carries `when` as its date."""
        with zipfile.ZipFile(f, "w") as z:
            z.writestr(zipfile.ZipInfo("strategy_Portfolio.xml", when), body)

    with tempfile.TemporaryDirectory() as tmp:
        bank, out = Path(tmp) / "bank", Path(tmp) / "export"
        bank.mkdir(), out.mkdir()
        sqx = bank / "Strategy 1.1.1.sqx"
        save(sqx, b"<rules/>", (2026, 9, 29, 6, 47, 0))
        os.utime(sqx, (time.time() - 60,) * 2)
        os.utime(bank, (time.time() - 60,) * 2)
        done = out / "manifest.json"
        done.write_text("{}")
        assert state.age(done, [sqx]) == "fresh" and (out / "manifest.json.sources.sig").exists()
        save(sqx, b"<rules/>", (2026, 9, 29, 10, 52, 0))      # the resave: same content
        os.utime(sqx, (time.time() + 5,) * 2)
        assert state.age(done, [sqx]) == "fresh", "a resave alone is not a change"
        wfm = bank / "Strategy 2.2.2.sqx"
        keys = []
        for ref, when in (("4f573d92", 1), ("393e78e3", 2)):
            with zipfile.ZipFile(wfm, "w") as z:
                z.writestr("settings.xml", f'<R><Run stats="c.s.SQStats@{ref}" p="25"/></R>')
            os.utime(wfm, (time.time() + when,) * 2)
            keys.append(state.fingerprint([wfm]))
        assert keys[0] == keys[1], "a Java object address is not content"
        save(sqx, b"<other rules/>", (2026, 9, 29, 11, 0, 0))
        os.utime(sqx, (time.time() + 10,) * 2)
        assert state.age(done, [sqx]) == "stale", "new content is"


if __name__ == "__main__":
    tests = [test_conductor_one_at_a_time, test_resave_is_not_a_change]
    if held():
        tests = [test_status_and_lanes, test_failure_and_retry, test_writing_waits,
                 test_route_and_roster, *tests]
    else:
        print(f"    (ninguna instalación guarda {BUILD[0]} / {BUILD[1]} y {CROSS[1]}: los cuatro "
              "tests que leen un databank vivo con su OOS no corren; hace falta un proyecto "
              "con build + OOS + cross-market en el custodio)")
    for test in tests:
        started = time.time()
        test()
        print(f"ok  {test.__name__}  {time.time() - started:.1f} s")
