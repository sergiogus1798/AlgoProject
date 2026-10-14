"""Encargo 66, `live.sync` and `live.cut` over real HTTP against a fake SQX servlet on a free port."""

import json
import threading
import urllib.parse
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from sqx.projects import live
from tests.test_perf66_sqxprojects import SAVED


class FakeSqx:
    """SQX's /project servlet on a free localhost port: `mem` is memory (databank -> names), the files are disk.

    `synchronizeDatabank` mirrors memory onto disk and logs the «saved» line; `removeReports` drops the
    names it holds, except those in `keep` (SQX leaving one behind)."""

    def __init__(self, top: Path, project: str, mem: dict[str, list[str]]) -> None:
        """Lay out the fake install under `top`, serve it on a free port and write that port to its settings."""
        self.top, self.project, self.mem, self.keep, self.calls = top, project, mem, set(), []
        (top / "user/settings").mkdir(parents=True)
        (top / "user/log/StrategyQuant").mkdir(parents=True)
        self.log = top / "user/log/StrategyQuant/log_2026_01_01.log"
        self.log.write_text("")
        for bank, _names in mem.items():
            self.write(bank)
        fake = self

        class H(BaseHTTPRequestHandler):
            """Hands every POST to `FakeSqx.answer` and replies with its JSON."""

            def do_POST(self) -> None:
                """Record the call, answer it, send the JSON back."""
                action = self.path.rsplit("/", 1)[1]
                q = {k: v[0] for k, v in urllib.parse.parse_qs(
                    self.rfile.read(int(self.headers["Content-Length"])).decode()).items()}
                fake.calls.append((action, q))
                out = fake.answer(action, q)
                body = json.dumps(out).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a: object) -> None:
                """Keep the test output quiet."""
                pass

        self.server = HTTPServer(("127.0.0.1", 0), H)       # port 0: a free one, never SQX's
        port = self.server.server_address[1]
        (top / "user/settings/settings.xml").write_text(
            f"<s><WebServerPortUsed>{port}</WebServerPortUsed><BrowserToken>t</BrowserToken></s>")
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def write(self, bank: str) -> None:
        """Disk = memory for one databank."""
        folder = self.top / "user/projects" / self.project / "databanks" / bank
        folder.mkdir(parents=True, exist_ok=True)
        for f in folder.glob("*.sqx"):
            f.unlink()
        for n in self.mem[bank]:
            (folder / f"{n}.sqx").write_text(n)

    def answer(self, action: str, q: dict) -> dict:
        """The reply of one servlet action against the fake memory and disk."""
        if action == "databankList":
            return {"databanks": [{"name": b, "records": len(n), "syncType": "Auto-sync every 1 hour"}
                                  for b, n in self.mem.items()]}
        if action == "synchronizeDatabank":
            self.write(q["databankName"])
            with self.log.open("a") as f:
                f.write(SAVED.format(q["databankName"], "API request"))
            return {}
        if action == "removeReports":
            gone = set(q["strategies"].split(",")) - self.keep
            self.mem[q["databankName"]] = [n for n in self.mem[q["databankName"]] if n not in gone]
            return {"records": len(self.mem[q["databankName"]])}
        return {"error": f"unknown {action}"}


@pytest.fixture
def sqx(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[FakeSqx]:
    """A FakeSqx of project Test_X (databank B holding a, b, c) standing in for the custodian."""
    fake = FakeSqx(tmp_path, "Test_X", {"B": ["a", "b", "c"]})
    monkeypatch.setattr(live.loadwait, "booted", lambda role, launch, *a: launch())      # the stubbed script writes no log; test_perf66_waits covers the wait
    monkeypatch.setitem(live.WORKERS, "custodian", {"path": tmp_path, "port": 0})
    yield fake
    fake.server.shutdown()


def test_real_sync_of_a_databank_rewritten_at_the_same_count(sqx: FakeSqx) -> None:
    """Over HTTP: equal counts send nothing; `force` sends the sync and ends on SQX's «saved» line."""
    assert live.sync("custodian", "Test_X") == {"B": 3}
    assert [c for c, _ in sqx.calls if c == "synchronizeDatabank"] == []
    assert live.sync("custodian", "Test_X", force={"B"}) == {"B": 3}
    assert [q["databankName"] for c, q in sqx.calls if c == "synchronizeDatabank"] == ["B"]


def test_real_cut_drops_names_and_fails_when_one_stays(sqx: FakeSqx) -> None:
    """Over HTTP: a cut mirrors disk; a name SQX leaves behind (and a duplicate counted once) is judged by counts."""
    assert live.cut("custodian", "Test_X", "B", ["a", "a"]) == 1
    assert sorted(p.stem for p in (sqx.top / "user/projects/Test_X/databanks/B").glob("*.sqx")) == ["b", "c"]
    sqx.keep = {"c"}
    with pytest.raises(SystemExit, match="se pidió quitar 2 y salieron 1"):
        live.cut("custodian", "Test_X", "B", ["b", "c"])
