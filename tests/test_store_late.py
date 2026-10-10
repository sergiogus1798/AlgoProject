"""Steps 13 to 20 in the store: who a renamed identity belongs to, and the audit that nothing is left out."""

import shutil
from pathlib import Path

import pandas as pd
import pytest

from core import sqxfile
from core.store import audit, extra, late, verify, write
from sqx.export import export_trades

SQX = Path(__file__).parent / "fixtures" / "strategy.sqx"
P, MOTHER, WFM, OTHER = "Test_x", "m" * 64, "w" * 64, "o" * 64


@pytest.fixture
def data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A data root with one WFM export and its report, the WFM having renamed the identity."""
    for mod in (late, extra, audit):
        monkeypatch.setattr(mod, "DATA", tmp_path, raising=False)
    monkeypatch.setattr(audit, "variants_dir", lambda p, n: tmp_path / "strategyPermutations" / p / n)
    monkeypatch.setattr(write, "store_dir", lambda: tmp_path / "store")
    monkeypatch.setattr(verify, "store_dir", lambda: tmp_path / "store")
    extra.table.cache_clear()
    raw = tmp_path / "raw" / P / "WFM" / "2026-10-08"
    (raw / "wfm").mkdir(parents=True)
    (raw / "identity.csv").write_text(f"strategy,identity\nS 1,{WFM}\nS 2,{OTHER}\n")
    pd.DataFrame({"strategy": ["S 1", "S 2"], "cell": [1, 2]}).to_parquet(raw / "wfm" / "cells.parquet")
    report = tmp_path / "reports" / P / "WFM" / "2026-10-08" / "wfm"
    (report / "estrategias").mkdir(parents=True)
    (report / "verdict.csv").write_text(f"strategy,identity,verdict\nS 1,{WFM},MANTENER\nS 2,{OTHER},MANTENER\n")
    (report / "estrategias" / "S 1.json").write_text("{}")
    (report / "wfm.json").write_text("{}")
    return tmp_path


def lineage(data: Path, mother: str) -> None:
    """Write a WFM lineage file whose one strategy has the given mother."""
    (data / "raw" / P / "WFM" / "2026-10-08" / "lineage.csv").write_text(
        f"strategy,identity,mother\nS 1,{WFM},{mother}\nS 2,{OTHER},{OTHER}\n")
    extra.table.cache_clear()


def test_a_name_pairs_nothing_until_the_export_says_whose_it_is(data: Path, tmp_path: Path) -> None:
    """No lineage, or a lineage that could not decide: the WFM's rows are nobody's."""
    assert late.names(P, "WFM", "2026-10-08", MOTHER) == set()
    assert late.exports(P, MOTHER, tmp_path / "a") == [] and late.mothers(P) == {}
    lineage(data, "")
    assert late.names(P, "WFM", "2026-10-08", MOTHER) == set() and late.mothers(P) == {}


def test_with_its_lineage_the_mother_gets_its_rows_and_only_its_rows(data: Path, tmp_path: Path) -> None:
    """With a lineage file the mother gets its rows and nobody else does."""
    lineage(data, MOTHER)
    assert late.mothers(P) == {WFM: MOTHER}
    assert late.names(P, "WFM", "2026-10-08", MOTHER) == {"S 1"}
    (_, out, about), = late.exports(P, MOTHER, tmp_path / "a")
    assert list(pd.read_parquet(out / "wfm" / "cells.parquet")["strategy"]) == ["S 1"]
    got = dict((stem, src) for stem, src, _ in late.unpaired(P, MOTHER, set(), set(), tmp_path / "b"))
    own = got["wfm.WFM.2026-10-08"]
    assert list(pd.read_csv(own / "verdict.csv")["strategy"]) == ["S 1"]
    assert (own / "estrategias" / "S 1.json").exists()
    assert (got["wfm.WFM.2026-10-08.poblacion"] / "wfm.json").exists()


def test_the_exporter_names_the_mother_only_when_one_other_identity_exists(tmp_path: Path) -> None:
    """One other file of that name in the project: the mother. Two different ones: nobody."""
    install, staged, out = tmp_path / "w", tmp_path / "staged", tmp_path / "out"
    banks = install / "user/projects" / P / "databanks"
    for folder in (staged, out, banks / "WFM", banks / "SPP OOS"):
        folder.mkdir(parents=True)
    for folder in (staged, banks / "WFM", banks / "SPP OOS"):
        shutil.copy(SQX, folder / "S 1.sqx")
    own = sqxfile.identity(SQX)
    assert export_trades.lineage(P, "WFM", install, staged, out) == 0
    assert (out / "lineage.csv").read_text().splitlines()[1] == f"S 1,{own},{own}"


def test_the_audit_names_what_no_zip_holds(data: Path, tmp_path: Path) -> None:
    """A stored mother, its WFM report unsaved: FALTA once it is vouched for, gone once saved."""
    identity = write.put_sqx(SQX, "EURUSD_H1_x", {"project": P, "strategy": "S 1"})
    lineage(data, identity)
    falta, _ = audit.missing(P)
    assert any("reports/WFM/2026-10-08/wfm" in line for line in falta)
    assert any("raw/WFM/2026-10-08: exportacion" in line for line in falta)
    for stem, src, about in (late.unpaired(P, identity, set(), set(), tmp_path / "u")
                             + late.exports(P, identity, tmp_path / "e")):
        write.add(identity, stem, src, about)
    assert audit.missing(P) == ([], [])
    (data / "newthing" / P).mkdir(parents=True)        # a writer nobody gave a place
    assert audit.missing(P)[0] == [f"newthing/{P}: carpeta que el almacén no conoce"]


def test_t1_neighbours_are_cut_to_the_strategy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Step 13's T1 table keeps only the strategy's rows."""
    monkeypatch.setattr(extra, "DATA", tmp_path)
    day = tmp_path / "raw" / P / "T1_Neighbours" / "2026-10-10"
    day.mkdir(parents=True)
    pd.DataFrame({"strategy": ["S 1", "S 1", "S 2"], "neighbour": [1, 2, 3]}).to_parquet(day / "neighbours.parquet")
    got = extra.neighbours(P, "S 1", tmp_path / "out")
    assert got[0][0] == "vecinas" and got[0][2]["rows"] == 2
    assert extra.neighbours(P, "S 9", tmp_path / "out2") == []


def test_a_second_identity_is_an_alias_only_when_the_two_name_each_other_mother(data: Path, tmp_path: Path) -> None:
    """A variant (its mother does not point back) is another strategy; a mutual pair is one."""
    lineage(data, MOTHER)
    assert late.aliases(P, MOTHER) == frozenset() and late.aliases(P, WFM) == frozenset()
    (data / "raw" / P / "WFM" / "2026-10-08" / "lineage.csv").write_text(
        f"strategy,identity,mother\nS 1,{WFM},{MOTHER}\nS 1,{MOTHER},{WFM}\n")
    extra.table.cache_clear()
    assert late.aliases(P, MOTHER) == {WFM} and late.aliases(P, WFM) == {MOTHER}
    from core.archive import collect
    monkey = pytest.MonkeyPatch()
    monkey.setattr(collect, "DATA", data)
    try:
        assert not any(e["study"] == "wfm" for e in collect.freeze(P, MOTHER, tmp_path / "x")[0])
        got = collect.freeze(P, MOTHER, tmp_path / "y", late.aliases(P, MOTHER))[0]
    finally:
        monkey.undo()
    assert [e["names"] for e in got if e["study"] == "wfm"] == [["S 1"]]
