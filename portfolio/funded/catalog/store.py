"""Write one firm's rows into the versioned tables, logging every added, removed or changed value."""

import sqlite3

from portfolio.funded.catalog.schema import TABLES


def _same(a: object, b: object) -> bool:
    """Equal as stored: 4 and 4.0 are the same number, 1 and True the same flag."""
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) == float(b)
    return a == b


def _current(db: sqlite3.Connection, table: str, firm: str) -> dict[tuple, dict]:
    """The firm's current rows of one table, by natural key."""
    keys, values = TABLES[table]
    where = "firm = ?" if "firm" in keys + values else "plan_key LIKE ?"
    arg = firm if "firm" in keys + values else f"{firm}:%"
    cur = db.execute(f"SELECT {', '.join(keys + values)} FROM {table} "
                     f"WHERE valid_to IS NULL AND {where}", (arg,))
    names = [c[0] for c in cur.description]
    rows = [dict(zip(names, r)) for r in cur]
    return {tuple(r[k] for k in keys): r for r in rows}


def write(db: sqlite3.Connection, table: str, firm: str, rows: list[dict], today: str) -> list[tuple]:
    """Close what changed or vanished, open what is new or changed.

    Returns:
        The change log rows written: (day, table, key, field, old, new). A new row logs field '*'
        with new 'added', a vanished one 'removed'.
    """
    keys, values = TABLES[table]
    old = _current(db, table, firm)
    new = {tuple(r[k] for k in keys): r for r in rows}
    assert len(new) == len(rows), f"{table}: two {firm} rows share a key {keys}"
    log = []
    for key in old.keys() - new.keys():
        log.append((today, table, "|".join(map(str, key)), "*", "present", "removed"))
    for key, row in new.items():
        if key not in old:
            log.append((today, table, "|".join(map(str, key)), "*", None, "added"))
            continue
        diff = [v for v in values if not _same(old[key][v], row[v])]
        log += [(today, table, "|".join(map(str, key)), v, str(old[key][v]), str(row[v]))
                for v in diff]
        if not diff:
            new[key] = None  # unchanged: the open row stays open
    closing = [k for k in old if k not in new or new[k] is not None]
    match = " AND ".join(f"{k} = ?" for k in keys)
    db.executemany(f"UPDATE {table} SET valid_to = ? WHERE valid_to IS NULL AND {match}",
                   [(today, *k) for k in closing])
    cols = keys + values
    db.executemany(f"INSERT INTO {table} ({', '.join(cols)}, valid_from) "
                   f"VALUES ({', '.join('?' * (len(cols) + 1))})",
                   [tuple(r[c] for c in cols) + (today,) for r in new.values() if r is not None])
    db.executemany("INSERT INTO changes VALUES (?, ?, ?, ?, ?, ?)", log)
    return log


def write_combos(db: sqlite3.Connection, firm: str, combos: list[dict]) -> None:
    """Replace the firm's combinations: they are derived, so only the current set is kept."""
    db.execute("DELETE FROM combos WHERE firm = ?", (firm,))
    cols = list(combos[0])
    db.executemany(f"INSERT INTO combos ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                   [tuple(c[k] for k in cols) for c in combos])
