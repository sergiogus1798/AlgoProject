"""The daemon's gate and the launchers' proof of confirmation, on a local app: never the real daemon, never SQX."""

import os
import stat
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from core import uitoken as session  # noqa: E402
from ui.daemon import gate, proof  # noqa: E402
from ui.daemon.advance import api as advance  # noqa: E402
from ui.daemon.launch import api as launch  # noqa: E402
from ui.daemon.mt5bridge import api as bridge  # noqa: E402
from ui.desktop import client  # noqa: E402

PORT = 8799                     # nothing listens there: TestClient speaks to the app in-process
HOST = f"127.0.0.1:{PORT}"
STARTED: list[tuple] = []
SAID = {"text": "Se va a lanzar «OOS» de Test_UiFake en SQX_w1"}
FORM = {"source": "archive", "identity": "abc", "start": "2024-01-01", "end": "2025-01-01",
        "model": "Every tick", "firms": ["FTMO"]}


def app() -> TestClient:
    """The three launchers, the cancel route, a health and a stand-in for close-terminal,
    behind the armed gate — the preflights faked ok with the sentence of `SAID`, the job
    start recorded instead of started."""
    with tempfile.TemporaryDirectory() as tmp:
        session.FOLDER = Path(tmp)
        token = session.mint(PORT)
        mode = stat.S_IMODE(os.stat(session.path(PORT)).st_mode)
        assert mode == 0o600 and session.read(PORT) == token and len(token) >= 40, (mode, token)
        gate.arm(PORT)
    STARTED.clear()
    proof.ISSUED.clear()
    jobs = SimpleNamespace(listing=lambda: [], JOBS=[], cancel=lambda i: STARTED.append(("cancel", i)),
                           start=lambda *a, **k: STARTED.append(a) or {"id": "j1", "log": "x"})
    launch.jobs = advance.jobs = bridge.jobs = jobs
    launch.check = lambda project, task="", step="": {
        "ok": True, "reasons": [], "role": "conductor", "titles": [task], "text": SAID["text"]}
    advance.check = lambda project, databank: {
        "ok": True, "reasons": [], "role": "conductor", "task": "OOS", "text": SAID["text"]}
    bridge.checked = lambda req: {"ok": True, "reasons": [], "file": "/x/a.sqx",
                                  "text": SAID["text"]}
    api = FastAPI()
    gate.install(api)
    for router in (launch.ROUTER, advance.ROUTER, bridge.ROUTER):
        api.include_router(router)
    api.get("/api/health")(lambda: {"ok": True})
    api.post("/api/jobs/{job_id}/cancel")(lambda job_id: {"ok": True, "cancelled": job_id})
    return TestClient(api, base_url=f"http://{HOST}")


def test_gate() -> None:
    """No token, a foreign Origin, a wrong Host: 403 each, on a write and on a read; health
    alone answers without a token, and never to another origin or host."""
    c, good = app(), {session.HEADER: gate.STATE["token"]}
    for path in ("/api/jobs/7/cancel", "/api/mt5bridge/close-terminal", "/api/launch/run"):
        assert c.post(path).status_code == 403, path
    assert c.post("/api/jobs/7/cancel", headers={session.HEADER: "nope"}).status_code == 403
    assert c.post("/api/jobs/7/cancel", headers=good).json() == {"ok": True, "cancelled": "7"}
    for origin in ("http://evil.example", "null", f"http://127.0.0.1:{PORT + 1}",
                   f"https://{HOST}"):
        got = c.post("/api/jobs/7/cancel", headers={**good, "Origin": origin})
        assert got.status_code == 403 and "origin" in got.json()["error"], origin
        assert c.get("/api/health", headers={"Origin": origin}).status_code == 403, origin
    assert c.post("/api/jobs/7/cancel", headers={**good, "Origin": f"http://{HOST}"}).is_success
    for host in ("evil.example", f"evil.example:{PORT}", "127.0.0.1", f"127.0.0.1:{PORT + 1}"):
        got = c.post("/api/jobs/7/cancel", headers={**good, "Host": host})
        assert got.status_code == 403 and "host" in got.json()["error"], host
        assert c.get("/api/health", headers={"Host": host}).status_code == 403, host
    assert c.post("/api/jobs/7/cancel", headers={**good, "Host": f"localhost:{PORT}"}).is_success
    assert c.get("/api/health").json() == {"ok": True}
    assert c.post("/api/health").status_code == 403         # open to GET only
    assert c.get("/api/launch/preflight", params={"project": "P", "task": "OOS"}).status_code == 403
    assert c.options("/api/launch/run", headers={"Origin": "http://evil.example"}).status_code == 403
    assert "access-control-allow-origin" not in c.get("/api/health").headers


def test_window_client_sends_token() -> None:
    """The window's one sender puts the token on GETs and POSTs, sends no Origin, and reads
    a token minted after it started (a daemon another window restarted)."""
    c = app()
    seen = []

    def relay(request: httpx.Request) -> httpx.Response:
        """Hand the window's request to the gated app as it was built."""
        seen.append(dict(request.headers))
        got = c.request(request.method, request.url.path, params=request.url.params,
                        content=request.content, headers=dict(request.headers))
        return httpx.Response(got.status_code, json=got.json())

    with tempfile.TemporaryDirectory() as tmp:
        session.FOLDER = Path(tmp)
        client.aim(PORT)
        client._HTTP = httpx.Client(base_url=client.BASE, transport=httpx.MockTransport(relay))
        try:
            client.get("launch/preflight", project="P", task="OOS")
            raise AssertionError("no token file yet: the gate must refuse")
        except httpx.HTTPStatusError as refused:
            assert refused.response.status_code == 403, refused
        session.path(PORT).write_text(gate.STATE["token"], encoding="utf-8")
        assert client.get("launch/preflight", project="P", task="OOS")["nonce"]
        assert client.post("jobs/7/cancel", {}) == {"ok": True, "cancelled": "7"}
    assert all("origin" not in h and h["host"] == HOST for h in seen), seen


def launcher(c: TestClient, kind: str) -> tuple:
    """(ask the preflight, send the run with a nonce, whether the answer queued a job)."""
    head = {session.HEADER: gate.STATE["token"]}
    if kind == "launch":
        body = {"project": "P", "task": "OOS"}
        return (lambda: c.get("/api/launch/preflight", params=body, headers=head).json(),
                lambda n: c.post("/api/launch/run", json={**body, "nonce": n}, headers=head).json(),
                lambda got: got.get("job") == "j1")
    if kind == "advance":
        body = {"project": "P", "databank": "Results"}
        return (lambda: c.get("/api/advance/preflight", params=body, headers=head).json(),
                lambda n: c.post("/api/advance/run", json={**body, "nonce": n}, headers=head).json(),
                lambda got: got.get("job") == "j1")
    return (lambda: c.post("/api/mt5bridge/preflight", json=FORM, headers=head).json(),
            lambda n: c.post("/api/mt5bridge/verify", json={**FORM, "nonce": n}, headers=head).json(),
            lambda got: got.get("id") == "j1")


def said(got: dict) -> str:
    """The refusal of a run, whichever way that launcher spells it."""
    return " ".join(got.get("reasons") or [got.get("error", "")])


def test_proof() -> None:
    """For each of the three launchers: no nonce, an invented one, a spent one, one whose plan
    moved and one too old start nothing; preflight → run with its nonce reaches `jobs.start`
    once."""
    for kind in ("launch", "advance", "mt5verify"):
        c = app()
        SAID["text"] = "Se va a lanzar «OOS» de Test_UiFake en SQX_w1"
        ask, run, queued = launcher(c, kind)
        assert "existe" in said(run("")) and "existe" in said(run("made-up")), kind
        assert STARTED == [], (kind, STARTED)

        nonce = ask()["nonce"]
        got = run(nonce)
        assert queued(got) and len(STARTED) == 1 and STARTED[0][0] == kind, (kind, got, STARTED)
        again = run(nonce)
        assert not queued(again) and "ya se usó" in said(again) and len(STARTED) == 1, (kind, again)

        nonce = ask()["nonce"]
        SAID["text"] = "Se van a borrar 9 estrategias, no 3"       # the state moved meanwhile
        moved = run(nonce)
        assert not queued(moved) and "cambió" in said(moved) and len(STARTED) == 1, (kind, moved)
        assert "existe" in said(run(nonce)), "a refused nonce is spent too"

        nonce = ask()["nonce"]
        plan, when = proof.ISSUED[nonce]
        proof.ISSUED[nonce] = (plan, when - proof.TTL_S - 1)
        old = run(nonce)
        assert not queued(old) and "caducó" in said(old) and len(STARTED) == 1, (kind, old)

        other = "advance" if kind == "launch" else "launch"         # a nonce of another launcher
        foreign = launcher(c, other)[0]()["nonce"]
        assert not queued(run(foreign)) and len(STARTED) == 1, kind


def test_refused_preflight_gives_no_nonce() -> None:
    """A preflight that refuses hands out nothing to run with."""
    c = app()
    launch.check = lambda project, task="", step="": {"ok": False, "reasons": ["no"], "text": ""}
    got = c.get("/api/launch/preflight", params={"project": "P", "task": "OOS"},
                headers={session.HEADER: gate.STATE["token"]}).json()
    assert "nonce" not in got and not proof.ISSUED, got


def test_real_app_is_gated() -> None:
    """`ui.daemon.app` carries the gate (and no CORS), so the real routes — close-terminal and
    cancel among them — are refused before they run."""
    from ui.daemon.app import APP
    kinds = [m.cls.__name__ for m in APP.user_middleware]
    assert kinds == ["BaseHTTPMiddleware"], kinds
    app()                                                   # arms the gate on PORT
    c = TestClient(APP, base_url=f"http://{HOST}")
    try:
        for path in ("/api/mt5bridge/close-terminal", "/api/jobs/nope/cancel"):
            assert c.post(path).status_code == 403, path
            assert c.post(path, headers={session.HEADER: gate.STATE["token"],
                                         "Origin": "http://evil.example"}).status_code == 403, path
        assert c.get("/api/health").json()["ok"]
        assert c.get("/api/jobs").status_code == 403
    finally:
        gate.STATE.update(port=None, token="")


if __name__ == "__main__":
    for test in (test_gate, test_window_client_sends_token, test_proof,
                 test_refused_preflight_gives_no_nonce, test_real_app_is_gated):
        test()
        print(f"ok  {test.__name__}")
    print("ui gate: all tests passed")
