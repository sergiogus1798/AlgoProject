"""Look at every place a firm shows offers, record what is on today, expire what is gone."""

import datetime as dt

from portfolio.funded.catalog.schema import connect
from portfolio.funded.deals import book, sources


def scan(today: str) -> list[dict]:
    """FTMO's table, FundedNext's sale prices, Hantec's banner, and every Hantec code on the books, re-checked.

    Everything is fetched first and written in one short transaction: the code checks are dozens
    of requests, and the database must not stay locked while they run.
    """
    db = connect()
    codes = db.execute("SELECT DISTINCT code, source FROM deals WHERE firm = 'hantec' AND "
                       "kind = 'code' AND status = 'valid'").fetchall()
    ftmo, banners, fnext = sources.ftmo_table(), sources.hantec_banners(), sources.fundednext_table()
    checked = {code: sources.hantec_code(code, source) for code, source in codes}
    fresh = []
    with db:
        fresh += book.record(db, ftmo, today)
        book.expire(db, "ftmo", "table", ftmo, today)
        fresh += book.record(db, fnext, today)
        book.expire(db, "fundednext", "table", fnext, today)
        fresh += book.record(db, banners, today)
        book.expire(db, "hantec", "banner", banners, today)
        for code, rows in checked.items():
            fresh += book.record(db, rows, today)
            book.expire(db, "hantec", "code", rows, today, code=code)
    return fresh


def main() -> None:
    """Scan and print what is new or better."""
    fresh = scan(dt.date.today().isoformat())
    print(f"{len(fresh)} deal rows new or better today")
    for r in fresh:
        print(f"  {r['firm']:7} {r['kind']:6} {r['code'] or '-':12} {r['plan_key']:28} "
              f"{r['list_price']} → {r['deal_price']}  −{r['pct']} %  {r['terms'][:60]}")


if __name__ == "__main__":
    main()
