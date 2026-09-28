"""Identity resolution after the databank left every install: the cosecha, the kept .sqx, and no guess."""

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import DATA  # noqa: E402
from core.study import identity, output  # noqa: E402
from sqx.export import export_trades  # noqa: E402

PROJECT = "Test_USDJPY_donchianUpperCrossUp_M30"      # retired: no install holds its databanks
RAW = DATA / "raw" / PROJECT
KNOWN = {"Strategy 10.11.79": "4d679e0c2ce2a63ee53bc6cb305830bcaf5a74997e6e6e2c1deeb4c30f307048",
         "Strategy 9.25.72": "2d1ac02dd185f3027469ee8d8d9cbc809d64e048393dc4972eb2f82fb42d2da4"}


def exporters() -> None:
    """What the two exporters leave behind signs the export, on copies in a scratch folder."""
    names = list(KNOWN)
    kept = RAW / "SPP_IS" / "2026-09-27" / "strategies"
    with tempfile.TemporaryDirectory() as tmp:
        staged, retest, trades = (Path(tmp) / n for n in ("staging", "retest", "trades"))
        for folder in (staged, retest, trades):
            folder.mkdir()
        for n in names:
            shutil.copy(kept / f"{n}.sqx", staged / f"1__{n}.sqx")    # export_retest's staging
            shutil.copy(kept / f"{n}.sqx", staged / f"0__{n}.sqx")    # another databank's leg
        assert identity.from_export(retest, names) == dict.fromkeys(names)
        assert export_trades.sign(staged, retest, "1__") == 2
        shutil.rmtree(staged)
        assert identity.from_export(retest, names) == KNOWN
        staged.mkdir()
        for n in names:
            shutil.copy(kept / f"{n}.sqx", staged / f"{n}.sqx")       # export_trades' staging
        assert export_trades.sign(staged, trades) == 2
        shutil.rmtree(staged)
        assert identity.from_export(trades, names) == KNOWN


def main() -> None:
    """Each source on its own, then the chain, then the names nobody holds."""
    names = list(KNOWN)
    assert identity.lookup(PROJECT, "Results", names) == dict.fromkeys(names)
    # The cosecha names the build databank on `strategy_build` and its OOS one on `strategy`.
    assert identity.from_harvest(PROJECT, "Results", names) == KNOWN
    assert identity.from_harvest(PROJECT, "OOS", names) == KNOWN
    # A cosecha taken after the export is not trusted: the databank may have been rebuilt.
    assert identity.from_harvest(PROJECT, "OOS", names, "2026-09-26") == dict.fromkeys(names)
    # A databank no cosecha paired gets nothing from it, whatever its names look like.
    assert identity.from_harvest(PROJECT, "Retest Markets - Family", names) == dict.fromkeys(names)
    # export_spp keeps the .sqx beside `spp/`, in `<day>/strategies/`.
    assert identity.from_export(RAW / "SPP_IS" / "2026-09-27" / "spp", names) == KNOWN
    assert output.identify(RAW / "OOS" / "2026-09-27", names) == KNOWN
    assert output.identify(RAW / "SPP_IS" / "2026-09-27" / "spp", names) == KNOWN
    # The retest copy `(1)` and its bare twin are two records of another databank: never guessed.
    lost = output.identify(RAW / "Retest_Markets_-_Family" / "2026-09-27",
                           ["Strategy 10.11.79(1)", "Strategy 10.11.79"])
    assert lost == {"Strategy 10.11.79(1)": None, "Strategy 10.11.79": None}, lost
    assert identity.note(lost).startswith("2 de 2 sin identidad")
    assert identity.note(KNOWN) == "" and identity.warning(KNOWN["Strategy 9.25.72"]) == []
    assert identity.warning(None)[0]["code"] == "identidad"
    exporters()
    print("identity ok: cosecha (build and OOS side), kept .sqx, day bound, no guess across databanks, both exporters leave identity.csv")


if __name__ == "__main__":
    main()
