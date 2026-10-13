"""Encargo 66 §4.3 bis g: the store's slow paths give today's answers (oracles = the old code, kept here)."""

import json
import os
import shutil
import time
from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from core import paths
from core.archive import collect, harvest, read
from core.store import write


def _old_harvest_rows(folder: Path, identity: str, out: Path) -> dict:
    """The pre-change per-survivor harvest, kept as the oracle."""
    out.mkdir()
    counts = {}
    for name in ("metrics", "equity", "trades"):
        if not (folder / f"{name}.parquet").exists():
            continue
        rows = pd.read_parquet(folder / f"{name}.parquet", filters=[("identity", "==", identity)])
        rows.to_parquet(out / f"{name}.parquet")
        counts[name] = len(rows)
    return counts


def _old_folder(identity: str, cell: str = "", name: str = "") -> Path | None:
    """The pre-change glob lookup of a strategy's folder."""
    return next(iter(write.store_dir().glob(f"*/* {identity[:8]}")),
                write.store_dir() / (cell or "_") / f"{name or '_'} {identity[:8]}")


def _old_listing(root: Path) -> list:
    """The pre-change store listing."""
    out = []
    for identity in sorted(p.name for p in root.iterdir() if p.is_dir()):
        for version in read.versions(identity):
            doc = json.loads((root / identity / version / "manifest.json").read_text(encoding="utf-8"))
            view = json.loads((root / identity / version / "view.json").read_text(encoding="utf-8"))
            tear = view["tearsheet"]
            out.append({"identity": identity, "version": version,
                        "strategy": tear["strategy"] if isinstance(tear, dict) else None,
                        **{k: doc[k] for k in ("project", "databank", "step", "archived_at", "note")}})
    return out


def test_harvest_rows_same_files(tmp_path: Path) -> None:
    """The new harvest writes the same files as the old."""
    ids = ["a" * 64, "b" * 64, "c" * 64]
    day = tmp_path / "h"
    day.mkdir()
    # identities interleaved, one absent from equity, a NaN identity row, no trades.parquet
    met = pd.DataFrame({"x": [1.0, 2, 3, 4, 5]}, index=pd.Index([ids[1], ids[0], ids[1], None, ids[0]], name="identity"))
    eq = pd.DataFrame({"identity": [ids[0], ids[1]] * 5, "equity": range(10),
                       "day": pd.date_range("2020", periods=10), "sample": list("ababababab")})
    met.to_parquet(day / "metrics.parquet")
    eq.to_parquet(day / "equity.parquet")
    for i, ident in enumerate(ids + ["d" * 64]):
        new, old = tmp_path / f"n{i}", tmp_path / f"o{i}"
        assert harvest.harvest_rows(day, ident, new) == _old_harvest_rows(day, ident, old)
        for f in old.iterdir():
            assert_frame_equal(pd.read_parquet(new / f.name), pd.read_parquet(f))
    # a rewritten file is seen
    pd.DataFrame({"x": [9.0]}, index=pd.Index([ids[0]], name="identity")).to_parquet(day / "metrics.parquet")
    os.utime(day / "metrics.parquet", ns=(1, 2))
    assert harvest.harvest_rows(day, ids[0], tmp_path / "n9") == {"metrics": 1, "equity": 5}


def _reports(tmp_path: Path) -> str:
    """A small reports tree to freeze."""
    ident = "e" * 64
    f = tmp_path / "reports" / "P" / "Results" / "2026-01-01" / "study"
    (f / "estrategias").mkdir(parents=True)
    (f / "verdict.csv").write_text(f"strategy,identity,v\nS1,{ident},ok\nS2,{'f' * 64},no\n")
    (f / "estrategias" / "S1.json").write_text(json.dumps({"strategy": "S1", "config_hash": "h"}))
    return ident


def test_freeze_cache_changes_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Serving freeze from the cache gives what parsing every time gives."""
    ident = _reports(tmp_path)
    monkeypatch.setattr(collect, "DATA", tmp_path)
    collect._READ.clear()
    first = collect.freeze("P", ident, tmp_path / "o1")
    second = collect.freeze("P", ident, tmp_path / "o2")            # served from the cache
    monkeypatch.setattr(collect, "_cached", lambda path, kind, load: load(path))
    plain = collect.freeze("P", ident, tmp_path / "o3")             # the old behaviour: parse every time
    assert first == second == plain and first[0][0]["named"] == "S1"
    assert sorted(p.name for p in (tmp_path / "o2").rglob("*") if p.is_file()) == \
        sorted(p.name for p in (tmp_path / "o3").rglob("*") if p.is_file())
    monkeypatch.undo()


def test_folder_matches_glob(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The folder lookup finds what the old glob finds."""
    monkeypatch.setattr(write, "store_dir", lambda: tmp_path)
    write._SEEN.clear()
    (tmp_path / ".pool").mkdir()
    (tmp_path / "c1").mkdir()
    (tmp_path / "c1" / "Strategy 1.2.3 12345678").mkdir()
    ids = ["12345678" + "0" * 56, "87654321" + "0" * 56, "00000000" + "1" * 56]
    for ident in ids:
        assert write.folder(ident, "cX", "nm") == _old_folder(ident, "cX", "nm")
    (tmp_path / "c2").mkdir()                                       # a new folder appears: seen at once
    (tmp_path / "c2" / "other 87654321").mkdir()
    for ident in ids:
        assert write.folder(ident, "cX", "nm") == _old_folder(ident, "cX", "nm")
    shutil.rmtree(tmp_path / "c1" / "Strategy 1.2.3 12345678")
    assert write.folder(ids[0], "cX", "nm") == _old_folder(ids[0], "cX", "nm")


def test_listing_same_rows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The listing returns the old rows."""
    monkeypatch.setattr(read, "archive_dir", lambda: tmp_path)
    man = {k: "v" for k in ("project", "databank", "step", "archived_at", "note")}
    shapes = {"a": {"results": {"x": {"tearsheet": 1}}, "tearsheet": {"strategy": "S 1", "day": "d"}, "gate": None},
              "b": {"results": {}, "tearsheet": "no hay cosecha", "gate": None},
              "c": {"results": {"k": [1]}, "tearsheet": {"strategy": "S \"2\"\n"}, "gate": {"tearsheet": 3}}}
    for ident, view in shapes.items():
        d = tmp_path / (ident * 64) / "2026-01-01T0000"
        d.mkdir(parents=True)
        (d / "manifest.json").write_text(json.dumps(man))
        (d / "view.json").write_text(json.dumps(view, indent=1, default=str))
    assert read.listing() == _old_listing(tmp_path)
    assert [r["strategy"] for r in read.listing()] == ["S 1", None, 'S "2"\n']


@pytest.mark.skipif(not paths.store_dir().is_dir(), reason="no real store")
def test_real_store_timing() -> None:
    """Read-only on the real data root; prints what it measures (run with -s)."""
    t = time.time()
    n = len({k for k in [write.folder(p.name.rsplit(" ", 1)[1].ljust(64, "0")) for c in paths.store_dir().iterdir()
                         if c.is_dir() and not c.name.startswith(".") for p in c.iterdir()
                         if " " in p.name and not p.name.startswith(".")]})
    new = time.time() - t
    t = time.time()
    for c in paths.store_dir().iterdir():
        if c.is_dir() and not c.name.startswith("."):
            for p in c.iterdir():
                if " " in p.name and not p.name.startswith("."):
                    _old_folder(p.name.rsplit(" ", 1)[1].ljust(64, "0"))
    old = time.time() - t
    print(f"\nfolder() x{n}: new {new:.2f}s, old glob {old:.2f}s")
    if paths.archive_dir().is_dir():
        t = time.time()
        rows = read.listing()
        new = time.time() - t
        t = time.time()
        assert _old_listing(paths.archive_dir()) == rows
        print(f"listing() x{len(rows)}: new {new:.2f}s, old {time.time() - t:.2f}s")


def test_a_folder_made_by_another_process_in_the_listing_tick_is_seen_later(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Listing at M+0.5 s, a foreign folder in the same mtime tick, the next call 5 s later: relisted."""
    monkeypatch.setattr(write, "store_dir", lambda: tmp_path)
    write._SEEN.clear()
    m = 1_700_000_000 * 10**9
    clock = [m + 5 * 10**8]
    monkeypatch.setattr(write.time, "time_ns", lambda: clock[0])
    (tmp_path / "c1" / "A 11111111").mkdir(parents=True)
    for d in (tmp_path / "c1", tmp_path):
        os.utime(d, ns=(m, m))
    write.folder("11111111")                      # lists at M + 0.5 s
    (tmp_path / "c1" / "B 22222222").mkdir()      # another process, same tick: the mtime is put back
    for d in (tmp_path / "c1", tmp_path):
        os.utime(d, ns=(m, m))
    clock[0] = m + 5 * 10**9
    assert write.folder("22222222", "cX", "B") == tmp_path / "c1" / "B 22222222"
