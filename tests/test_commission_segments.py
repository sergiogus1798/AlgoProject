#!/usr/bin/env python3
"""Known-answer test for the per-segment commission (owner, 2026-09-29): the max-per-segment
maths in `core.commission.per_segment`, and that a built project's Setups really carry each
task's own segment method — never one flat figure across the whole project.
"""

import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.assetdata import load
from core.commission import per_segment
from core.datapaths import projects_backup
from sqx.projects import builder

TEMPLATE = (Path(__file__).resolve().parent.parent / "tools/sqx-lab/plugins/sqx-lab/skills/"
            "sqx-strategy-template/engine/skeletons/market_skeleton.sqx")
DONOR = projects_backup("XAUUSD_base_2026-09-21") / "project.cfx"

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    """Record one assertion without stopping the run, so one failure doesn't hide the rest."""
    if ok:
        print(f"  ok  {label}")
    else:
        print(f"  FAIL {label}" + (f" — {detail}" if detail else ""))
        FAILURES.append(label)


def test_per_segment_known_answer() -> None:
    """A `$/lot` broker and a `%` broker built to disagree in exactly one direction per segment."""
    print("test_per_segment_known_answer")
    brokers = {"infinox": {"method": "SizeBased", "value": 8.0, "confirmed": True},
              "darwinex": {"method": "PercentageBased", "value": 0.005, "confirmed": True},
              "ftmo": {"method": "PercentageBased", "value": 0.0014, "confirmed": True},
              "unconfirmed": {"method": "SizeBased", "value": 999.0, "confirmed": False}}
    # At 1000 and point_value 100: Darwinex = 0.005/100*1000*100 = 5.0 < Infinox's flat 8.0.
    # At 3000: Darwinex = 0.005/100*3000*100 = 15.0 > Infinox's flat 8.0 — the winner flips.
    result = per_segment(brokers, {"build": 1000.0, "oos2": 3000.0}, point_value=100.0)
    check("build stays with the $/lot broker below the crossover price",
          result["build"] == {"broker": "infinox", "method": "SizeBased", "value": 8.0,
                              "usd_per_lot": 8.0}, result["build"])
    check("oos2 flips to the % broker above the crossover price",
          result["oos2"] == {"broker": "darwinex", "method": "PercentageBased", "value": 0.005,
                             "usd_per_lot": 15.0}, result["oos2"])
    check("an unconfirmed broker never wins however large its figure",
          all(r["broker"] != "unconfirmed" for r in result.values()), result)

    try:
        per_segment({"x": {"method": "SizeBased", "value": 1.0, "confirmed": False}},
                   {"build": 1.0}, 1.0)
        raise AssertionError("no confirmed broker must raise, not silently return nothing")
    except ValueError:
        pass


def test_xauusd_real_file() -> None:
    """Gold's own file (owner's 2026-09-29 figures): Infinox flat wins cheap build, Darwinex's
    % overtakes it once price has risen enough — build and oos2 must show different methods."""
    print("test_xauusd_real_file")
    use = load("XAUUSD")["costs"]["commission"]["use"]
    check("build: Infinox, SizeBased, flat 8.0/lot",
          use["build"] == {"method": "SizeBased", "value": 8.0}, use["build"])
    check("oos2: Darwinex, PercentageBased, 0.005 % of notional",
          use["oos2"] == {"method": "PercentageBased", "value": 0.005}, use["oos2"])
    check("build and oos2 disagree on METHOD, not only on value",
          use["build"]["method"] != use["oos2"]["method"], use)


def test_setup_carries_its_own_segment_method() -> None:
    """A built project's Build task and its retest task must carry DIFFERENT `<Method>`s —
    gold's build is Infinox's SizeBased, its retest (oos1) is Darwinex's PercentageBased —
    reusing test_builder_feedswap.py's temp-install pattern: no real SQX install touched."""
    print("test_setup_carries_its_own_segment_method")
    with tempfile.TemporaryDirectory(prefix="sqx-test-install-") as install:
        builder.worker_dir = lambda role: Path(install)
        done = builder.build(
            name="Test_fixture_commission_segments", template=TEMPLATE, symbol="XAUUSD",
            role="conductor", timeframe="M30", strategies=50, minutes=5, donor=DONOR,
            tasks=("Build", "Retest"))

        with zipfile.ZipFile(Path(done["cfx"])) as z:
            build_xml = z.read("Build-Task3.xml").decode("utf-8")
            retest_xml = z.read("Retest-Task1.xml").decode("utf-8")

        check("Build's Setup has SizeBased switched on",
              '<Method type="SizeBased"' in build_xml and 'use="true"' in
              build_xml[build_xml.index('<Method type="SizeBased"'):][:60])
        check("Build's SizeBased param carries Infinox's flat 8.0",
              'className="SizeBased">8.0' in build_xml, build_xml)
        check("the retest's Setup has PercentageBased switched on, not SizeBased",
              '<Method type="PercentageBased"' in retest_xml and 'use="true"' in
              retest_xml[retest_xml.index('<Method type="PercentageBased"'):][:70])
        check("the retest's PercentageBased param carries Darwinex's 0.005",
              'className="PercentageBased">0.005' in retest_xml, retest_xml)


def main() -> None:
    """Run every known-answer check and exit non-zero if any regressed."""
    test_per_segment_known_answer()
    test_xauusd_real_file()
    test_setup_carries_its_own_segment_method()
    if FAILURES:
        print(f"\ntest_commission_segments: FAILED — {', '.join(FAILURES)}")
        sys.exit(1)
    print("\ntest_commission_segments: ok")


if __name__ == "__main__":
    main()
