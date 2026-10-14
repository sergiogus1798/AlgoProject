#!/usr/bin/env python3
"""Known-answer test: a feed no project carries gets its resources from SQX's data registry.

`resources.definitions` looks in the source project first and in the registry second
(`registryxml.definitions`, read off the data root's copy of the master's `data.db`). The
fixture database is made here with SQX's own columns and the real rows of `DAX40_M1`.
"""

import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.projects import registryxml, resources, sessiondb

INFO = (
    '<InstrumentInfo instrument="DAX40_ftmo" description="GER40.cash" tickSize="0.01" '
    'tickStep="0.01" minDistance="0.0" tickValueInMoney="0.0" dateFrom="0" dateTo="0" rows="0" '
    'totalDays="0" defaultSpread="100.0" defaultSlippage="1.0" decimals="2" commissions="" '
    'pointValue="1.12948" dataType="4" recognizedFromOrders="false" swap="null" '
    'orderSizeMultiplier="1.0" orderSizeStep="0.01" broker="8" />'
)
SYMBOL = (
    '<Symbol name="DAX40_M1" source="2" barType="1" precision="M1" timezone="EETUS" '
    'dateFrom="1380564780000" dateTo="1790823480000" uSymbol="DEUIDXEUR" '
    'uSymbolName="Germany 30 Index" removeWeekends="false" broker="8">\n        '
    + INFO
    + "\n      </Symbol>"
)
BROKER = (
    '<Broker id="8" name="[[FTMO]]" description="FTMO" timezone="EETUS" postfix="_ftmo" '
    'mtUse="true" spUse="false" />'
)
MINE = (
    '<Symbol name="DAX40_M1" broker="3"><InstrumentInfo instrument="X" /></Symbol>',
    '<InstrumentInfo instrument="X" />',
    '<Broker id="3" />',
)

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    """Record one assertion without stopping the run, so one failure doesn't hide the rest."""
    if ok:
        print(f"  ok  {label}")
    else:
        print(f"  FAIL {label}" + (f" — {detail}" if detail else ""))
        FAILURES.append(label)


def fixture_db(folder: Path) -> Path:
    """A registry with SQX's own three tables and the rows of DAX40_M1, its instrument and FTMO."""
    db = folder / "data.db"
    con = sqlite3.connect(db)
    con.execute(
        "CREATE TABLE DATA (ID INTEGER PRIMARY KEY, SYMBOL, INSTRUMENT, TIMEFRAME, "
        "TIMEZONE, DATEFROM, DATETO, DATATYPE, SOURCE, USYMBOL, USYMBOLNAME, "
        "REMOVE_WEEKENDS, BROKER_ID)"
    )
    con.execute(
        "INSERT INTO DATA VALUES (384, 'DAX40_M1', 'DAX40_ftmo', 'M1', 'EETUS', "
        "1380564780000, 1790823480000, 1, 2, 'DEUIDXEUR', 'Germany 30 Index', 0, 8)"
    )
    con.execute(
        "CREATE TABLE INSTRUMENTS (INSTRUMENT, DESCRIPTION, POINTVALUE, TICKSIZE, TICKSTEP, "
        "DEFAULTSPREAD, COMMISSIONS, DATATYPE, EXCHANGE, COUNTRY, SECTOR, DEFAULTSLIPPAGE, "
        "SWAP, ORDERSIZEMULTIPLIER, ORDERSIZESTEP, BROKER_ID, MIN_DISTANCE)"
    )
    con.execute(
        "INSERT INTO INSTRUMENTS VALUES ('DAX40_ftmo', 'GER40.cash', 1.12948, 0.01, 0.01, "
        "100.0, '', 4, NULL, NULL, NULL, 1.0, NULL, 1.0, 0.01, 8, 0.0)"
    )
    con.execute(
        "CREATE TABLE BROKER (ID, NAME, SYSTEM, DESC, STOCKPICKER_USE, MT_USE, "
        "MT_TIMEZONE, POSTFIX)"
    )
    con.execute(
        "INSERT INTO BROKER VALUES (8, '[[FTMO]]', 1, 'FTMO', 0, 1, 'EETUS', '_ftmo')"
    )
    con.commit()
    con.close()
    return db


def project(folder: Path, date_to: int, timezone: str = "EETUS") -> Path:
    """A one-task project trading DAX40_M1 up to `date_to` (epoch ms), plus a task switched off."""
    task = (
        "<Task><Resources><Symbols>"
        + SYMBOL.replace('dateTo="1790823480000"', f'dateTo="{date_to}"').replace(
            'timezone="EETUS"', f'timezone="{timezone}"'
        )
        + f"</Symbols><Instruments>{INFO}</Instruments><Sessions></Sessions></Resources></Task>"
    )
    cfx = folder / f"p{date_to}{timezone}.cfx"
    with zipfile.ZipFile(cfx, "w") as z:
        z.writestr(
            "config.xml",
            '<Project><Tasks><Task active="true" taskXMLFile="A.xml" />'
            '<Task active="false" taskXMLFile="B.xml" /></Tasks></Project>',
        )
        z.writestr("A.xml", task)
        z.writestr("B.xml", task.replace('timezone="', 'timezone="X'))
    return cfx


def check_unresolved(folder: Path) -> None:
    """`registryxml.unresolved`: the 2026-10-03 XAUUSD refusal — a window ending on the feed's last day."""
    last = 1790823480000  # DAX40_M1's last bar, 2026-10-01 02:58
    midnight_before, midnight_after = 1790812800000, 1790899200000
    check(
        "a range ending the midnight before the last bar resolves",
        registryxml.unresolved(project(folder, midnight_before), active_only=True)
        == [],
    )
    got = registryxml.unresolved(project(folder, midnight_after), active_only=True)
    check(
        "a range ending the midnight AFTER the last bar is unresolved",
        len(got) == 1 and "A.xml: DAX40_M1 range" in got[0] and str(last) in got[0],
        str(got),
    )
    check(
        "another timezone is unresolved",
        any(
            "timezone EET /" in g
            for g in registryxml.unresolved(
                project(folder, midnight_before, "EET"), active_only=True
            )
        ),
    )
    check(
        "a task switched off is read by default (SQX checks every task), skipped when asked",
        any(
            g.startswith("B.xml")
            for g in registryxml.unresolved(project(folder, midnight_before))
        ),
    )


def main() -> None:
    """Run every known-answer check and exit non-zero if any found a regression."""
    with tempfile.TemporaryDirectory(prefix="sqx-test-feeddb-") as tmp:
        db = fixture_db(Path(tmp))
        sessiondb.copy = lambda: db

        got = registryxml.definitions("DAX40_M1")
        check(
            "the <Symbol> block is the registry's row", got[0] == SYMBOL, repr(got[0])
        )
        check("its <InstrumentInfo>", got[1] == INFO, repr(got[1]))
        check("its <Broker>", got[2] == BROKER, repr(got[2]))
        check(
            "refresh() leaves a registry-written block untouched",
            registryxml.refresh(SYMBOL) == SYMBOL,
        )
        check(
            "a feed the registry lacks is None, not invented",
            registryxml.definitions("NOPE_M1") is None,
        )

        check(
            "no project at all: built from the registry",
            resources.definitions(None, "DAX40_M1") == (SYMBOL, INFO, BROKER),
        )
        source = Path(tmp) / "project.cfx"
        with zipfile.ZipFile(source, "w") as z:
            z.writestr("Build-Task1.xml", "<Task>" + "".join(MINE) + "</Task>")
        check(
            "a project that carries the feed wins over the registry",
            resources.definitions(source, "DAX40_M1") == MINE,
        )
        with zipfile.ZipFile(source, "w") as z:
            z.writestr("Build-Task1.xml", "<Task/>")
        check(
            "a project without it falls back to the registry",
            resources.definitions(source, "DAX40_M1") == (SYMBOL, INFO, BROKER),
        )
        check_unresolved(Path(tmp))
        try:
            resources.definitions(source, "NOPE_M1")
            check("in neither: refused, naming the feed", False, "no SystemExit")
        except SystemExit as e:
            check(
                "in neither: refused, naming the feed", "FEED NOPE_M1" in str(e), str(e)
            )

    if FAILURES:
        print(f"\ntest_feed_from_db: FAILED — {', '.join(FAILURES)}")
        sys.exit(1)
    print("\ntest_feed_from_db: ok")


if __name__ == "__main__":
    main()
