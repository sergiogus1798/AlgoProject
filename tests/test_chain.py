"""«Correr workflow» and the per-step ▶ SQX on a scratch install: the stop rule, one start per step."""

import json
import os
import sys
import tempfile
import time
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from core import worker  # noqa: E402
from sqx.projects import stage  # noqa: E402
from tests.test_advance import CALLS, P  # noqa: E402
from tests.test_launch import scratch  # noqa: E402
from ui.daemon import jobs, workerguard  # noqa: E402
from ui.daemon.launch import api, chain, chainplan, run  # noqa: E402
from ui.daemon.launch import preflight as launch_preflight  # noqa: E402
from ui.daemon.workflow.steps import STEPS  # noqa: E402
from ui.daemon.workflow.tests import SPENDS  # noqa: E402

MCR = stage.titles("mcretest")
# (title, type, input, output, MC Retest on): a workflow project's chain, MCR 4 left off.
TASKS = ([("CONSTRUCCION", "Build", "", "Results", False), ("OOS", "Retest", "Results", "OOS", False)]
         + [(t, "Retest", "Results", t, t != "MCR 4 MinDist") for t in MCR]
         + [("SPP IS", "Retest", "Results", "SPP IS", False),
            ("SPP OOS", "Retest", "SPP IS", "SPP OOS", False)])


def workflow_cfx(path: Path) -> None:
    """Rewrite the scratch project.cfx with the tasks above, as `perturbations.disable` leaves one."""
    tags = "".join(f'<Task active="false" name="t{i}" taskXMLFile="t{i}.xml" title="{t}" '
                   f'type="{k}"/>' for i, (t, k, *_) in enumerate(TASKS))
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("config.xml", f"<Project><Tasks>{tags}</Tasks></Project>")
        for i, (_, _, src, out, mc) in enumerate(TASKS):
            z.writestr(f"t{i}.xml", f'<Settings><MonteCarloRetest use="{str(mc).lower()}"/>'
                                    f'<Databank name="Input" value="{src}"/>'
                                    f'<Databank name="Output" value="{out}"/></Settings>')


def rail(states: dict[str, str], tests_state: str = "pending") -> dict:
    """GET /api/workflow's shape for every step: `states` by number, the rest done.

    Each Python step carries its studies as tests, `auto` as `workflow.tests.one` sets it.
    """
    steps = []
    for s in STEPS:
        tests = [{"key": k, "runnable": True, "state": tests_state,
                  "auto": k not in SPENDS and s["feeds"] != ()} for k in s["studies"]]
        steps.append({"n": s["n"], "title": s["title"], "kind": s["kind"],
                      "state": states.get(s["n"], "done"), "tests": tests})
    return {"steps": steps}


def test_stop_rule(root: Path) -> None:
    """Runs straight from build to its analysis, stops before the next task after a judgement;
    only a press starting ON that task (its judge done) crosses it; a judge not done halts,
    whatever its tests; a running step halts; the oos2 steps and 21-25 never run."""
    got = chainplan.plan(rail({"6": "pending", "7": "pending", "9": "pending"}, "done"))
    assert [(a["n"], a["kind"]) for a in got["do"]] == [("6", "sqx"), ("7", "sqx"),
                                                        ("8", "python")], got
    assert got["do"][2]["tests"] == ["gate", "edgeCost", "feedQuality", "spread"], got
    assert got["stop"]["n"] == "9" and "decides tú" in got["stop"]["why"], got
    again = chainplan.plan(rail({"9": "pending", "10.5": "pending"}, "done"))
    assert [a["n"] for a in again["do"]] == ["9", "10"] and again["stop"]["n"] == "10.5", again
    mc = chainplan.plan(rail({"13": "pending", "15": "pending"}, "done"))
    assert [a["n"] for a in mc["do"]] == ["13", "14"] and mc["stop"]["n"] == "15", mc
    late = chainplan.plan(rail({"19": "pending"}))
    ran = {k for a in late["do"] for k in a["tests"]}
    assert not ran & set(SPENDS) and not {a["n"] for a in late["do"]} & {
        "17", "18", "18.5", "20", "21", "22", "23", "24", "25"}, late
    assert late["stop"]["n"] == "19" and "oos2" in late["stop"]["why"], late
    assert chainplan.plan(rail({"3": "missing"}))["do"] == []
    judge = chainplan.plan(rail({"8": "pending", "9": "pending"}))
    assert [a["n"] for a in judge["do"]] == ["8"] and judge["stop"]["n"] == "9", judge
    busy = chainplan.plan(rail({"11": "pending", "12": "running", "13": "pending"}, "done"))
    assert [a["n"] for a in busy["do"]] == ["11"] and busy["stop"]["n"] == "12", busy
    idle = chainplan.plan(rail({"8": "blocked", "9": "pending"}, "done"))
    assert idle["do"] == [] and idle["stop"]["n"] == "8", "a judge not done halts, tests or not"


def test_step_launch(root: Path) -> None:
    """▶ SQX of step 13: seven MCR tasks in ONE start, MCR 4 left off and said; step 15's
    SPP OOS reads what SPP IS writes in the same run, so its empty input is no refusal."""
    built = scratch(root)
    workerguard.MARKS = root / "marks"
    workflow_cfx(built["source"].parents[1] / "project.cfx")
    c = TestClient(FastAPI())
    c.app.include_router(api.ROUTER)
    got = c.get("/api/launch/preflight", params={"project": P, "step": "13"}).json()
    assert got["ok"] and got["titles"] == [t for t in MCR if t != "MCR 4 MinDist"], got
    assert "«MCR 4 MinDist» no se lanza" in got["text"], got["text"]
    spp = c.get("/api/launch/preflight", params={"project": P, "step": "15"}).json()
    assert spp["ok"], spp
    every = c.get("/api/launch/steps", params={"project": P}).json()["steps"]
    assert not every["6"]["ok"] and "custodio" in every["6"]["reasons"][0], every["6"]
    assert not every["16.5"]["ok"] and "/variants" in every["16.5"]["reasons"][0]
    run.launch(P, step="13")
    kinds = [x[0] for x in CALLS if x[0] not in ("state", "call")]
    assert kinds == ["assets", "just", "start", "stop"], kinds
    assert next(x for x in CALLS if x[0] == "just")[2] == got["titles"], CALLS


def test_chain_runs(root: Path) -> None:
    """The chain on the custodian: build, OOS, then step 8's tests — each SQX step one start
    and one stop, the second not refused for the log the first wrote — and nothing after."""
    built = scratch(root, install="SQX_w2", role="custodian")
    workerguard.MARKS = root / "marks"
    workflow_cfx(built["source"].parents[1] / "project.cfx")
    up = built["up"]
    start = worker.start

    def fresh(role: str = "custodian") -> None:
        """Each start writes its own «Starting project», then its own finish."""
        up.update(started=False, polls=0)
        start(role)

    worker.start = fresh
    chain.workflow.workflow = lambda p: rail({"6": "pending", "7": "pending", "9": "pending"})
    chain.workflow.context = lambda p: {"sqx": None}
    chain.rail.refusal = lambda n, k, ctx: None
    chain.rail.plan = lambda spec, k, ctx, db, picked: [{"label": k, "argv": ["-m", k],
                                                         "about": {}}]
    chain.command = lambda argv: (CALLS.append(("cmd", argv[1])), (0, ""))[1]
    got = chain.check(P)
    assert got["ok"], got
    assert "Se para antes del paso 9" in chain.text(got, P)
    chain.chain(P)
    kinds = [x[0] if x[0] != "cmd" else x[1] for x in CALLS if x[0] not in ("state", "call")]
    assert kinds == ["assets", "just", "start", "stop", "assets", "just", "start", "stop",
                     "gate", "edgeCost", "feedQuality", "spread"], kinds
    assert [x[2] for x in CALLS if x[0] == "just"] == [["CONSTRUCCION"], ["OOS"]], CALLS


def test_plan_diverged(root: Path) -> None:
    """The job runs the confirmed plan: a step whose state moved since is a halt, not a guess."""
    scratch(root, install="SQX_w2", role="custodian")
    chain.workflow.workflow = lambda p: rail({"6": "pending", "7": "pending"})
    confirmed = chain.check(P)["plan"]
    chain.workflow.workflow = lambda p: rail({"7": "pending"})       # 6 finished meanwhile
    try:
        chain.chain(P, confirmed)
        raise AssertionError("a moved step must stop the chain")
    except SystemExit as stop:
        assert "estaba «pending»" in str(stop), stop
    assert not [x for x in CALLS if x[0] in ("start", "just")], CALLS


def test_worker_guards(root: Path) -> None:
    """A worker up right before the start is never taken nor stopped; one still up after
    `stop` (sqx-worker.sh's «STILL RUNNING», rc 0) fails the run before anything is read."""
    built = scratch(root)
    workerguard.MARKS = root / "marks"
    pre = launch_preflight.check(P, "OOS")
    held = {"always": True}
    worker.holding = lambda top: [7] if held["always"] else []
    try:
        run.execute(pre, P)
        raise AssertionError("a worker already up must refuse")
    except SystemExit as stop:
        assert "ya estaba arrancado" in str(stop), stop
    assert not [x for x in CALLS if x[0] in ("start", "stop")], CALLS
    up = built["up"]
    worker.holding = lambda top: [7] if up["on"] or held["stuck"] else []
    held["stuck"] = False
    stop_ = worker.stop
    worker.stop = lambda role="conductor": (stop_(role), held.update(stuck=True))
    try:
        run.execute(pre, P)
        raise AssertionError("a worker that does not stop must fail the run")
    except SystemExit as stop:
        assert "no se paró" in str(stop), stop
    assert workerguard.marked("conductor")["pid"] == os.getpid(), "the marker stays while up"


def test_chain_refused(root: Path) -> None:
    """A launcher already queued refuses the chain, and the chain's job is a launcher too."""
    scratch(root, install="SQX_w2", role="custodian")
    chain.workflow.workflow = lambda p: rail({"7": "pending"})
    queued = [{"label": "advance", "rc": None, "project": "X", "databank": "Results"}]
    jobs.listing = lambda: queued
    got = api.chain_check(P)
    assert not got["ok"] and any("lanzamiento" in r for r in got["reasons"]), got
    started = []
    jobs.start = lambda label, argv, about, lane="python": started.append((label, lane)) or {
        "id": "1"}
    queued.clear()
    jobs.LOGS = root / "logs"
    shown = api.chain_check(P)["plan"]
    assert not api.chain_run(api.Chain(project=P, plan={"do": []}))["ok"], "another plan"
    assert api.chain_run(api.Chain(project=P, plan=shown))["job"] == "1"
    assert started == [("launch", "conductor")], started
    assert json.loads(next((root / "logs").glob("chain-*.json")).read_text()) == shown


if __name__ == "__main__":
    for test in (test_stop_rule, test_step_launch, test_chain_runs, test_plan_diverged,
                 test_worker_guards, test_chain_refused):
        with tempfile.TemporaryDirectory() as tmp:
            began = time.time()
            test(Path(tmp))
        print(f"ok  {test.__name__}  {time.time() - began:.1f} s")
