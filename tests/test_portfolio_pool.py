#!/usr/bin/env python3
"""Known-answer test of the declared pool: hash stability, prohibitions, frozen declare, dev mark."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import portfolio.common.construct.inputs.pool as pool

REAL_IDENTITY = "4d679e0c2ce2a63ee53bc6cb305830bcaf5a74997e6e6e2c1deeb4c30f307048"
REAL_VERSION = "2026-09-28T0919"

FAKE_STEPS = {("AAA", "v1"): "16.5", ("BBB", "v1"): "8", ("BBB", "v2"): "8"}

FAILURES = []


def check(name: str, ok: bool) -> None:
    """Print one line per case; remember the failures."""
    print(f"{'OK   ' if ok else 'FALLO'}  {name}")
    if not ok:
        FAILURES.append(name)


def _fake_load(identity: str, version: str) -> dict:
    """Stands in for `core.archive.read.load`, for identities with no real archive folder."""
    return {"manifest": {"step": FAKE_STEPS[(identity, version)]}}


def main() -> None:
    """Run every case in one temp `pool.ROOT`, print a line each, exit non-zero on any failure."""
    real_load = pool.archive_read.load
    with tempfile.TemporaryDirectory() as tmp:
        pool.ROOT = Path(tmp)
        pool.archive_read.load = _fake_load

        rows = [{"identity": "AAA", "version": "v1"}, {"identity": "BBB", "version": "v1", "near": True}]
        pool.declare("p1", rows, added_by="test")
        pool.declare("p1_reordered", list(reversed(rows)), added_by="test")
        h1 = pool.read("p1", None)["hash"]
        h2 = pool.read("p1_reordered", None)["hash"]
        check("hash stable under row order", h1 == h2)

        pool.declare("p1_v2", [rows[0], {"identity": "BBB", "version": "v2"}], added_by="test")
        h3 = pool.read("p1_v2", None)["hash"]
        check("hash changes with a version", h1 != h3)

        try:
            pool.declare("p1", rows, added_by="test")
            check("a second declare of the same name is refused", False)
        except FileExistsError:
            check("a second declare of the same name is refused", True)

        (pool.ROOT / "prohibitions").mkdir(parents=True)
        (pool.ROOT / "prohibitions" / "firmX.csv").write_text(
            "identity,version,firm,plan,rule,reason,decided_on\n"
            "AAA,v1,firmX,plan1,weekend,no holding over the weekend,2026-09-30\n")
        got = pool.read("p1", "firmX")
        check("prohibited identity dropped", len(got["members"]) == 1
              and got["members"][0]["identity"] == "BBB")
        check("prohibited count", got["n_prohibited"] == 1 and got["n_pool"] == 2)
        check("prohibited row carries its reason", got["prohibited"][0]["reason"]
              == "no holding over the weekend")

        pool.archive_read.load = real_load
        pool.declare("real", [{"identity": REAL_IDENTITY, "version": REAL_VERSION}], added_by="test")
        real_got = pool.read("real", None)
        check("development true for step 16.5", real_got["members"][0]["development"] == "True")

    if FAILURES:
        print(f"\n{len(FAILURES)} fallo(s): {FAILURES}")
        sys.exit(1)
    print("\ntodo OK")


if __name__ == "__main__":
    main()
