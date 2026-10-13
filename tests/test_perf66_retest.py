"""Encargo 66, tanda E: export_retest packs a live session's `.abk` in place of one orderstocsv pass, fakes only."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import sqxfile
from sqx.export import export_retest


def _retest(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, banks: dict) -> tuple[dict, list]:
    """Run export_retest on fake databanks A and B; `banks` maps a databank to the `.abk` to leave for it."""
    from core import bankfile
    from tests.test_perf66_algobank import _csv, strategies, write
    bank, ran, written = strategies(), [], {}
    for db, held in banks.items():
        if held:
            (tmp_path / "abk").mkdir(parents=True, exist_ok=True)
            write(tmp_path / "abk" / f"{db}.abk", bank)

    def stage(project: str, db: str, dest: Path, limit: int, install: Path, prefix: str) -> dict:
        """The databank's three strategies, as files named after them."""
        dest.mkdir(parents=True, exist_ok=True)
        for s in bank:
            (dest / f"{prefix}{s['name']}.sqx").write_text(s["xml"])
        return {s["name"]: "H1" for s in bank}

    def trades(sqx: Path, raw: Path, data: str) -> None:
        """orderstocsv: one CSV per staged file."""
        raw.mkdir()
        ran.append(sorted(f.name for f in sqx.iterdir()))
        for f in sqx.iterdir():
            _csv(raw / f"{f.stem}.csv", next(s for s in bank if f.stem.endswith(s["name"])),
                 {"XAUUSD": 2, "XAGUSD": 3})

    for name, val in {"export_dir": lambda p, db, day, batch="": tmp_path / "out" / db,
                      "worker_dir": lambda role: tmp_path, "stage": stage,
                      "databank_dir": lambda p, db, install: tmp_path / "none",
                      "sign": lambda *a: 0}.items():
        monkeypatch.setattr(export_retest, name, val)
    monkeypatch.setattr(export_retest.exportdrv, "trades", trades)
    monkeypatch.setattr(export_retest.identities, "many", lambda files, n: {
        f: sqxfile._hashed(f.read_text()) for f in files})
    monkeypatch.setattr(export_retest.membank, "bank_dir", lambda p, r: tmp_path / "abk")
    monkeypatch.setattr(export_retest.manifest, "write",
                        lambda out, meta, cmd, res, since: written.__setitem__(out.name, res))
    for db in banks:
        (tmp_path / "out" / db).mkdir(parents=True)
    monkeypatch.setattr(sys, "argv", ["x", "--project", "Test_X", "--role", "custodian",
                                      *[a for db in banks for a in ("--databank", db)]])
    monkeypatch.setattr(export_retest.membank, "take", lambda p, r, db, ids, mt, data: (
        bankfile.load(tmp_path / "abk" / f"{db}.abk") if banks[db] else None))
    export_retest.main()
    return written, ran


def test_export_retest_from_memory_equals_orderstocsv(monkeypatch: pytest.MonkeyPatch,
                                                      tmp_path: Path) -> None:
    """P4: a databank taken from the `.abk` packs the same Parquet and manifest block as the orderstocsv route."""
    mem, none = tmp_path / "mem", tmp_path / "csv"
    got_mem, ran_mem = _retest(monkeypatch, mem, {"A": True, "B": True})
    got_csv, ran_csv = _retest(monkeypatch, none, {"A": False, "B": False})
    assert ran_mem == [] and len(ran_csv) == 1 and len(ran_csv[0]) == 6      # no sqcli at all vs today's one pass
    assert got_mem == got_csv
    for db in "AB":
        pd.testing.assert_frame_equal(pd.read_parquet(mem / "out" / db / "trades.parquet"),
                                      pd.read_parquet(none / "out" / db / "trades.parquet"),
                                      check_exact=True, check_categorical=True)


def test_export_retest_mixed_sends_only_the_untaken_to_orderstocsv(monkeypatch: pytest.MonkeyPatch,
                                                                   tmp_path: Path) -> None:
    """P4: with A taken and B not, orderstocsv sees B's strategies only and both directories are written."""
    got, ran = _retest(monkeypatch, tmp_path, {"A": True, "B": False})
    assert len(ran) == 1 and all(n.startswith("1__") for n in ran[0]) and len(ran[0]) == 3
    assert set(got) == {"A", "B"} and all((tmp_path / "out" / db / "trades.parquet").exists() for db in "AB")
