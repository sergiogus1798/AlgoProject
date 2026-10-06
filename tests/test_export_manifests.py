#!/usr/bin/env python3
"""A trades export and an SPP export of the same databank and day keep each other's files.

`export_trades` used to stage into `<day>/strategies/` and `rmtree` it — the folder `export_spp`
writes the mothers and their manifest into (📓 2026-09-29). Both `main()`s run here for real in
a temp data root, in the order that lost data (spp, trades, trades again); only SQX and the
parsers are stubbed. Then the audit's two manifest checks read the result.
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import manifest  # noqa: E402
from sqx.export import export_spp, export_trades  # noqa: E402
from tools import daily_audit  # noqa: E402

DAY = "raw/Test_P/SPP_IS"


def fake_export(staged: Path, csvs: Path) -> None:
    """Stand in for SQX's orderstocsv: one CSV per staged strategy."""
    csvs.mkdir()
    for f in staged.glob("*.sqx"):
        (csvs / f"{f.stem}.csv").write_text("x\n")


def fake_pack(files: list, out: Path, per_market: bool) -> dict:
    """Stand in for the Parquet packer."""
    out.write_text("parquet")
    return {"strategies": len(files)}


def fake_profiles(project: str, databank: str, install: Path, spill: Path) -> tuple[dict, dict]:
    """Stand in for the profile reader: no profile, but the scratch folder main() removes."""
    spill.mkdir(parents=True)
    return {}, {}


with tempfile.TemporaryDirectory() as tmp:
    data, bank = Path(tmp), Path(tmp) / "bank"
    bank.mkdir()
    (bank / "Strategy 1.sqx").write_text("sqx")
    for mod in (export_trades, export_spp):
        mod.export_dir = lambda project, databank, day, batch="": data / DAY / "today"
        mod.databank_dir = lambda project, databank, install: bank
    export_trades.exportdrv.trades = fake_export
    export_trades.tradepack.pack = fake_pack
    export_trades.sqxfile.symbol = lambda f: ("USDJPY", "USDJPY_M30")
    export_trades.sqxfile.identity = lambda f: "abc"
    export_spp.profiles = fake_profiles

    out = data / DAY / "today"
    for mod, extra in ((export_spp, []), (export_trades, ["--symbol", "USDJPY"]),
                       (export_trades, ["--symbol", "USDJPY"])):
        sys.argv = ["x", "--project", "Test_P", "--databank", "SPP IS", *extra]
        mod.main()
        assert manifest.read(out / "spp")["command"].startswith("export_spp.py"), mod.__name__
        assert manifest.read(out / "strategies")["counts"] == {"sqx": 1}, mod.__name__
        assert (out / "strategies" / "Strategy 1.sqx").exists(), mod.__name__
    assert manifest.read(out)["command"].startswith("export_trades.py")
    assert sorted(p.name for p in out.iterdir()) == [
        "identity.csv", "manifest.json", "spp", "strategies", "timeframes.csv", "trades.parquet"]

    # The audit: a manifest in the folder that holds the data, or above it, covers it; a
    # half-finished export (CSVs, no manifest) is reported once, by its dated folder.
    daily_audit.DATA = data
    assert daily_audit.exports_without_manifest() == []
    torn = data / "raw/Test_P/OOS/2026-01-01/trades"
    torn.mkdir(parents=True)
    (torn / "Strategy 1.csv").write_text("x\n")
    assert daily_audit.exports_without_manifest() == ["raw/Test_P/OOS/2026-01-01"]

    # code_version: this commit resolves, the pre-git marker is accepted by name, anything
    # else is reported.
    assert daily_audit.manifests_of_unknown_code() == []
    for name, version in (("old", manifest.PRE_GIT), ("lost", "0000000-dirty")):
        (data / "raw/Test_P" / name).mkdir()
        (data / "raw/Test_P" / name / "manifest.json").write_text(
            json.dumps({"code_version": version}))
    assert daily_audit.manifests_of_unknown_code() == ["raw/Test_P/lost (0000000-dirty)"]
print("ok")
