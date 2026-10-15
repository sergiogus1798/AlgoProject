#!/usr/bin/env python3
"""Known-answer test of the declared pool: hash stability, prohibitions, frozen declare, dev mark."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import archive_planted  # noqa: E402

PLANTED = archive_planted.plant()  # before anything imports core.paths

import portfolio.common.construct.inputs.pool as pool  # noqa: E402

REAL_IDENTITY, REAL_VERSION = PLANTED["identity"], PLANTED["version"]

FAKE_STEPS = {
    ("AAA", "v1"): "16.5",
    ("BBB", "v1"): "8",
    ("BBB", "v2"): "8",
    ("CCC", "v1"): "16.5",
    ("DDD", "v1"): "16.5",
}

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

        rows = [
            {"identity": "AAA", "version": "v1"},
            {"identity": "BBB", "version": "v1", "near": True},
        ]
        pool.declare("p1", rows, added_by="test")
        pool.declare("p1_reordered", list(reversed(rows)), added_by="test")
        h1 = pool.read("p1", None)["hash"]
        h2 = pool.read("p1_reordered", None)["hash"]
        check("hash stable under row order", h1 == h2)

        pool.declare(
            "p1_v2", [rows[0], {"identity": "BBB", "version": "v2"}], added_by="test"
        )
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
            "AAA,v1,firmX,plan1,weekend,no holding over the weekend,2026-09-30\n"
        )
        got = pool.read("p1", "firmX")
        check(
            "prohibited identity dropped",
            len(got["members"]) == 1 and got["members"][0]["identity"] == "BBB",
        )
        check("prohibited count", got["n_prohibited"] == 1 and got["n_pool"] == 2)
        check(
            "prohibited row carries its reason",
            got["prohibited"][0]["reason"] == "no holding over the weekend",
        )

        # M6: two named members banned for firmX (one on every plan, one on one plan family)
        four = [{"identity": i, "version": "v1"} for i in ("AAA", "BBB", "CCC", "DDD")]
        pool.declare("p4", four, added_by="test")
        (pool.ROOT / "prohibitions" / "firmX.csv").write_text(
            ",".join(pool.PROHIBITION_COLUMNS) + "\n"
            "AAA,v1,firmX,,weekend,holds over the weekend,2026-10-05\n"
            "CCC,v1,firmX,firmX:express,news,trades the news window,2026-10-05\n"
            "ZZZ,v1,firmX,,weekend,not in this pool,2026-10-05\n"
        )
        with_x = pool.read("p4", "firmX")
        check(
            "--firm X: exactly the two banned members are out, and named",
            [m["identity"] for m in with_x["members"]] == ["BBB", "DDD"]
            and with_x["n_prohibited"] == 2
            and with_x["n_pool"] == 4
            and [(r["identity"], r["rule"]) for r in with_x["prohibited"]]
            == [("AAA", "weekend"), ("CCC", "news")],
        )
        whole = pool.read("p4", None)
        check(
            "without the flag nobody is out",
            whole["n_prohibited"] == 0 and len(whole["members"]) == 4,
        )
        other = pool.read("p4", "firmY")
        check(
            "--firm Y (no file): nobody is out, same hash as the whole pool",
            other["n_prohibited"] == 0
            and other["hash"] == whole["hash"] != with_x["hash"],
        )
        express = pool.read("p4", "firmX", "firmX:express:10000:USD")
        steps = pool.read("p4", "firmX", "firmX:2step:10000:USD")
        check(
            "a plan's pool loses the firm-wide ban and its own family's, not another family's",
            [m["identity"] for m in express["members"]] == ["BBB", "DDD"]
            and [m["identity"] for m in steps["members"]] == ["BBB", "CCC", "DDD"],
        )
        scoped = pool.scoped({"relaxed": {}}, "firmX", "firmX:2step:10000:USD")
        lines = pool.prohibited_lines("p4", scoped)
        check(
            "the report names the firm, the count and each member with its rule and reason",
            lines[0].startswith("Prohibiciones de firmX: 1 de 4")
            and len(lines) == 2
            and "AAA" in lines[1]
            and "weekend" in lines[1]
            and "holds over the weekend" in lines[1]
            and pool.declared("p4", scoped)["hash"] == steps["hash"]
            and pool.prohibited_lines("p4", pool.scoped({}, None)) == [],
        )

        pool.archive_read.load = real_load
        pool.declare(
            "real",
            [{"identity": REAL_IDENTITY, "version": REAL_VERSION}],
            added_by="test",
        )
        real_got = pool.read("real", None)
        check(
            "development true for step 16.5",
            real_got["members"][0]["development"] == "True",
        )

    if FAILURES:
        print(f"\n{len(FAILURES)} fallo(s): {FAILURES}")
        sys.exit(1)
    print("\ntodo OK")


if __name__ == "__main__":
    main()
