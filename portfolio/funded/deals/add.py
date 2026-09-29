"""Put a discount code found somewhere on the books — verified with the firm itself where it can be."""

import argparse
import datetime as dt

from portfolio.funded.catalog import firms
from portfolio.funded.catalog.schema import connect
from portfolio.funded.deals import book, sources


def main() -> None:
    """Hantec codes are checked plan by plan with Hantec's own check; the other firms have none, so theirs stay unverified."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("firm", choices=firms.named(*firms.FOLLOWED))
    parser.add_argument("code")
    parser.add_argument("--source", required=True, help="the URL where the code was found")
    parser.add_argument("--pct", type=float, help="not hantec: the discount the source claims, in %%")
    parser.add_argument("--terms", default="", help="not hantec: the conditions the source states")
    args = parser.parse_args()
    today = dt.date.today().isoformat()
    if args.firm == "hantec":
        rows = sources.hantec_code(args.code, args.source)
        if not rows:
            raise SystemExit(f"{args.code}: Hantec says it is not a valid code today — not recorded")
    else:
        rows = [{"firm": args.firm, "kind": "code", "code": args.code.upper(), "plan_key": "*",
                 "list_price": None, "deal_price": None, "pct": args.pct, "terms": args.terms,
                 "source": args.source, "status": "unverified"}]
    db = connect()
    with db:
        fresh = book.record(db, rows, today)
    print(f"{args.code}: {len(rows)} plan rows, {len(fresh)} new or better")
    for r in rows:
        print(f"  {r['plan_key']:28} {r['list_price']} → {r['deal_price']}  −{r['pct']} %")


if __name__ == "__main__":
    main()
