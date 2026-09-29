#!/usr/bin/env python3
"""Known-answer test for `sqx.projects.builder`: a non-XAUUSD project must actually swap
feed, and a failed build must leave nothing behind (OPEN.md issues 34-35).

Builds are staged into a throwaway temp directory standing in for a headless install —
`sqx.projects.builder.worker_dir` is monkeypatched, so this never touches a real SQX
install, never talks to a worker's HTTP API, and writes no data outside /tmp.
"""

import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.datapaths import projects_backup
from core.paths import MASTER
from sqx.projects import builder, source

TEMPLATE = (Path(__file__).resolve().parent.parent / "tools/sqx-lab/plugins/sqx-lab/skills/"
            "sqx-strategy-template/engine/skeletons/market_skeleton.sqx")
DONOR = projects_backup("XAUUSD_base_2026-09-21") / "project.cfx"
# A project SQX itself wrote and that carries both USDJPY's session and its feed —
# read-only, on the master. `source.pick` would find this one on its own; passed
# explicitly here so the test does not depend on what else is on disk today.
USDJPY_SOURCE = MASTER / "user/projects/USDJPY/project.cfx"

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    """Record one assertion without stopping the run, so one failure doesn't hide the rest."""
    if ok:
        print(f"  ok  {label}")
    else:
        print(f"  FAIL {label}" + (f" — {detail}" if detail else ""))
        FAILURES.append(label)


def project_texts(cfx: Path) -> dict[str, str]:
    """Every task XML of a built project, decoded."""
    with zipfile.ZipFile(cfx) as z:
        return {n: z.read(n).decode("utf-8", "replace") for n in z.namelist()
                if n.endswith(".xml") and n != "config.xml"}


def test_usdjpy_feedswap() -> None:
    """Building USDJPY from the XAUUSD donor must carry no trace of gold."""
    print("test_usdjpy_feedswap")
    if not USDJPY_SOURCE.exists():
        print(f"  SKIP — {USDJPY_SOURCE} not on this machine")
        return
    with tempfile.TemporaryDirectory(prefix="sqx-test-install-") as install:
        builder.worker_dir = lambda role: Path(install)
        done = builder.build(
            name="Test_fixture_usdjpy_feedswap", template=TEMPLATE, symbol="USDJPY",
            role="conductor", timeframe="M30", strategies=50, minutes=5, donor=DONOR,
            session_from=USDJPY_SOURCE)

        out = Path(done["cfx"])
        check("project.cfx installed", out.exists())
        check("feed actually swapped", done["feed_replaced"] is not None, str(done["feed_replaced"]))
        check("every task priced (no zero Setup count)",
              bool(done["setups"]) and all(done["setups"].values()), str(done["setups"]))
        check("session is USDJPY's, not gold's", done["session"] == "USDJPY_ftmo",
              done["session"])

        texts = project_texts(out)
        donor_feed = done["feed_replaced"]
        stray = {n for n, t in texts.items() if donor_feed in t}
        check("donor feed (XAUUSD) gone from every task", not stray, str(stray))
        stray_spread = {n for n, t in texts.items() if 'spread="10.0"' in t}
        # 10.0 is gold's spread on the frozen donor; USDJPY's own is a different figure
        # (assets/symbols/USDJPY.yaml). Not a hard failure by itself (10.0 could coincide
        # by chance) but worth a look if it fires.
        if stray_spread:
            print(f"  note: spread=\"10.0\" (gold's) still literally present in {stray_spread} "
                  "— check by hand whether that is coincidence")
        check("main chart carries USDJPY's feed",
              all(done["feed"] in t for n, t in texts.items() if n.startswith("Build")),
              done["feed"])


def test_failed_build_leaves_nothing() -> None:
    """No project SQX has ever written defines an index's session. That must refuse
    cleanly, before touching the install — not after a half-built .cfx is on disk."""
    print("test_failed_build_leaves_nothing")
    from core.assetdata import load
    asset = load("USA500")
    borrow = source.pick(DONOR, asset["session"], asset["sqx_symbol"])
    check("precondition: no project defines USA500's session yet (documents today's gap)",
          borrow is None, str(borrow))

    with tempfile.TemporaryDirectory(prefix="sqx-test-install-") as install:
        builder.worker_dir = lambda role: Path(install)
        raised = False
        try:
            builder.build(
                name="Test_fixture_usa500_feedswap", template=TEMPLATE, symbol="USA500",
                role="conductor", timeframe="M30", strategies=50, minutes=5, donor=DONOR,
                session_from=borrow)
        except SystemExit:
            raised = True
        check("build refuses (SystemExit)", raised)
        leftover = list(Path(install, "user", "projects").glob("*")) \
            if Path(install, "user", "projects").exists() else []
        check("nothing left in the install after the refusal", not leftover, str(leftover))


def main() -> None:
    """Run both known-answer checks and exit non-zero if either found a regression."""
    test_usdjpy_feedswap()
    test_failed_build_leaves_nothing()
    if FAILURES:
        print(f"\ntest_builder_feedswap: FAILED — {', '.join(FAILURES)}")
        sys.exit(1)
    print("\ntest_builder_feedswap: ok")


if __name__ == "__main__":
    main()
