"""The store under injected faults: a cut write, a missing file, a flipped byte, an orphan."""

import os
from pathlib import Path

import pytest

from core.store import verify, write

SQX = Path(__file__).parent / "fixtures" / "strategy.sqx"


@pytest.fixture
def stored(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """One strategy saved in a throwaway store with one set of tests; its identity."""
    monkeypatch.setattr(write, "store_dir", lambda: tmp_path / "store")
    monkeypatch.setattr(verify, "store_dir", lambda: tmp_path / "store")
    identity = write.put_sqx(SQX, "EURUSD_H1_x", {"project": "Test_x"})
    write.add(
        identity,
        "gate.Results.2026-10-07",
        results_of(tmp_path, "a"),
        {"study": "gate"},
    )
    return identity


def results_of(tmp: Path, content: str) -> Path:
    """A folder standing for one study's results about the strategy."""
    src = tmp / f"src-{content}"
    (src / "estrategias").mkdir(parents=True, exist_ok=True)
    (src / "estrategias" / "S.json").write_text(content)
    (src / "verdict.csv").write_text("strategy,verdict\nS,MANTENER\n")
    return src


def test_what_was_saved_is_whole_and_read_only(stored: str) -> None:
    """The round trip: the folder is named by the identity its .sqx carries, and nothing is loose."""
    assert verify.check(stored) == []
    assert not os.access(write.folder(stored) / write.SQX, os.W_OK)
    assert (
        verify.stored() == [stored]
        and write.folder(stored).parent.name == "EURUSD_H1_x"
    )


def test_the_same_tests_again_write_nothing_and_new_ones_never_overwrite(
    stored: str, tmp_path: Path
) -> None:
    """Saving twice is one file; the same test under other results is a second file beside it."""
    before = (write.folder(stored) / "gate.Results.2026-10-07.zip").stat().st_mtime_ns
    assert (
        write.add(stored, "gate.Results.2026-10-07", results_of(tmp_path, "a"), {})
        == "gate.Results.2026-10-07.zip"
    )
    assert (
        write.folder(stored) / "gate.Results.2026-10-07.zip"
    ).stat().st_mtime_ns == before
    assert (
        write.add(stored, "gate.Results.2026-10-07", results_of(tmp_path, "b"), {})
        == "gate.Results.2026-10-07.2.zip"
    )
    assert len(write.manifest(stored)["files"]) == 2 and verify.check(stored) == []


def test_each_damage_is_named(stored: str) -> None:
    """A flipped byte, a deleted file, a stranger and a damaged .sqx are each reported."""
    here = write.folder(stored)
    z = here / "gate.Results.2026-10-07.zip"
    data = bytearray(z.read_bytes())
    data[len(data) // 2] ^= 0xFF
    z.chmod(0o644)
    z.write_bytes(bytes(data))
    assert verify.check(stored) == [
        "gate.Results.2026-10-07.zip no tiene la huella del manifiesto"
    ]
    z.unlink()
    assert verify.check(stored) == ["falta gate.Results.2026-10-07.zip"]
    (here / "extra.zip").write_bytes(b"x")
    assert "extra.zip no está en el manifiesto" in verify.check(stored)
    (here / write.SQX).chmod(0o644)
    (here / write.SQX).write_bytes(b"not a zip")
    assert any(line.startswith("strategy.sqx") for line in verify.check(stored))


def test_a_write_cut_before_the_rename_leaves_the_folder_as_it_was(
    stored: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The process dies with the temporary on disk: no half file, and the next save goes through."""

    def dead(*_: object) -> None:
        """The process dying at this call."""
        raise KeyboardInterrupt

    monkeypatch.setattr(write.os, "replace", dead)
    with pytest.raises(KeyboardInterrupt):
        write.add(stored, "crossTF.CrossTF.2026-10-07", results_of(tmp_path, "c"), {})
    assert (
        verify.check(stored) == []
        and "crossTF.CrossTF.2026-10-07.zip" not in write.manifest(stored)["files"]
    )
    monkeypatch.undo()
    monkeypatch.setattr(write, "store_dir", lambda: tmp_path / "store")
    monkeypatch.setattr(verify, "store_dir", lambda: tmp_path / "store")
    write.add(stored, "crossTF.CrossTF.2026-10-07", results_of(tmp_path, "c"), {})
    assert verify.check(stored) == [] and len(write.manifest(stored)["files"]) == 2


def test_a_cut_between_the_file_and_the_manifest_is_seen_and_then_adopted(
    stored: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The file landed and the manifest never named it: an orphan verify shows and a re-save adopts."""
    real = write.record

    def dead(*_: object) -> None:
        """The process dying at this call."""
        raise KeyboardInterrupt

    monkeypatch.setattr(write, "record", dead)
    with pytest.raises(KeyboardInterrupt):
        write.add(stored, "crossTF.CrossTF.2026-10-07", results_of(tmp_path, "c"), {})
    assert verify.check(stored) == [
        "crossTF.CrossTF.2026-10-07.zip no está en el manifiesto"
    ]
    monkeypatch.setattr(write, "record", real)
    assert (
        write.add(stored, "crossTF.CrossTF.2026-10-07", results_of(tmp_path, "c"), {})
        == "crossTF.CrossTF.2026-10-07.zip"
    )
    assert verify.check(stored) == []


def test_a_failed_step_is_marked_and_nothing_is_deleted(stored: str) -> None:
    """Failing a later test writes the verdict in the manifest; the .sqx and the tests stay."""
    write.step(
        stored,
        "12",
        {"verdict": "DESCARTAR", "outcome": "fail", "reason": "z_new=-1.2", "run": "r"},
    )
    assert write.manifest(stored)["steps"]["12"]["verdict"] == "DESCARTAR"
    assert verify.check(stored) == [] and (write.folder(stored) / write.SQX).exists()


def test_equal_files_of_two_strategies_are_one_on_disk(
    stored: str, tmp_path: Path
) -> None:
    """A population file saved under two names is one inode, and each folder still verifies."""
    write.add(stored, "gate.poblacion", results_of(tmp_path, "pop"), {})
    write.add(stored, "otra.poblacion", results_of(tmp_path, "pop"), {})
    here = write.folder(stored)
    assert (here / "gate.poblacion.zip").stat().st_ino == (
        here / "otra.poblacion.zip"
    ).stat().st_ino
    assert (here / "gate.poblacion.zip").stat().st_nlink == 3 and verify.check(
        stored
    ) == []
    assert verify.stored() == [stored]  # the pool is not a strategy


def test_a_strategy_owns_its_sisters_rows_and_nobody_elses(tmp_path: Path) -> None:
    """`Strategy 1.2.3` is not `Strategy 1.2.31`; its scaled sisters are its own; a table with
    somebody else's rows is the population's and one with only its rows is not."""
    import pandas as pd
    from core.store import extra

    frame = pd.DataFrame(
        {
            "strategy": [
                "Strategy 1.2.3",
                "Strategy 1.2.31",
                "Strategy 1.2.3_ScaledH1",
                "Strategy 1.2.31_ScaledH1",
            ],
            "x": range(4),
        }
    )
    assert list(extra.family(frame, "Strategy 1.2.3")["x"]) == [0, 2]
    assert list(extra.family(frame.assign(identity=""), "Strategy 1.2.3")["x"]) == [
        0,
        2,
    ]  # "" is nobody
    src = tmp_path / "study"
    src.mkdir()
    frame.to_csv(src / "funnel.csv", index=False)
    frame.iloc[[0, 2]].to_parquet(src / "cells.parquet")
    (src / "study.json").write_text('{"population": 4}')
    (src / "S.json").write_text('{"strategy": "Strategy 1.2.3"}')
    assert extra.population(src, "id", ["Strategy 1.2.3"], tmp_path / "pop")
    assert sorted(p.name for p in (tmp_path / "pop").iterdir()) == [
        "funnel.csv",
        "study.json",
    ]
    assert sorted(p.name for p in src.iterdir()) == ["S.json", "cells.parquet"]


def test_two_identities_each_other_s_mother_keep_the_gate_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The gate's identity is the stored one: a mutual lineage must not swap it with the retest copy's."""
    from core.store import late, save

    rep, run = tmp_path / "reports/P/Results/d/gate", tmp_path / "autopilot/P/r/paso-8"
    for folder, ident in ((rep, "A"), (run, "B")):
        folder.mkdir(parents=True)
        (folder / "verdict.csv").write_text(
            f"strategy,identity,verdict\nS,{ident},MANTENER\n", encoding="utf-8"
        )
    monkeypatch.setattr(save, "DATA", tmp_path)
    monkeypatch.setattr(
        late, "mothers", lambda p: {"A": "B", "B": "A"}
    )  # mutual: gate A stays, B maps to A
    assert list(save.verdicts("P")) == ["A"]
