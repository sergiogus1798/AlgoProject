"""The window's run side: the python queue, cancel, the refusals, and with `--run` a real study
run end to end (it writes a report under AlgoData/reports/)."""

import sys
import tempfile
import time
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from core.paths import DATA, report_dir  # noqa: E402
from ui.daemon import jobs, jobsapi  # noqa: E402
from ui.daemon.runner import api, where  # noqa: E402

# Since F13 (2026-09-28): the USDJPY Donchian project. The strategy is read off the newest
# export rather than pinned by name: a nightly workflow re-run gives this project a fresh
# population under new names (📓 2026-09-30, T1 UI feedback pass — a hardcoded "Strategy
# 1.15.54" no longer existed in the export and made this test fail on unrelated grounds).
PROJECT, DATABANK = "Test_USDJPY_donchianUpperCrossUp_M30", "Results"
_export = where.newest(DATA / "raw" / PROJECT / DATABANK, "*/trades.parquet")
STRATEGY = pd.read_parquet(_export, columns=["strategy"])["strategy"].iloc[0]
# Job logs go here, not to AlgoData/logs/ui, and vanish with the test.
SCRATCH = tempfile.TemporaryDirectory(prefix="ui-runner-")
SLEEPER = ["-c", "import time; print('PROGRESS 40 a medias', flush=True); time.sleep(30)"]


def client() -> TestClient:
    """A local app with only the run routes and the job listing, logs in a scratch folder."""
    app = FastAPI()
    app.include_router(api.ROUTER)
    app.include_router(jobsapi.ROUTER)
    jobs.LOGS = Path(SCRATCH.name)
    jobs.JOBS.clear()
    return TestClient(app)


def listed(http: TestClient) -> dict[str, dict]:
    """Every job by id, as GET /api/jobs gives it."""
    return {j["id"]: j for j in http.get("/api/jobs").json()["jobs"]}


def wait(http: TestClient, job_id: str, seconds: float = 30) -> dict:
    """Poll one job until it has ended."""
    end = time.time() + seconds
    while time.time() < end:
        job = listed(http)[job_id]
        if job["rc"] is not None:
            return job
        time.sleep(0.2)
    raise AssertionError(f"{job_id} did not end in {seconds} s")


def test_real_run() -> None:
    """edgeCost on one strategy of a real harvest: percent reaches 100 and the result lands."""
    http = client()
    before = time.time()
    got = http.post("/api/study/run", json={
        "study": "edgeCost", "scope": "one", "project": PROJECT, "databank": DATABANK,
        "strategies": [STRATEGY], "asset": "USDJPY"}).json()
    assert "jobs" in got, got
    job = wait(http, got["jobs"][0]["id"])
    assert job["rc"] == 0 and job["percent"] == 100, job["tail"]
    assert (job["lane"], job["study"], job["scope"]) == ("python", "edgeCost", "one")
    landed = (report_dir(PROJECT, DATABANK, date.today().isoformat()) / "edgeCost"
              / "estrategias" / f"{STRATEGY}.json")
    assert landed.stat().st_mtime >= before, landed


def test_queue_and_cancel() -> None:
    """Two wide jobs fill the budget, the third waits; cancelling a runner starts the waiting
    one. Light jobs run sixteen at once and the seventeenth waits."""
    http = client()
    ids = [jobs.start("crossmarket", SLEEPER, {"project": "p", "databank": "d", "strategy": ""})["id"]
           for _ in range(3)]
    time.sleep(1)
    now = listed(http)
    assert [now[i]["queued"] for i in ids] == [None, None, 1], now
    assert now[ids[0]]["percent"] == 40 and now[ids[0]]["state"] == "a medias"
    assert now[ids[2]]["state"] == "en cola"
    assert http.post(f"/api/jobs/{ids[0]}/cancel").json() == {"ok": True}
    time.sleep(0.5)
    now = listed(http)
    assert now[ids[0]]["rc"] == jobs.CANCELLED and now[ids[0]]["state"] == "cancelado"
    assert now[ids[2]]["queued"] is None and now[ids[2]]["rc"] is None
    queued = jobs.start("crossmarket", SLEEPER, {"project": "p", "databank": "d", "strategy": ""})
    assert queued["queued"] == 1
    assert http.post(f"/api/jobs/{queued['id']}/cancel").json() == {"ok": True}
    assert http.post(f"/api/jobs/{queued['id']}/cancel").json() == {"ok": False}
    assert http.post("/api/jobs/nope/cancel").json() == {"ok": False}
    for i in ids[1:]:
        http.post(f"/api/jobs/{i}/cancel")
    light = [jobs.start("profitShape", SLEEPER, {"project": "p", "databank": "d", "strategy": "s"})["id"]
             for _ in range(jobs.SLOTS // jobs.LIGHT + 1)]
    now = listed(http)
    assert [now[i]["queued"] for i in light].count(None) == jobs.SLOTS // jobs.LIGHT, now
    assert now[light[-1]]["queued"] == 1
    for i in light:
        http.post(f"/api/jobs/{i}/cancel")
    assert all(j["rc"] is not None for j in listed(http).values())


def test_refusals() -> None:
    """What cannot run answers with a sentence and starts nothing. `jobs.start` is swapped for
    a recorder while this runs: a case the daemon wrongly accepted must not start a real study
    on a real project (📓 2026-09-28: blindJoint on the Donchian project was accepted and began).
    blindJoint is not asked here: whether it may run is the ledger's door on the data of the
    day, not a fixed refusal."""
    http = client()
    started, real = [], jobs.start
    jobs.start = lambda *a, **k: started.append(a) or {"id": "x"}
    body = {"project": PROJECT, "databank": DATABANK, "strategies": [STRATEGY], "asset": "USDJPY"}
    try:
        for study, scope, extra in [("profitShape", "many", {}), ("gate", "one", {}),
                                    ("gate", "many", {"only": "x"}), ("edgeCost", "one", {"asset": ""}),
                                    ("edgeCost", "one", {"asset": "NOPE"}), ("nope", "many", {})]:
            got = http.post("/api/study/run", json=body | {"study": study, "scope": scope} | extra)
            assert set(got.json()) == {"error"}, (study, got.json())
    finally:
        jobs.start = real
    assert started == [] and jobs.JOBS == []


def test_only_options() -> None:
    """crossmarket offers each non-base market of the export; other studies offer none."""
    http = client()
    got = http.get("/api/study/only", params={
        "study": "crossmarket", "project": PROJECT, "databank": "Retest_Markets_-_Family",
        "asset": "USDJPY"}).json()["options"]
    keys = [o["key"] for o in got]
    assert keys and "USDJPY_M1" not in keys, keys
    assert http.get("/api/study/only", params={"study": "gate"}).json() == {"options": []}


def test_offer() -> None:
    """On the build databank the tests whose data lives elsewhere are refused, with the jump
    to the databank their Databanks tab reads when it holds the same name, and a sentence when
    it does not; a study that can run on Results is not listed (owner, 2026-09-30)."""
    got = client().get("/api/study/offer", params={
        "project": PROJECT, "databank": DATABANK, "strategy": "Strategy 13.14.82",
        "asset": "USDJPY"}).json()["studies"]
    cross = got["crossmarket"]
    assert "cross-market" in cross["why"], cross
    # The project was retired from the custodian on 2026-09-30: with no install holding
    # Retest Markets there is no jump, only the sentence naming the databank.
    go = cross["go"]
    assert (go.get("tab") == "Cross Market" and go["identity"]
            if "databank" in go else "Retest_Markets_-_Family" in go["absent"]), go
    assert "MCR_All" in got["mcRetest"]["go"]["absent"], got["mcRetest"]
    assert "gate" not in got and "edgeCost" not in got, sorted(got)


if __name__ == "__main__":
    assert DATA.exists()
    tests = [test_refusals, test_only_options, test_offer, test_queue_and_cancel]
    if "--run" in sys.argv:
        tests.append(test_real_run)
    else:
        print("    (sin --run: test_real_run no corre edgeCost de verdad; escribiría un informe "
              "del día en AlgoData/reports/ de este proyecto)")
    for test in tests:
        started = time.time()
        test()
        print(f"ok  {test.__name__}  {time.time() - started:.1f} s")
