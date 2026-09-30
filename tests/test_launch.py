"""«Lanzar en SQX» on a scratch install: its refusals, and the order of what it sends SQX."""

import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from sqx.projects import stage  # noqa: E402
from tests.test_advance import CALLS, P, fakes, tree  # noqa: E402
from ui.daemon.advance import preflight as advance  # noqa: E402
from ui.daemon.launch import api, run  # noqa: E402


def scratch(root: Path, install: str = "SQX_w1", role: str = "conductor") -> dict:
    """`test_advance`'s scratch install and fakes, under the role asked, runs.csv aside."""
    built = tree(root, install=install)
    advance.WORKERS = {role: advance.WORKERS.pop("conductor")}
    up = fakes(built)
    stage.just = lambda cfx_, on, expected=None: CALLS.append(("just", cfx_.parent.name, on))
    run.assets = lambda symbol: CALLS.append(("assets", symbol))
    run.SNAPSHOTS = root / "snapshots"
    run.template_runs = lambda: root / "runs.csv"
    return {**built, "up": up}


def client() -> TestClient:
    """A local app holding only the launch router; never the real daemon, never 8765."""
    app = FastAPI()
    app.include_router(api.ROUTER)
    return TestClient(app)


def test_master_refused(root: Path) -> None:
    """A project the registry puts on the master is refused before anything else."""
    scratch(root, install="SQX")
    got = client().get("/api/launch/preflight", params={"project": P, "task": "OOS"}).json()
    assert not got["ok"] and "maestro" in got["reasons"][0], got


def test_build_only_on_custodian(root: Path) -> None:
    """A build on the conductor is refused; the task list still shows every task."""
    scratch(root)
    c = client()
    listed = c.get("/api/launch/tasks", params={"project": P}).json()
    assert [t["title"] for t in listed["tasks"]] == ["CONSTRUCCION", "OOS", "SPP IS"], listed
    assert listed["tasks"][1]["n_in"] == 3, listed
    got = c.get("/api/launch/preflight", params={"project": P, "task": "CONSTRUCCION"}).json()
    assert not got["ok"] and any("custodio" in r for r in got["reasons"]), got
    got = c.get("/api/launch/preflight", params={"project": P, "task": "NOPE"}).json()
    assert not got["ok"] and any("NOPE" in r for r in got["reasons"]), got


def test_retest_happy_path(root: Path) -> None:
    """Assets check, snapshot, only that task on, start, only status until finished, stop;
    the snapshot is deleted when no other databank fell."""
    built = scratch(root)
    got = client().get("/api/launch/preflight", params={"project": P, "task": "OOS"}).json()
    assert got["ok"] and "«OOS» (Retest)" in got["text"] and "Results» (3" in got["text"], got
    run.launch(P, "OOS")
    kinds = [c[0] for c in CALLS if c[0] not in ("state", "call")]
    assert kinds == ["assets", "just", "start", "stop"], kinds
    assert next(c for c in CALLS if c[0] == "just")[1:] == (P, ["OOS"]), CALLS
    sent = [c[1] for c in CALLS if c[0] == "call"]
    launch = sent.index(f"-project action=start name={P}")
    assert all("action=status" in c for i, c in enumerate(sent) if i != launch), sent
    assert built["up"]["polls"] == 2 and not built["up"]["on"]
    assert not any((root / "snapshots" / P).iterdir()), "the snapshot must go when nothing fell"
    assert not (root / "runs.csv").exists(), "a retest is not a build: runs.csv untouched"


def test_build_records_run(root: Path) -> None:
    """A build on the custodian runs and writes its runs.csv row with the template's name."""
    scratch(root, install="SQX_w2", role="custodian")
    got = client().get("/api/launch/preflight",
                       params={"project": P, "task": "CONSTRUCCION"}).json()
    assert got["ok"] and "custodio" in got["text"], got
    run.launch(P, "CONSTRUCCION")
    rows = (root / "runs.csv").read_text(encoding="utf-8").splitlines()
    assert rows[1].startswith(f"fam,USDJPY,M30,{P},") and rows[1].split(",")[5] == "3", rows


def test_fallen_bank_keeps_snapshot(root: Path) -> None:
    """A databank the task does not write that lost files keeps the copy, and says so."""
    kept = root / "copy"
    kept.mkdir()
    line = run.compare({"Results": 3, "OOS": 0}, {"Results": 1, "OOS": 2}, "OOS", kept)
    assert "Results 3 → 1" in line and kept.exists(), line
    assert "borrado" in run.compare({"OOS": 0}, {"OOS": 2}, "OOS", kept) and not kept.exists()


if __name__ == "__main__":
    for test in (test_master_refused, test_build_only_on_custodian, test_retest_happy_path,
                 test_build_records_run, test_fallen_bank_keeps_snapshot):
        with tempfile.TemporaryDirectory() as tmp:
            began = time.time()
            test(Path(tmp))
        print(f"ok  {test.__name__}  {time.time() - began:.1f} s")
