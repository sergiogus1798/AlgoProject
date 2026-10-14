#!/usr/bin/env python3
"""Known-answer test for the commission per segment: an asset with commission confirmed prices
the WHOLE workflow at one method and value, the same in build/oos1/oos2, and a built project's
Setup carries exactly that `use` — and `core.commission.commission_pct` converts
a broker's own $/lot figure into the % `broker_pct()` hands step 26 and `weeklyReconciler`.
"""

import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.assetdata import load
from core.commission import commission_pct
from core.datapaths import projects_backup
from sqx.projects import builder

TEMPLATE = (
    Path(__file__).resolve().parent.parent / "tools/sqx-lab/plugins/sqx-lab/skills/"
    "sqx-strategy-template/engine/skeletons/market_skeleton.sqx"
)
DONOR = projects_backup("XAUUSD_base_2026-09-21") / "project.cfx"

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    """Record one assertion without stopping the run, so one failure doesn't hide the rest."""
    if ok:
        print(f"  ok  {label}")
    else:
        print(f"  FAIL {label}" + (f" — {detail}" if detail else ""))
        FAILURES.append(label)


def test_commission_pct_known_answer() -> None:
    """8 $/lot at a price of 4000 with a 100 contract size is 0.002 % of notional."""
    print("test_commission_pct_known_answer")
    check(
        "SizeBased converts to a percentage of notional",
        round(commission_pct("SizeBased", 8.0, 4000.0, 100.0), 6) == 0.002,
    )
    check(
        "PercentageBased returns its own figure, price and point_value unused",
        commission_pct("PercentageBased", 0.005, None, None) == 0.005,
    )


def test_xauusd_real_file() -> None:
    """Gold's own file: build, oos1 and oos2 carry the same method AND value — one figure for the
    whole workflow, not one broker per segment. Which broker wins is the cost cards' call
    (`assets/_classes.yaml`), so the test reads it instead of pinning it."""
    print("test_xauusd_real_file")
    use = load("XAUUSD")["costs"]["commission"]["use"]
    check(
        "build, oos1 and oos2 agree, method and value both",
        use["build"] == use["oos1"] == use["oos2"],
        use,
    )
    check(
        "the method is one SQX knows",
        use["build"]["method"] in ("SizeBased", "PercentageBased"),
        use["build"],
    )


def test_xauusd_broker_table_has_pct_now() -> None:
    """Every confirmed broker of gold's own table carries a `pct_now` `--refresh` computed."""
    print("test_xauusd_broker_table_has_pct_now")
    brokers = load("XAUUSD")["costs"]["commission"]["brokers"]
    confirmed = {n: b for n, b in brokers.items() if b.get("confirmed")}
    check(
        "every confirmed broker has a pct_now",
        all("pct_now" in b for b in confirmed.values()),
        confirmed,
    )
    check(
        "Darwinex's own pct_now is its own 0.005 % unchanged",
        confirmed["darwinex"]["pct_now"] == 0.005,
        confirmed["darwinex"],
    )
    check(
        "Infinox's SizeBased 8.0/lot converts to a percentage below Darwinex's",
        0 < confirmed["infinox"]["pct_now"] < confirmed["darwinex"]["pct_now"],
        confirmed["infinox"],
    )


def test_setup_carries_the_asset_use() -> None:
    """A built project's Build task and its retest task both carry the asset's `use` — the SAME
    method and value everywhere, reusing
    `test_builder_feedswap.py`'s temp-install pattern (no real SQX install touched)."""
    print("test_setup_carries_the_asset_use")
    want = load("XAUUSD")["costs"]["commission"]["use"]["build"]
    method, value = want["method"], want["value"]
    with tempfile.TemporaryDirectory(prefix="sqx-test-install-") as install:
        builder.worker_dir = lambda role: Path(install)
        done = builder.build(
            name="Test_fixture_commission_segments",
            template=TEMPLATE,
            symbol="XAUUSD",
            role="conductor",
            timeframe="M30",
            strategies=50,
            minutes=5,
            donor=DONOR,
            tasks=("Build", "Retest"),
        )

        with zipfile.ZipFile(Path(done["cfx"])) as z:
            build_xml = z.read("Build-Task3.xml").decode("utf-8")
            retest_xml = z.read("Retest-Task1.xml").decode("utf-8")

        for label, xml in (("Build", build_xml), ("Retest", retest_xml)):
            at = xml.find(f'<Method type="{method}"')
            check(
                f"{label}'s Setup has {method} switched on",
                at >= 0 and 'use="true"' in xml[at:][:70],
            )
            check(
                f"{label}'s {method} param carries {value}",
                f'className="{method}">{value}' in xml,
                xml[at:][:400] if at >= 0 else "",
            )


def main() -> None:
    """Run every known-answer check and exit non-zero if any regressed."""
    test_commission_pct_known_answer()
    test_xauusd_real_file()
    test_xauusd_broker_table_has_pct_now()
    test_setup_carries_the_asset_use()
    if FAILURES:
        print(f"\ntest_commission_segments: FAILED — {', '.join(FAILURES)}")
        sys.exit(1)
    print("\ntest_commission_segments: ok")


if __name__ == "__main__":
    main()
