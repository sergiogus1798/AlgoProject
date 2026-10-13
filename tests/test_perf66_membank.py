#!/usr/bin/env python3
"""`membank.take` hands an `.abk` over only when it is this databank's, whole and newer than its files.

Ports every case of `test_memtrades.py` (finished, same strategies, newer than the files) and adds the
data mode, the identities, a corrupt file, and `run` replacing only the banks it names. The `.abk`
files come from the struct writer of `test_perf66_algobank.py` (imported, not copied).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import sqxfile  # noqa: E402
from sqx.export import membank  # noqa: E402
from tests.test_perf66_algobank import strategies, write  # noqa: E402

WRITTEN = 1_760_000_000.0          # the writer's fixed written_ms, in seconds


@pytest.fixture
def folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The bank folder redirected under tmp_path."""
    monkeypatch.setattr(membank, "bank_dir", lambda project, role: tmp_path)
    return tmp_path


def _ids(bank: list[dict]) -> dict[str, str]:
    """File stem -> identity of each strategy, as the harvest computes it."""
    return {s["name"]: sqxfile._hashed(s["xml"]) for s in bank}


def test_take(folder: Path, capsys: pytest.CaptureFixture) -> None:
    """Fresh dump is taken; every way of not being this databank's gives None and one line."""
    bank = strategies()
    write(folder / "R.abk", bank)
    ids = _ids(bank)
    ok = membank.take("P", "x", "R", ids, WRITTEN - 10, "main")
    assert ok is not None and sorted(ok["names"]) == sorted(ids)
    assert capsys.readouterr().out == ""
    bad = {"wrong data mode": (ids, WRITTEN - 10, "all"),
           "name missing in the file": ({**ids, "Strategy 9": "z"}, WRITTEN - 10, "main"),
           "name extra in the file": ({k: v for k, v in ids.items() if k != "Strategy 3.3.3"}, WRITTEN - 10, "main"),
           "one identity differs": ({**ids, "Strategy 2.1.1": "0"}, WRITTEN - 10, "main"),
           "older than the files": (ids, WRITTEN + 10, "main")}
    for case, (i, newest, data) in bad.items():
        assert membank.take("P", "x", "R", i, newest, data) is None, case
        assert len(capsys.readouterr().out.splitlines()) == 1, case


def test_take_refuses_missing_and_corrupt(folder: Path) -> None:
    """No file, a truncated file and a flipped byte are all None."""
    assert membank.take("P", "x", "R", {}, 0.0, "main") is None
    write(folder / "R.abk", strategies())
    raw = bytearray((folder / "R.abk").read_bytes())
    raw[40] ^= 1
    (folder / "R.abk").write_bytes(raw)
    assert membank.take("P", "x", "R", _ids(strategies()), 0.0, "main") is None
    (folder / "R.abk").write_bytes(bytes(raw[:50]))
    assert membank.take("P", "x", "R", _ids(strategies()), 0.0, "main") is None


def test_run_keeps_the_first_modes_files(folder: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Two data modes mean two task runs; the second must not wipe what the first wrote."""
    modes = []
    monkeypatch.setattr(membank.toolproject, "cfx", lambda role: folder)
    monkeypatch.setattr(membank.install, "pending", lambda role: [])
    monkeypatch.setattr(membank.live, "call", lambda role, action, **kw: modes.append(kw["xmlConfig"]))

    def fake_run(role: str, project: str, config: str) -> str:
        """The snippet: writes the banks of the last call's mode, then _done.tsv."""
        banks = modes[-1].split("|")[1].split(";") if "|" in modes[-1] else []
        for b in banks:
            write(folder / f"{b}.abk", strategies()[:2])
        (folder / "_done.tsv").write_text("done\n")
        return "end"

    monkeypatch.setattr(membank.live, "run", fake_run)
    monkeypatch.setattr(membank.live, "records", lambda role, project: {"A": 2, "B": 2})
    monkeypatch.setattr(membank.toolproject, "settings", lambda snippet, args: args)
    (folder / "Other.abk").write_bytes(b"keep")
    assert membank.run("x", "P", {"A": "main", "B": "all"}) == {"A": 2, "B": 2}
    assert len(modes) == 2 and (folder / "A.abk").exists() and (folder / "Other.abk").read_bytes() == b"keep"
