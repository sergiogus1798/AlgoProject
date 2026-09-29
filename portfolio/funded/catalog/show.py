"""Print a firm's plans, or one plan with chosen add-ons: its price and every rule in force."""

import argparse
import sqlite3

from portfolio.funded.catalog.schema import connect

PLAN_COLS = "plan_key, family, steps, size, price, price_ccy, eas_allowed"
STAGE_COLS = ("stage, profit_target_pct, daily_loss_pct, max_loss_pct, max_loss_mode, min_days, "
              "time_limit_days, consistency_pct, reward_share_pct, payout_days, news_ok, "
              "weekend_ok, filled_from")


def _table(cur: sqlite3.Cursor) -> None:
    """Print a cursor as aligned columns."""
    names = [c[0] for c in cur.description]
    rows = [["" if v is None else str(v) for v in r] for r in cur]
    widths = [max(len(n), *(len(r[i]) for r in rows)) if rows else len(n)
              for i, n in enumerate(names)]
    for line in [names] + rows:
        print("  ".join(v.ljust(w) for v, w in zip(line, widths)))


def firm(db: sqlite3.Connection, name: str) -> None:
    """Every current plan of a firm, with its add-ons and their surcharge."""
    _table(db.execute(f"SELECT {PLAN_COLS}, (SELECT group_concat(option_key || ' +' || "
                      "ifnull(price_pct, '?') || '%', ', ') FROM options o WHERE o.plan_key = "
                      "p.plan_key AND o.valid_to IS NULL) AS addons FROM plans p "
                      "WHERE firm = ? AND valid_to IS NULL ORDER BY family, size", (name,)))


def plan(db: sqlite3.Connection, key: str, chosen: list[str]) -> None:
    """One plan with a set of add-ons: price, the combined rules, each stage, the firm's rules."""
    combo = [r for r in db.execute("SELECT options, price, price_ccy FROM combos WHERE plan_key = ?",
                                   (key,)) if set(filter(None, r[0].split(","))) == set(chosen)]
    options, price, ccy = combo[0]
    print(f"{key}  add-ons: {options or 'none'}  →  {price} {ccy}\n")
    _table(db.execute("SELECT * FROM combos WHERE plan_key = ? AND options = ?", (key, options)))
    print("\nstages before add-ons (filled_from: curated rule, '?' = unconfirmed)")
    _table(db.execute(f"SELECT {STAGE_COLS} FROM stages WHERE plan_key = ? AND valid_to IS NULL",
                      (key,)))
    firm_name, family = key.split(":")[:2]
    print("\nrules")
    _table(db.execute("SELECT rule_key, value, status, text FROM rules WHERE firm = ? AND "
                      "family IN ('*', ?) AND valid_to IS NULL", (firm_name, family)))


def main() -> None:
    """Show a firm's plans or one plan, as the arguments ask."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("what", help="a firm (hantec, ftmo) or a plan key, e.g. hantec:express:25000:USD")
    parser.add_argument("addons", nargs="*", help="add-on keys, e.g. MAX_DRAWDOWN PROFIT_TARGET")
    args = parser.parse_args()
    db = connect()
    if ":" in args.what:
        plan(db, args.what, args.addons)
    else:
        firm(db, args.what)


if __name__ == "__main__":
    main()
