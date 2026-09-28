"""The strategy archive on a real strategy: frozen versions never overwritten, read back equal, nothing run."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from core import sqxfile  # noqa: E402
from core.archive import read, write  # noqa: E402
from core.paths import DATA, ROOT  # noqa: E402
from ui.daemon import gateview  # noqa: E402
from ui.daemon.results import matrix, runs  # noqa: E402
from ui.daemon.tearsheet import harvest, sheet  # noqa: E402

PROJECT, DATABANK, FAMILY = "Test_USDJPY_donchianUpperCrossUp_M30", "Results", "donchianUpperCrossUp"
IDENTITY = "4d679e0c2ce2a63ee53bc6cb305830bcaf5a74997e6e6e2c1deeb4c30f307048"   # Strategy 10.11.79
# The install's databanks of this Test_ project are gone; the SPP export kept the file.
SQX = DATA / "raw" / PROJECT / "SPP_IS" / "2026-09-27" / "strategies" / "Strategy 10.11.79.sqx"
CHILD = """
import os, subprocess, sys
from pathlib import Path
sys.path.insert(0, {root!r})
def refuse(*a, **k):
    raise AssertionError("load() tried to run something")
subprocess.Popen = os.system = os.fork = os.posix_spawn = os.execv = refuse
from core.archive import read
read.archive_dir = lambda: Path({tmp!r})
got = read.load({identity!r})
loaded = sorted(m for m in sys.modules if m.split(".")[0] in ("studies", "ui"))
assert not loaded, loaded
print("child ok:", sum(len(v) for v in got["results"].values()), "results, no studies.*, no ui.*")
"""


def same(a: object, b: object) -> bool:
    """Equal as the daemon would serve them: the same JSON text."""
    return json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)


def unseal(folder: Path) -> None:
    """Give the owner write access back so a temporary archive can be deleted."""
    for root, dirs, _ in os.walk(folder):
        os.chmod(root, 0o755)


def main() -> None:
    """Archive twice into a temporary root, refuse a third on a taken stamp, compare with live."""
    tmp = Path(tempfile.mkdtemp())
    write.archive_dir = read.archive_dir = lambda: tmp
    try:
        stamps = iter(["2026-01-01T0000", "2026-01-01T0000", "2026-01-01T0001", "2026-01-01T0002"])
        write._stamp = lambda: next(stamps)
        first = write.archive(PROJECT, DATABANK, IDENTITY, "16", "prueba", family=FAMILY, sqx=SQX)
        before = (first / "manifest.json").read_bytes()
        try:
            write.archive(PROJECT, DATABANK, IDENTITY, "16", family=FAMILY, sqx=SQX)
            raise AssertionError("a second archive on the same stamp was not refused")
        except FileExistsError:
            pass
        write.archive(PROJECT, DATABANK, IDENTITY, "17", family=FAMILY, sqx=SQX)
        assert read.versions(IDENTITY) == ["2026-01-01T0000", "2026-01-01T0001"], read.versions(IDENTITY)
        assert (first / "manifest.json").read_bytes() == before, "the first version changed"
        assert all(not (p.stat().st_mode & 0o222) for p in first.rglob("*")), "not sealed"
        print("versions:", read.versions(IDENTITY), "· same stamp refused · sealed read-only")

        held, busy = write.find.install_of, write.find.writing
        write.find.install_of, write.find.writing = lambda p, d: ("custodian", tmp), lambda t, p: True
        try:
            write.archive(PROJECT, DATABANK, IDENTITY, "16", family=FAMILY, sqx=SQX)
            raise AssertionError("archived while SQX was writing the project")
        except RuntimeError:
            pass
        finally:
            write.find.install_of, write.find.writing = held, busy
        print("refused while SQX writes the project")

        got = read.load(IDENTITY)
        assert sqxfile.identity(Path(got["sqx"])) == IDENTITY
        newest = {(e["databank"], e["study"]): e for e in got["manifest"]["studies"]
                  if e["study"] in got["results"].get(e["databank"], {})}
        for (databank, study), e in newest.items():
            live = runs.result(PROJECT, databank, study, e["named"] or e["names"][0], IDENTITY, "")
            assert same(got["results"][databank][study], live), (databank, study)
            live = runs.result(PROJECT, databank, study, "", "", e["day"])
            assert same(got["populations"][databank][study], live), (databank, study)
        for databank, cells in got["cells"].items():
            assert same(cells, matrix.matrix(PROJECT, databank)["cells"].get(IDENTITY, {}))
        report = gateview.gate(PROJECT, DATABANK, got["gate"]["report_day"])
        report["rows"] = [r for r in report["rows"] if r["identity"] == IDENTITY]
        assert same(got["gate"]["report"], report), "the gate report differs"
        live = gateview.strategy(PROJECT, DATABANK, got["tearsheet"]["day"], IDENTITY)
        assert same(got["gate"]["strategy"], live), "the gate sheet differs"
        live = harvest.read(PROJECT, DATABANK, IDENTITY)
        pd.testing.assert_frame_equal(got["tearsheet"]["equity"], live["equity"])
        pd.testing.assert_frame_equal(got["tearsheet"]["trades"], live["trades"])
        drawn = [sheet.build(got["tearsheet"]), sheet.build(live)]
        for d in drawn:
            d.pop("computed_at")                  # stamped with now() at second precision
        assert same(*drawn), "the Ficha differs"
        try:
            read.load("0" * 64)
            raise AssertionError("an identity never archived did not raise")
        except FileNotFoundError as e:
            print("unknown identity:", e)
        print("skipped:", [k["path"] for k in got["manifest"]["skipped"]], "· loose:", got["manifest"]["loose"])
        print("equal to live:", {d: sorted(s) for d, s in got["results"].items()}, "+ Ficha + gate")

        out = subprocess.run([sys.executable, "-c", CHILD.format(root=str(ROOT), tmp=str(tmp),
                                                                 identity=IDENTITY)],
                             capture_output=True, text=True)
        assert out.returncode == 0, out.stderr
        print(out.stdout.strip())
    finally:
        unseal(tmp)
        shutil.rmtree(tmp)
    print("test_archive: OK")


if __name__ == "__main__":
    main()
