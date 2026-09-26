"""The clock a feed's bars and trades are stamped in, as SQX's own data registry declares it."""

import sqlite3

from core.paths import MASTER

REGISTRY = MASTER / "user" / "data" / "data.db"


def timezone(feed: str) -> str:
    """The IANA zone SQX stamps one feed's bars in — its trades' times are in the same clock.

    Args:
        feed: The feed name, e.g. "USDJPY_DukasM1_the5ers".

    Returns:
        The zone as the registry spells it, e.g. "EET" or "Asia/Jerusalem". Read-only: the
        registry is opened with `mode=ro`, so a running master is never written to.
    """
    with sqlite3.connect(f"file:{REGISTRY}?mode=ro", uri=True) as db:
        row = db.execute("SELECT TIMEZONE FROM DATA WHERE SYMBOL = ?", (feed,)).fetchone()
    return row[0]
