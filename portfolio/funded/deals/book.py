"""The deals table: record what was seen today, expire what was not, and the universe the owner buys from."""

import sqlite3

from portfolio.funded.catalog import firms

COLS = ("firm", "kind", "code", "plan_key", "list_price", "deal_price", "pct", "terms", "source",
        "status")
# What the owner buys today (2026-09-29): accounts of 10k at most, in USD, where EAs are allowed,
# of the firms the register marks active (a candidate is followed but not bought from).
UNIVERSE_SQL = ("SELECT plan_key, firm, family, size, price, price_ccy FROM plans WHERE valid_to IS NULL "
                "AND size <= 10000 AND account_ccy = 'USD' AND eas_allowed = 1")


def universe(db: sqlite3.Connection) -> dict[str, dict]:
    """The plans in the owner's buying universe, by plan key."""
    cur = db.execute(UNIVERSE_SQL)
    names = [c[0] for c in cur.description]
    active = set(firms.named("active"))
    return {r[0]: dict(zip(names, r)) for r in cur if r[1] in active}


def record(db: sqlite3.Connection, rows: list[dict], today: str) -> list[dict]:
    """Insert new deals and refresh the ones seen again. A deal whose price dropped again counts as new.

    Returns:
        The rows that are new or better than before — the ones worth a notification.
    """
    fresh = []
    for r in rows:
        old = db.execute("SELECT deal_price, pct, status FROM deals WHERE firm = ? AND kind = ? AND "
                         "code = ? AND plan_key = ?",
                         (r["firm"], r["kind"], r["code"], r["plan_key"])).fetchone()
        if old is None:
            db.execute(f"INSERT INTO deals ({', '.join(COLS)}, first_seen, last_seen) "
                       f"VALUES ({', '.join('?' * len(COLS))}, ?, ?)",
                       (*(r[c] for c in COLS), today, today))
            fresh.append(r)
            continue
        better = old[2] != "valid" or (r["pct"] or 0) > (old[1] or 0)
        db.execute("UPDATE deals SET list_price = ?, deal_price = ?, pct = ?, terms = ?, status = ?, "
                   "last_seen = ?" + (", notified_on = NULL" if better else "") +
                   " WHERE firm = ? AND kind = ? AND code = ? AND plan_key = ?",
                   (r["list_price"], r["deal_price"], r["pct"], r["terms"], r["status"], today,
                    r["firm"], r["kind"], r["code"], r["plan_key"]))
        if better:
            fresh.append(r)
    return fresh


def expire(db: sqlite3.Connection, firm: str, kind: str, seen: list[dict], today: str,
           code: str | None = None) -> int:
    """Mark as expired every valid deal of this firm and kind (and code) that today's look did not find."""
    keys = {(r["code"], r["plan_key"]) for r in seen}
    rows = db.execute("SELECT deal_id, code, plan_key FROM deals WHERE firm = ? AND kind = ? AND "
                      "status = 'valid'" + (" AND code = ?" if code else ""),
                      (firm, kind, code) if code else (firm, kind)).fetchall()
    gone = [r[0] for r in rows if (r[1], r[2]) not in keys]
    db.executemany("UPDATE deals SET status = 'expired', last_seen = ? WHERE deal_id = ?",
                   [(today, g) for g in gone])
    return len(gone)
