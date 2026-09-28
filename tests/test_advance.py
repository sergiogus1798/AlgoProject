"""«Continuar workflow» on a scratch install: its refusals, and the order of what it sends SQX."""

import os
import shutil
import socket
import sys
import tempfile
import time
import zipfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from core import sqxfile, worker  # noqa: E402
from core.paths import DATA  # noqa: E402
from ledger import record  # noqa: E402
from sqx.curate import apply_verdict  # noqa: E402
from sqx.projects import registry, stage  # noqa: E402
from ui.daemon import progress  # noqa: E402
from ui.daemon.advance import api, preflight, run, sqxlog  # noqa: E402
from ui.daemon.filters import discards, ledgerrow  # noqa: E402

# Three real strategies, copied into the scratch databank; nothing under an install is read.
SAMPLE = (DATA / "raw" / "Test_USDJPY_donchianUpperCrossUp_M30" / "SPP_IS" / "2026-09-27"
          / "strategies")
P, OTHER = "Test_UiFake", "Test_Otro"
TASKS = [("CONSTRUCCION", "Build", "", "Results"), ("OOS", "Retest", "Results", "OOS"),
         ("SPP IS", "Retest", "Results", "SPP IS")]
OLD = time.time() - 48 * 3600
CALLS: list[tuple] = []


def cfx(path: Path) -> None:
    """A project.cfx with the three tasks above, as SQX lays one out (config.xml + a file each)."""
    tags = "".join(f'<Task active="false" name="t{i}" taskXMLFile="t{i}.xml" title="{t}" '
                   f'type="{k}"/>' for i, (t, k, _, _) in enumerate(TASKS))
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("config.xml", f"<Project><Tasks>{tags}</Tasks></Project>")
        for i, (_, _, src, out) in enumerate(TASKS):
            z.writestr(f"t{i}.xml", f'<Settings><Databank name="Input" value="{src}"/>'
                                    f'<Databank name="Output" value="{out}"/></Settings>')


def age(folder: Path, when: float) -> None:
    """Set a project folder and everything under it to one modification time."""
    for p in [*folder.rglob("*"), folder]:
        os.utime(p, (when, when))


def free_port() -> int:
    """A loopback port nobody listens on right now."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def tree(root: Path, install: str = "SQX_w1", template: str = "fam/template.sqx") -> dict:
    """Build the scratch install and point every module at it.

    Returns:
        `source` (the databank folder), `top`, `dropped` (identity → name of the two
        discarded), `port`.
    """
    top, master = root / install, root / "SQX"
    source = top / "user/projects" / P / "databanks" / "Results"
    source.mkdir(parents=True)
    (master / "user/projects").mkdir(parents=True, exist_ok=True)
    for f in sorted(SAMPLE.glob("*.sqx")):
        shutil.copy2(f, source / f.name)
    cfx(source.parents[1] / "project.cfx")
    (top / "user/projects" / OTHER).mkdir()
    cfx(top / "user/projects" / OTHER / "project.cfx")
    age(top / "user/projects" / OTHER, OLD)
    port = free_port()
    preflight.WORKERS = {"conductor": {"path": top, "port": port}}
    preflight.MASTER, preflight.DISCARDS = master, root / "discards"
    registry.rows = lambda: [{"name": P, "install": install, "retired": "", "symbol": "USDJPY",
                              "timeframe": "M30",
                              "template": str(root / template) if template else ""}]
    discards.folder = lambda p, d: root / "filters" / p / d.replace(" ", "_")
    files = sorted(source.glob("*.sqx"))[:2]
    dropped = {sqxfile.identity(f): f.stem for f in files}
    discards.record(P, "Results", dropped, "filter", "Net profit (OOS) > 0", 3)
    return {"source": source, "top": top, "dropped": dropped, "port": port}


def write(top: Path, lines: list[str], day: date | None = None) -> None:
    """Append lines to the scratch install's SQX log of one day (today by default)."""
    f = sqxlog.path(top, day or date.today())
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("a", encoding="utf-8") as fh:
        fh.write("".join(line + "\n" for line in lines))


def fakes(built: dict, start_reply: str = "Project started", logs_start: bool = True,
          start_fails: bool = False, within: int = 120) -> dict:
    """Record every call that would reach SQX; SQX's log grows one step per status poll.

    Returns:
        The fake's state: `polls` after the launch, `on` whether the worker is up.
    """
    CALLS.clear()
    source, top = built["source"], built["top"]
    up = {"on": False, "started": False, "polls": 0}
    # An earlier run of the same project today, already finished: never this run's end.
    write(top, [f"06:00:00.000 Starting project '{P}'",
                "06:00:01.000 ProgressEngine - OOS : Task finished",
                "06:00:02.000 ProgressEngine - Project finished"])
    log = sqxlog.path(top, date.today())
    os.utime(log, (time.time() - 3600,) * 2)     # an hour old: the preflight's log is quiet

    def call(command: str, role: str = "conductor") -> str:
        """core.worker.call: record it; the CLI is ready at once."""
        CALLS.append(("call", command, role))
        if "action=start" in command:
            up["started"] = True
            return start_reply
        return "Strategies generated 0"

    def state(role: str, project: str) -> dict:
        """progress.state: send status as tasklog does; after the launch, one log step a poll."""
        CALLS.append(("state", role, project))
        call(f"-project action=status name={project}", role)
        if up["started"] and logs_start:
            up["polls"] += 1
            write(top, [f"07:00:00.000 Starting project '{P}'",
                        "07:00:00.500 ProgressEngine - OOS : 40 %"] if up["polls"] == 1 else
                       ["07:05:00.000 ProgressEngine - OOS : Task finished",
                        "07:05:01.000 ProgressEngine - Project finished"])
        return {"status": None}

    def cut(project: str, databank: str, verdict_csv: Path, role: str,
            into: str | None = None) -> dict:
        """apply_verdict.apply: record it and delete the named files from the scratch bank."""
        CALLS.append(("apply_verdict", project, databank, Path(verdict_csv), role, into))
        names = pd.read_csv(verdict_csv).strategy
        for n in names:
            (source / f"{n}.sqx").unlink()
        return {"install": "SQX_w1", "before": 3, "after": 3 - len(names),
                "removed": len(names), "out": source}

    def start(role: str = "conductor") -> None:
        """core.worker.start: the worker comes up — or dies half-way through its launch."""
        CALLS.append(("start", role))
        up["on"] = True
        if start_fails:
            raise RuntimeError("sqx-worker.sh start: worker failed to start")

    worker.call, worker.start = call, start
    worker.stop = lambda role="conductor": (CALLS.append(("stop", role)), up.update(on=False))
    worker.holding = lambda top_: [4242] if up["on"] else []
    progress.state = state
    apply_verdict.apply = cut
    stage.apply = lambda cfx_, steps, skip=(): CALLS.append(("stage", cfx_.parent.name, steps,
                                                             list(skip)))
    record.log = lambda study, row, scores=None: CALLS.append(("ledger", study, row))
    ledgerrow.placed = lambda project, databank: (8, "build")
    run.POLL, run.START_WITHIN = 0, within
    return up


def test_master_refused_first(root: Path) -> None:
    """A project the registry puts on the master is refused before anything else is checked."""
    tree(root, install="SQX")
    got = preflight.check(P, "Results")
    assert not got["ok"] and len(got["reasons"]) == 1 and "maestro" in got["reasons"][0], got


def test_busy_port_refused(root: Path) -> None:
    """A worker whose port answers is refused as busy, and never stopped."""
    built = tree(root)
    fakes(built)
    with socket.socket() as s:
        s.bind(("127.0.0.1", built["port"]))
        s.listen()
        got = preflight.check(P, "Results")
    assert not got["ok"] and any("install ocupado" in r for r in got["reasons"]), got
    assert not any(c[0] == "stop" for c in CALLS), CALLS


def test_recent_project_refused(root: Path) -> None:
    """Another project of that worker touched within 24 h is a refusal."""
    tree(root)
    age(preflight.WORKERS["conductor"]["path"] / "user/projects" / OTHER, time.time() - 3600)
    got = preflight.check(P, "Results")
    assert not got["ok"] and any(OTHER in r for r in got["reasons"]), got


def test_happy_path(root: Path) -> None:
    """Copy, verdict, curate, stage, start, launch, only status until finished, stop — and the
    finished run already in today's log is not taken for this one's end."""
    built = tree(root)
    up = fakes(built)
    app = FastAPI()
    app.include_router(api.ROUTER)
    got = TestClient(app).get("/api/advance/preflight",
                              params={"project": P, "databank": "Results"}).json()
    assert got["ok"], got
    assert got["text"] == (f"Se van a borrar 2 estrategias de Results en {P} sobre SQX_w1, y "
                           "después se lanzará OOS"), got["text"]
    run.advance(P, "Results")
    assert up["polls"] == 2, "finished only once the new «Project finished» was written"
    kinds = [c[0] for c in CALLS if c[0] != "state"]
    order = ["apply_verdict", "ledger", "stage", "start", "stop"]
    assert [k for k in kinds if k in order] == order, kinds
    cut = next(c for c in CALLS if c[0] == "apply_verdict")
    assert cut[1:3] == (P, "Results") and cut[4] == "conductor" and cut[5] is None, cut
    assert next(c for c in CALLS if c[0] == "stage")[1:] == (P, ["oos"], []), CALLS
    sent = [c[1] for c in CALLS if c[0] == "call"]
    launch = sent.index(f"-project action=start name={P}")
    assert all("action=status" in c for i, c in enumerate(sent) if i != launch), sent
    first = CALLS.index(next(c for c in CALLS if c[0] == "start"))
    between = CALLS[first + 1:CALLS.index(("stop", "conductor"))]
    assert [c for c in between if c[0] not in ("call", "state")] == [], between
    backup = next(preflight.DISCARDS.glob(f"{P}/Results/*"))
    verdict = pd.read_csv(backup / "verdict.csv")
    assert set(verdict.columns) >= {"strategy", "verdict", "identity"}, verdict.columns
    assert dict(zip(verdict.identity, verdict.strategy)) == built["dropped"], verdict
    assert set(verdict.verdict) == {"DESCARTAR"}
    assert sorted(f.stem for f in backup.glob("*.sqx")) == sorted(built["dropped"].values())
    assert discards.live(P, "Results") == [], "the cut must consume the discards"
    last = discards.events(P, "Results")[-1]
    assert last["cut"] and last["clear"] and (last["removed"], last["task"]) == (2, "OOS"), last
    row = next(c for c in CALLS if c[0] == "ledger")
    assert row[1] == "USDJPY_M30_fam" and (row[2]["n_in"], row[2]["n_out"]) == (3, 1), row


if __name__ == "__main__":
    for test in (test_master_refused_first, test_busy_port_refused, test_recent_project_refused,
                 test_happy_path):
        with tempfile.TemporaryDirectory() as scratch:
            began = time.time()
            test(Path(scratch))
        print(f"ok  {test.__name__}  {time.time() - began:.1f} s")
