#!/usr/bin/env python3
"""Known-answer test for the builder's scope rule (owner, 2026-09-29): from the master, a new
project may take ONLY bar data, instrument definitions and trading sessions — never any task
configuration (costs, acceptance, exits, databanks, task XML).

`sqx.projects.resources.definitions()` borrows exactly `<Symbol>`, `<InstrumentInfo>` and
`<Broker>`; `sqx.projects.doctrine.borrow_session()` borrows exactly one `<Session>`. Neither
touches a `<Setup>`, a `<Task>`, a `<Databank>` or an acceptance/exit block. The master's
`<InstrumentInfo>` DOES carry an embedded cost blob (defaultSpread, commissions, swap — SQX's own
identity fields, `knowhow/costs/per-task-costs.md`), so the proof that matters is not "the text
never appears" but "the text never governs a backtest": every `<Setup>` of the FINISHED project
must carry `assets/`'s own declared costs, not the master's.
"""

import re
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.assetdata import load
from core.datapaths import projects_backup
from core.paths import MASTER
from sqx.projects import builder, doctrine, resources

TEMPLATE = (Path(__file__).resolve().parent.parent / "tools/sqx-lab/plugins/sqx-lab/skills/"
            "sqx-strategy-template/engine/skeletons/market_skeleton.sqx")
DONOR = projects_backup("XAUUSD_base_2026-09-21") / "project.cfx"
USDJPY_SOURCE = MASTER / "user/projects/USDJPY/project.cfx"

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    """Record one assertion without stopping the run, so one failure doesn't hide the rest."""
    if ok:
        print(f"  ok  {label}")
    else:
        print(f"  FAIL {label}" + (f" — {detail}" if detail else ""))
        FAILURES.append(label)


FORBIDDEN = ("<Setup", "<Task", "<Databank", "<AcceptanceCondition", "<Exit", "<StrategyType")


def test_definitions_scope() -> None:
    """`resources.definitions()` returns only Symbol/InstrumentInfo/Broker — nothing task-shaped."""
    print("test_definitions_scope")
    if not USDJPY_SOURCE.exists():
        print(f"  SKIP — {USDJPY_SOURCE} not on this machine")
        return
    symbol, instrument, broker = resources.definitions(USDJPY_SOURCE, "USDJPY_DukasM1_the5ers")
    check("Symbol block", symbol.startswith("<Symbol"))
    check("InstrumentInfo block", instrument.startswith("<InstrumentInfo"))
    check("Broker block", broker.startswith("<Broker"))
    for name, block in (("Symbol", symbol), ("InstrumentInfo", instrument), ("Broker", broker)):
        hit = next((f for f in FORBIDDEN if f in block), None)
        check(f"{name} carries no task-shaped element", hit is None, hit or "")


def test_session_scope() -> None:
    """`doctrine.borrow_session` copies exactly one `<Session>` element, nothing beside it."""
    print("test_session_scope")
    if not USDJPY_SOURCE.exists():
        print(f"  SKIP — {USDJPY_SOURCE} not on this machine")
        return
    session = load("USDJPY")["session"]
    with zipfile.ZipFile(USDJPY_SOURCE) as z:
        candidates = [doctrine.settings.session_block(z.read(n).decode("utf-8", "replace"), session)
                      for n in z.namelist() if n.endswith(".xml") and n != "config.xml"]
    block = next((b for b in candidates if b), None)
    check("a session block was found on the master", block is not None)
    if block:
        check("Session block only", block.startswith("<Session") and block.endswith("</Session>"))
        hit = next((f for f in FORBIDDEN if f in block), None)
        check("Session carries no task-shaped element", hit is None, hit or "")


def test_finished_setups_carry_assets_costs_not_the_masters() -> None:
    """Even though the borrowed `InstrumentInfo` embeds the master's own cost blob (its
    identity fields, never edited — hard rule 4 territory), every `<Setup>` of the FINISHED
    project must carry `assets/`'s declared costs. If the master's figures ever leaked
    through, this is where they would show up."""
    print("test_finished_setups_carry_assets_costs_not_the_masters")
    if not USDJPY_SOURCE.exists():
        print(f"  SKIP — {USDJPY_SOURCE} not on this machine")
        return
    asset = load("USDJPY")
    with zipfile.ZipFile(USDJPY_SOURCE) as z:
        master_spread = None
        for n in z.namelist():
            if n.endswith(".xml") and n != "config.xml":
                m = re.search(r'defaultSpread="([^"]*)"', z.read(n).decode("utf-8", "replace"))
                if m:
                    master_spread = m.group(0)
                    break
    check("precondition: the master's own spread differs from assets/'s declared one",
          master_spread is not None and 'defaultSpread="0.1"' == master_spread,
          f"master carries {master_spread!r}, expected the known 0.1 fixture value")

    with tempfile.TemporaryDirectory(prefix="sqx-test-install-") as install:
        builder.worker_dir = lambda role: Path(install)
        done = builder.build(
            name="Test_fixture_usdjpy_scope", template=TEMPLATE, symbol="USDJPY",
            role="conductor", timeframe="M30", strategies=50, minutes=5, donor=DONOR,
            session_from=USDJPY_SOURCE)

        with zipfile.ZipFile(done["cfx"]) as z:
            texts = {n: z.read(n).decode("utf-8", "replace") for n in z.namelist()
                     if n.endswith(".xml") and n != "config.xml"}

        setups = [m.group(0) for t in texts.values()
                  for m in re.finditer(r"<Setup\b[^>]*>.*?</Setup>", t, re.S)
                  if f'symbol="{asset["sqx_symbol"]}"' in m.group(0)]
        check("the built project has Setups trading USDJPY", bool(setups))
        wrong = [s for s in setups if f'spread="{asset["costs"]["spread"]["use"]}"' not in s]
        check("every Setup carries assets/'s declared spread, not the master's",
              not wrong, f"{len(wrong)} of {len(setups)} Setups")
        stray_master_spread = [s for s in setups if 'spread="0.1"' in s]
        check("the master's own spread (0.1) never appears in a finished Setup",
              not stray_master_spread, f"{len(stray_master_spread)} Setup(s)")


def main() -> None:
    """Run every known-answer check and exit non-zero if any found a regression."""
    test_definitions_scope()
    test_session_scope()
    test_finished_setups_carry_assets_costs_not_the_masters()
    if FAILURES:
        print(f"\ntest_builder_scope: FAILED — {', '.join(FAILURES)}")
        sys.exit(1)
    print("\ntest_builder_scope: ok")


if __name__ == "__main__":
    main()
