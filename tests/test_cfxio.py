#!/usr/bin/env python3
"""cfxio: the guard of hard rule 4 and the atomic rewrite; the registry's lock. No real port is touched."""

import sys
import tempfile
import threading
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.projects import cfxio, registry

MEMBERS = {"config.xml": b"<Project/>", "b.xml": b"\x00\x01" * 500, "a.xml": b"zz"}


def _read(cfx: Path) -> dict:
    """Members of a zip, by name, in order."""
    with zipfile.ZipFile(cfx) as z:
        return {n: z.read(n) for n in z.namelist()}


def _fake_install(root: Path) -> tuple:
    """Patch the installs to one fake custodian under `root`, with its port answering."""
    return (
        mock.patch.object(
            cfxio, "_installs", lambda: {"custodian": (root.resolve(), 5070)}
        ),
        mock.patch.object(cfxio, "listening", lambda port: True),
        mock.patch.object(cfxio, "holding", lambda install: []),
    )


def test_round_trip_and_crash() -> None:
    """Content and order survive; a crash mid-write leaves the original and no .tmp."""
    with tempfile.TemporaryDirectory() as d:
        cfx = Path(d) / "p" / "project.cfx"
        cfx.parent.mkdir()
        with mock.patch.object(cfxio, "_installs", lambda: {}):
            cfxio.write(cfx, MEMBERS)
            got = _read(cfx)
            assert got == MEMBERS and list(got) == list(MEMBERS)
            assert not cfx.with_suffix(".cfx.tmp").exists()
            before = cfx.read_bytes()
            bad = {"x.xml": b"1", "y.xml": object()}  # writestr raises on the second
            try:
                cfxio.write(cfx, bad)
            except TypeError:
                pass
            else:
                raise AssertionError("the crash did not happen")
            assert cfx.read_bytes() == before
            assert not cfx.with_suffix(".cfx.tmp").exists()


def test_held() -> None:
    """Role under a fake install, through a symlink and a booting JVM; None outside."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        cfx = root / "inst" / "user" / "projects" / "P" / "project.cfx"
        cfx.parent.mkdir(parents=True)
        cfx.write_bytes(b"x")
        link = root / "link.cfx"
        link.symlink_to(cfx)
        outside = root / "elsewhere.cfx"
        a, b, c = _fake_install(root / "inst")
        with a, b, c:
            assert cfxio.held(cfx) == "custodian"
            assert cfxio.held(link) == "custodian"  # a symlink to a held file is held
            assert cfxio.held(outside) is None  # outside every install: never held
            try:
                cfxio.write(link, MEMBERS)
            except SystemExit:
                pass
            else:
                raise AssertionError("write went through a held file")
            assert cfx.read_bytes() == b"x"
            cfxio.write(cfx, MEMBERS, force=True)
        with (
            a,
            mock.patch.object(cfxio, "listening", lambda port: False),
            mock.patch.object(cfxio, "holding", lambda install: [4242]),
        ):
            assert cfxio.held(cfx) == "custodian"  # JVM booting: no port yet, a process
        with a, mock.patch.object(cfxio, "listening", lambda port: False), c:
            assert cfxio.held(cfx) is None  # down and no process


def test_registry_interleaved_writers_lose_no_row() -> None:
    """Three threads recording 25 rows each: all 75 are there."""
    with tempfile.TemporaryDirectory() as d:
        csv_path = Path(d) / "registry.csv"
        done = lambda n: {
            "project": n,
            "install": "SQX_w2",
            "timeframe": "H1",
            "acceptance": {"mode": "m", "sample": "s", "conditions": []},
        }

        def work(tag: str) -> None:
            """Record 25 projects."""
            for i in range(25):
                registry.record(done(f"Test_{tag}{i}"), "p", "XAUUSD", "t")

        with mock.patch.object(registry, "project_registry", lambda: csv_path):
            ts = [threading.Thread(target=work, args=(t,)) for t in "ABC"]
            [t.start() for t in ts]
            [t.join() for t in ts]
            names = {r["name"] for r in registry.rows()}
            assert len(names) == 75, len(names)
            assert not csv_path.with_name("registry.csv.tmp").exists()


if __name__ == "__main__":
    for t in (
        test_round_trip_and_crash,
        test_held,
        test_registry_interleaved_writers_lose_no_row,
    ):
        t()
    print("test_cfxio: ok")
