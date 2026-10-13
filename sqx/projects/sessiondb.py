"""Build a task's <Session> block from SQX's Data Manager database, read through a copy."""

import os
import shutil
import sqlite3
from pathlib import Path

from core.datapaths import cache_dir
from core.paths import MASTER

SOURCE = MASTER / "user/data/data.db"
DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")   # ELEMENTS stores 1..7, Monday first
# A task XML as SQX writes it: CRLF, the elements eight spaces in, the closing tag six.
ELEMENT = '        <Element dayFrom="{}" dayTo="{}" timeFrom="{}" timeTo="{}" eod="{}" />\r\n'


def copy() -> Path:
    """The data root's copy of the master's `data.db`, refreshed when the master's is newer or another size.

    Returns:
        Path of the copy. The master's GUI holds the original open, so nothing here opens
        it: the file is copied — never written — and only the copy is queried.
    """
    out = cache_dir("sessions") / "data.db"
    src = SOURCE.stat()
    if not out.exists() or out.stat().st_mtime < src.st_mtime or out.stat().st_size != src.st_size:
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_name(f".{out.name}.{os.getpid()}.tmp")
        shutil.copy2(SOURCE, tmp)      # a cut copy stays under its own name, never as the cache
        os.replace(tmp, out)
    return out


def block(session: str, db: Path) -> str | None:
    """One session's definition as a task carries it, from the hours SQX itself stores.

    Args:
        session: Session name, e.g. "EURUSD_ftmo".
        db: A copy of an install's `user/data/data.db`.

    Returns:
        The <Session>…</Session> element, or None when the database has no such session.
        ELEMENTS keeps a time as the integer HHMM (105 is 01:05).
    """
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as con:
        rows = con.execute("SELECT DAYFROM, TIMEFROM, DAYTO, TIMETO, EOD FROM ELEMENTS "
                           "WHERE SESSION = ? ORDER BY ID", (session,)).fetchall()
    if not rows:
        return None
    return (f'<Session name="{session}">\r\n' + "".join(
        ELEMENT.format(DAYS[d0 - 1], DAYS[d1 - 1], f"{t0 // 100:02d}:{t0 % 100:02d}",
                       f"{t1 // 100:02d}:{t1 % 100:02d}", "true" if eod else "false")
        for d0, t0, d1, t1, eod in rows) + "      </Session>")
