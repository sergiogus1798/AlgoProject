"""Tell the owner, with a desktop notification, about every deal in his universe he has not heard of yet."""

import datetime as dt
import subprocess

from portfolio.funded.catalog.schema import connect
from portfolio.funded.deals import book


def pending() -> tuple[dict[tuple, list[tuple]], list[int]]:
    """Unnotified live deals that touch the universe, grouped by (firm, kind, code).

    A deal notifies only if it is the cheapest live price of at least one universe plan, or it
    names no price (a banner, an unverified code). The rest are beaten by a deal the owner already
    knows: they are returned apart, to be stamped without a notification.
    """
    db = connect()
    plans = book.universe(db)
    best = dict(db.execute("SELECT plan_key, min(deal_price) FROM deals WHERE status = 'valid' AND "
                           "deal_price IS NOT NULL GROUP BY plan_key"))
    rows = db.execute("SELECT deal_id, firm, kind, code, plan_key, list_price, deal_price, pct, terms, "
                      "status FROM deals WHERE status IN ('valid', 'unverified') AND notified_on IS NULL "
                      "ORDER BY firm, kind, code, deal_price").fetchall()
    groups = {}
    for r in rows:
        if r[4] in plans or r[4] == "*":
            groups.setdefault(r[1:4], []).append(r)
    beaten = [r[0] for rows in groups.values()
              if not any(r[6] is None or r[6] <= best[r[4]] for r in rows) for r in rows]
    return {k: v for k, v in groups.items() if not {r[0] for r in v} <= set(beaten)}, beaten


def message(key: tuple, rows: list[tuple]) -> tuple[str, str]:
    """Title and body of one notification."""
    firm, kind, code = key
    pct = max(r[7] or 0 for r in rows)
    what = code or {"table": "precio rebajado", "banner": "banner"}[kind]
    unverified = " (sin verificar)" if rows[0][9] == "unverified" else ""
    title = f"Oferta de fondeo: {firm} {what} −{pct:g} %{unverified}"
    biggest = sorted((r for r in rows if r[6] is not None), key=lambda r: -float(r[4].split(":")[2]))
    lines = [f"{r[4].split(':')[1]} {int(float(r[4].split(':')[2])) // 1000}k: {r[5]:g} → {r[6]:g}"
             for r in biggest][:5]
    lines = lines or [rows[0][8][:120]]
    lines.append(f"¿Merece la pena? python3 -m portfolio.funded.deals.worth {rows[0][0]}")
    return title, "\n".join(lines)


def main() -> None:
    """Send one notification per deal and stamp its rows, so it is not sent again."""
    groups, beaten = pending()
    db = connect()
    today = dt.date.today().isoformat()
    with db:
        db.executemany("UPDATE deals SET notified_on = ? WHERE deal_id = ?", [(today, b) for b in beaten])
    for key, rows in groups.items():
        title, body = message(key, rows)
        subprocess.run(["notify-send", "--app-name=AlgoProject", "--urgency=critical", title, body],
                       check=True)
        print(f"{title}\n{body}\n")
        with db:
            db.executemany("UPDATE deals SET notified_on = ? WHERE deal_id = ?",
                           [(today, r[0]) for r in rows])
    print(f"{len(groups)} notifications sent, {len(beaten)} deal rows beaten by a better known deal")


if __name__ == "__main__":
    main()
