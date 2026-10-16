#!/usr/bin/env python3
"""`core.store.rekey` (encargo 76 D): a folder moves to its new identity; two that become one stop it."""

import json
import shutil
from pathlib import Path

import pytest

from core import sqxfile
from core.store import rekey
from core.store.write import MANIFEST, SQX

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "identity"


def _stored(root: Path, name: str, sqx: Path) -> Path:
    """One store folder holding `sqx` under a stale identity."""
    here = root / "cell" / f"{name} deadbeef"
    here.mkdir(parents=True)
    shutil.copy(sqx, here / SQX)
    (here / MANIFEST).write_text(json.dumps({"identity": "deadbeef" * 8}))
    return here


def test_a_folder_moves_to_its_new_identity(tmp_path: Path) -> None:
    """The folder takes the new 8 letters, its manifest the new identity, the old one is backed up."""
    sqx = FIXTURES / "retest_oos.build.sqx"
    _stored(tmp_path / "store", "S1", sqx)
    rows = rekey.plan(tmp_path / "store")
    out = tmp_path / "map.csv"
    rekey.apply(rows, tmp_path / "backup", out)
    new = sqxfile.identity(sqx)
    there = tmp_path / "store" / "cell" / f"S1 {new[:8]}"
    assert json.loads((there / MANIFEST).read_text())["identity"] == new
    assert (tmp_path / "backup" / "cell" / "S1 deadbeef" / MANIFEST).exists()
    rekey.apply(rekey.plan(tmp_path / "store"), tmp_path / "backup", out)
    assert out.read_text().splitlines()[1:] == [
        f"cell,S1 deadbeef,{'deadbeef' * 8},{new}"
    ]


def test_a_new_name_already_on_disk_stops_it(tmp_path: Path) -> None:
    """A folder never lands on one that is already there."""
    sqx = FIXTURES / "retest_oos.build.sqx"
    _stored(tmp_path / "store", "S1", sqx)
    (tmp_path / "store" / "cell" / f"S1 {sqxfile.identity(sqx)[:8]}").mkdir()
    with pytest.raises(SystemExit, match="ya existe"):
        rekey.plan(tmp_path / "store")


def test_two_folders_that_become_one_stop_it(tmp_path: Path) -> None:
    """The same strategy stored twice is the owner's call: nothing is rewritten."""
    _stored(tmp_path / "store", "S1", FIXTURES / "retest_oos.build.sqx")
    _stored(tmp_path / "store", "S2", FIXTURES / "retest_oos.after.sqx")
    with pytest.raises(SystemExit, match="NO SE REESCRIBE"):
        rekey.plan(tmp_path / "store")


def test_the_loose_tables_follow_every_map(tmp_path: Path) -> None:
    """A chain of maps lands on the last identity; only identity columns move."""
    (tmp_path / "identity-map-2026-10.csv").write_text("cell,folder,old,new\nc,f,a,b\n")
    (tmp_path / "identity-map-2026-11.csv").write_text("cell,folder,old,new\nc,f,b,c\n")
    m = rekey.mapping(tmp_path)
    assert m == {"a": "c", "b": "c"}
    rows, n = rekey.retabled([["strategy", "identity", "mother"], ["a", "a", "b"]], m)
    assert (rows[1], n) == (["a", "c", "c"], 2)
