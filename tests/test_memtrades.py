#!/usr/bin/env python3
"""A memory export is taken only when it is this databank's, whole and newer than its files.

`memtrades.take` hands the AlgoTrades snippet's CSVs to `export_trades` in place of orderstocsv.
Anything short of that — no `_done.tsv`, other strategies, files saved after it — must fall back,
because a stale folder would be packed as today's trades without a word. And `install.pending`
must name a snippet whose class is missing or older than its source: SQX keeps the old class
when a compile fails.
"""

import os
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.export import memtrades  # noqa: E402
from sqx.snippets import install  # noqa: E402


def _export(root: Path, names: list[str], done: bool = True) -> Path:
    """A snippet's output folder for `names`."""
    out = root / "_trades_mem"
    out.mkdir()
    for n in names:
        (out / f"{n}.csv").write_text("x\r\n")
    if done:
        (out / "_done.tsv").write_text("".join(f"{n}\t1\n" for n in names))
    return out


def test_take(tmp_path: Path) -> None:
    """Only a finished export of exactly these strategies, newer than their files, is taken."""
    memtrades.folder = lambda project, databank: tmp_path / "_trades_mem"
    names = {"Strategy 1", "Strategy 2(1)"}
    cases = {"fresh": (sorted(names), True, -10, True),
             "unfinished": (sorted(names), False, -10, False),
             "other strategies": (["Strategy 1"], True, -10, False),
             "files saved after it": (sorted(names), True, +10, False)}
    for case, (wrote, done, age, want) in cases.items():
        out = _export(tmp_path, wrote, done)
        newest = (out / "_done.tsv").stat().st_mtime + age if done else 0.0
        into = tmp_path / f"csv {case}"
        assert memtrades.take("P", "Results", names, newest, into) is want, case
        assert not out.exists(), case                     # consumed either way
        assert into.exists() is want, case
        if want:
            assert sorted(p.name for p in into.iterdir()) == ["Strategy 1.csv", "Strategy 2(1).csv"]


def test_pending(tmp_path: Path) -> None:
    """A snippet is pending until its class is in a jar newer than its installed source."""
    top = tmp_path / "SQX"
    jar = top / "internal/libs/Snippets.jar"
    jar.parent.mkdir(parents=True)
    install.worker_dir = lambda role: top
    sources = sorted(p.relative_to(install.SOURCES).as_posix() for p in install.SOURCES.rglob("*.*")
                     if p.relative_to(install.SOURCES).parts[0] in ("Snippets", "Code"))
    java = [s for s in sources if s.endswith(".java")]
    assert java and len(sources) > len(java)

    zipfile.ZipFile(jar, "w").close()
    assert install.pending("x") == sources                # nothing copied

    for s in sources:
        (top / "user/extend" / s).parent.mkdir(parents=True, exist_ok=True)
        (top / "user/extend" / s).write_bytes((install.SOURCES / s).read_bytes())
    assert install.pending("x") == java                   # copied, no class in the jar

    with zipfile.ZipFile(jar, "w") as z:
        for s in java:
            z.writestr(s.removeprefix("Snippets/").removesuffix(".java") + ".class", b"")
    assert install.pending("x") == []                     # compiled after the copy

    old = jar.stat().st_mtime - 60
    os.utime(jar, (old, old))
    assert install.pending("x") == java                   # the jar predates the source: a failed compile
