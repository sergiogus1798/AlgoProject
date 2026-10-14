#!/usr/bin/env python3
"""Known-answer test: a session no project defines is built from SQX's Data Manager database.

`doctrine.borrow_session` looks in the source project first and in the database second
(`sqx.projects.sessiondb`, `knowhow/costs/sessions-live-in-data-db.md`). The fixture database
is made here with the real schema and the real five rows of `XAUUSD_ftmo`; the block that comes
out must be the one the master's own `XAUUSD/project.cfx` carries, byte for byte.
"""

import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.projects import doctrine, sessiondb

KNOWN = (
    '<Session name="XAUUSD_ftmo">\r\n'
    + "".join(
        f'        <Element dayFrom="{d}" dayTo="{d}" timeFrom="01:05" timeTo="23:50" eod="true" />\r\n'
        for d in ("Mon", "Tue", "Wed", "Thu", "Fri")
    )
    + "      </Session>"
)
TASK = "<Task><Resources><Sessions>{}</Sessions></Resources></Task>"
OTHER = '<Session name="OTHER_x"><Element dayFrom="Mon" /></Session>'

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    """Record one assertion without stopping the run, so one failure doesn't hide the rest."""
    if ok:
        print(f"  ok  {label}")
    else:
        print(f"  FAIL {label}" + (f" — {detail}" if detail else ""))
        FAILURES.append(label)


def fixture_db(folder: Path) -> Path:
    """A database with SQX's own two tables and the rows of XAUUSD_ftmo, HHMM as integers."""
    db = folder / "data.db"
    con = sqlite3.connect(db)
    con.execute(
        "CREATE TABLE SESSIONS (SESSION VARCHAR(50) PRIMARY KEY NOT NULL, "
        "BROKER_ID INT DEFAULT -1)"
    )
    con.execute(
        "CREATE TABLE ELEMENTS (ID INTEGER PRIMARY KEY AUTOINCREMENT, SESSION VARCHAR(50) "
        "NOT NULL, DAYFROM INTEGER NOT NULL, TIMEFROM INTEGER NOT NULL, DAYTO INTEGER "
        "NOT NULL, TIMETO INTEGER NOT NULL, EOD BOOLEAN NOT NULL)"
    )
    con.execute("INSERT INTO SESSIONS VALUES ('XAUUSD_ftmo', 8)")
    con.executemany(
        "INSERT INTO ELEMENTS (SESSION, DAYFROM, TIMEFROM, DAYTO, TIMETO, EOD) "
        "VALUES ('XAUUSD_ftmo', ?, 105, ?, 2350, 1)",
        [(d, d) for d in range(1, 6)],
    )
    con.commit()
    con.close()
    return db


def main() -> None:
    """Run every known-answer check and exit non-zero if any found a regression."""
    with tempfile.TemporaryDirectory(prefix="sqx-test-sessiondb-") as tmp:
        db = fixture_db(Path(tmp))
        check(
            "the block equals the one the master's project carries",
            sessiondb.block("XAUUSD_ftmo", db) == KNOWN,
            repr(sessiondb.block("XAUUSD_ftmo", db)),
        )
        check(
            "a session the database lacks is None, not invented",
            sessiondb.block("NOPE_ftmo", db) is None,
        )

        source = Path(tmp) / "project.cfx"
        with zipfile.ZipFile(source, "w") as z:
            z.writestr("config.xml", "<Project/>")
            z.writestr("Build-Task1.xml", TASK.format(OTHER))
        sessiondb.copy = lambda: db

        members = {
            "config.xml": b"<Project/>",
            "Build-Task1.xml": TASK.format(OTHER).encode(),
        }
        target = doctrine.borrow_session(members, "XAUUSD_ftmo", source)
        text = members[target].decode()
        check("absent from every project: built from the database", KNOWN in text)
        check(
            "exactly one definition added, the task's own kept",
            text.count("<Session ") == 2 and OTHER in text,
        )

        mine = '<Session name="XAUUSD_ftmo"><Element dayFrom="Sun" /></Session>'
        with zipfile.ZipFile(source, "w") as z:
            z.writestr("Build-Task1.xml", TASK.format(mine))
        members = {"Build-Task1.xml": TASK.format(OTHER).encode()}
        doctrine.borrow_session(members, "XAUUSD_ftmo", source)
        check(
            "a project that defines it wins over the database",
            mine in members["Build-Task1.xml"].decode(),
        )

        members = {"Build-Task1.xml": TASK.format(OTHER).encode()}
        try:
            doctrine.borrow_session(members, "NOPE_ftmo", source)
            check("in neither: refused", False, "no SystemExit")
        except SystemExit:
            check("in neither: refused", True)

    if FAILURES:
        print(f"\ntest_session_from_db: FAILED — {', '.join(FAILURES)}")
        sys.exit(1)
    print("\ntest_session_from_db: ok")


if __name__ == "__main__":
    main()
