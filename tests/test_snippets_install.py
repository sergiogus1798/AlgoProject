#!/usr/bin/env python3
"""`install.pending` names a snippet whose class is missing or older than its source: SQX keeps the old class when a compile fails."""

import os
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.snippets import install  # noqa: E402


def test_pending(tmp_path: Path) -> None:
    """A snippet is pending until its class is in a jar newer than its installed source."""
    top = tmp_path / "SQX"
    jar = top / "internal/libs/Snippets.jar"
    jar.parent.mkdir(parents=True)
    install.worker_dir = lambda role: top
    sources = sorted(
        p.relative_to(install.SOURCES).as_posix()
        for p in install.SOURCES.rglob("*.*")
        if p.relative_to(install.SOURCES).parts[0] in ("Snippets", "Code")
    )
    java = [s for s in sources if s.endswith(".java")]
    assert java and len(sources) > len(java)

    zipfile.ZipFile(jar, "w").close()
    assert install.pending("x") == sources  # nothing copied

    for s in sources:
        (top / "user/extend" / s).parent.mkdir(parents=True, exist_ok=True)
        (top / "user/extend" / s).write_bytes((install.SOURCES / s).read_bytes())
    assert install.pending("x") == java  # copied, no class in the jar

    with zipfile.ZipFile(jar, "w") as z:
        for s in java:
            z.writestr(
                s.removeprefix("Snippets/").removesuffix(".java") + ".class", b""
            )
    assert install.pending("x") == []  # compiled after the copy

    old = jar.stat().st_mtime - 60
    os.utime(jar, (old, old))
    assert install.pending("x") == java  # the jar predates the source: a failed compile

    os.utime(jar)
    foreign = (
        top / "user/extend/Snippets/SQ/Blocks/Owner.java"
    )  # not ours: never listed, never deleted
    gone = top / "user/extend" / install.DROPPED[0]
    for f in (foreign, gone):
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("x")
    assert install.pending("x") == list(install.DROPPED)  # only what this repo dropped
