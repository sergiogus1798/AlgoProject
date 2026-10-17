"""collect: a planted store stands for gorilla; rsync runs between two local folders, no ssh."""

import json
import subprocess
from pathlib import Path

import pytest

from core.store import collect


def plant(data: Path, ident: str = "1530c225") -> None:
    """One survivor folder in a store standing for gorilla."""
    folder = data / "store" / "DAX40_H1_" / f"Strategy 1.2.3 {ident}"
    folder.mkdir(parents=True)
    (folder / "strategy.sqx").write_bytes(b"sqx")
    origin: dict[str, str] = {"project": "Test_A", "symbol": "DAX40", "timeframe": "H1"}
    (folder / "manifest.json").write_text(json.dumps({"origin": origin}))
    (data / "projects").mkdir()
    (data / "projects" / "registry.csv").write_text(
        "name,install,symbol\r\nTest_A,SQX_w2,DAX40\r\n", newline=""
    )
    (data / "reports" / "Test_A").mkdir(parents=True)
    for sub in ("d", "_aparte"):
        (data / "harvest" / "Test_A" / "Results" / sub).mkdir(parents=True)
        (data / "harvest" / "Test_A" / "Results" / sub / "trades.parquet").write_text(
            "t"
        )
    (data / "reports" / "Test_A" / "r.csv").write_text("a\n")


def test_collect_lands_suffixed_and_never_overwrites(tmp_path: Path) -> None:
    """A collect lands suffixed; a repeat leaves it alone."""
    gor, here = tmp_path / "gorilla", tmp_path / "here"
    plant(gor)
    plan = collect.listing("Test_A", gor)
    assert collect.listing("Test_B", gor)["folders"] == []

    dry = collect.collect(plan, f"{gor}/", here, dry=True)
    assert dry[0].startswith("traería") and not (here / "store").exists()

    out = collect.collect(plan, f"{gor}/", here)
    got = here / "store" / "DAX40_H1__gorilla" / "Strategy 1.2.3_gorilla 1530c225"
    assert (got / "strategy.sqx").read_bytes() == b"sqx"
    assert not (here / "ledger").exists()  # the ledger comes by bin/ledger-pull.sh

    (got / "strategy.sqx").write_bytes(b"edited")  # a second collect leaves it alone
    again = collect.collect(plan, f"{gor}/", here)
    assert (got / "strategy.sqx").read_bytes() == b"edited"
    assert again[0].startswith("existe")
    assert out[0].startswith("traída")


def test_same_identity_held_locally_is_not_fetched(tmp_path: Path) -> None:
    """An identity already held locally is not fetched."""
    gor, here = tmp_path / "gorilla", tmp_path / "here"
    plant(gor)
    plant(here)  # the same strategy is already a local survivor
    out = collect.collect(collect.listing("Test_A", gor), f"{gor}/", here)
    assert out[0].startswith("ya local")
    assert not (here / "store" / "DAX40_H1__gorilla").exists()


def test_failed_rsync_leaves_no_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A fetch that fails leaves neither the target nor the temp, so the next run retries."""
    gor, here = tmp_path / "gorilla", tmp_path / "here"
    plant(gor)

    def boom(src: str, dest: Path) -> None:
        """rsync dies after creating a partial file."""
        (dest / "partial").write_text("x")
        raise subprocess.CalledProcessError(23, "rsync", stderr="boom")

    monkeypatch.setattr(collect, "_rsync", boom)
    with pytest.raises(subprocess.CalledProcessError):
        collect.collect(collect.listing("Test_A", gor), f"{gor}/", here)
    assert not list((here / "store").glob("*/*")) and not list(
        (here / "store").glob(".collect-*")
    )


def test_registry_row_and_reports_come_marked_and_append_only(tmp_path: Path) -> None:
    """The registry row is appended once with a gorilla install; reports land; a repeat changes nothing."""
    gor, here = tmp_path / "gorilla", tmp_path / "here"
    plant(gor)
    (here / "projects").mkdir(parents=True)
    reg = here / "projects" / "registry.csv"
    reg.write_text("name,install,symbol\r\nOther,SQX_w1,EURUSD\r\n", newline="")
    plan = collect.listing("Test_A", gor)
    collect.collect(plan, f"{gor}/", here)
    assert reg.read_bytes().decode() == (
        "name,install,symbol\r\nOther,SQX_w1,EURUSD\r\nTest_A,SQX_w2_gorilla,DAX40\r\n"
    )
    assert (here / "reports" / "Test_A" / "r.csv").read_text() == "a\n"
    assert (here / "harvest" / "Test_A" / "Results" / "d" / "trades.parquet").is_file()
    assert not (here / "harvest" / "Test_A" / "Results" / "_aparte").exists()
    again = collect.collect(plan, f"{gor}/", here)
    assert (
        reg.read_bytes().decode().count("Test_A") == 1
        and "existe    registry" in again[1]
    )


def test_archive_names_what_is_missing(tmp_path: Path) -> None:
    """A survivor no report judges, or a cell that gives no family, fails naming it (rule 11)."""
    from portfolio.common.construct import adopt

    folder = tmp_path / "S 1_gorilla abcd1234"
    folder.mkdir()
    man = {
        "identity": "f" * 64,
        "cell": "DAX40_H1_simple_long",
        "origin": {"symbol": "DAX40", "timeframe": "H1"},
    }
    (folder / "manifest.json").write_text(json.dumps(man))
    with pytest.raises(RuntimeError, match="ningún informe"):
        adopt._archive("Test_A", folder, {})
    man["cell"] = "OTHER"
    (folder / "manifest.json").write_text(json.dumps(man))
    with pytest.raises(RuntimeError, match="familia"):
        adopt._archive("Test_A", folder, {})


def test_archived_without_harvest_is_not_done(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A version with no harvest/trades.parquet is incomplete: _archive goes on to archive again."""
    from portfolio.common.construct import adopt

    monkeypatch.setattr(adopt, "archive_dir", lambda: tmp_path / "archive")
    monkeypatch.setattr(adopt, "versions", lambda i: ["2026-10-16T0000"])
    ident = "e" * 64
    folder = tmp_path / "S 1_gorilla eeee"
    folder.mkdir()
    (folder / "manifest.json").write_text(
        json.dumps(
            {
                "identity": ident,
                "cell": "OTHER",
                "origin": {"symbol": "A", "timeframe": "H1"},
            }
        )
    )
    version = tmp_path / "archive" / ident / "2026-10-16T0000"
    version.mkdir(parents=True)
    with pytest.raises(RuntimeError, match="familia"):  # got past «ya archivada»
        adopt._archive("Test_A", folder, {})
    (version / "harvest").mkdir()
    (version / "harvest" / "trades.parquet").write_text("t")
    assert adopt._archive("Test_A", folder, {}) == "ya archivada"
