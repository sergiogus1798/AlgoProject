"""Is a deal worth it? Every universe plan priced per $1,000 of funded account at the zero-edge floor, with and without today's deals.

Provisional: the floor is what a funded account costs when the strategy has no edge (barrier
geometry, P(+a before −b) = b/(a+b) per phase), per $1,000 of its size because payouts scale with
size, net of the passing account's fee when the firm refunds it. The expected value with the owner's
strategies is encargo 33's.
"""

import argparse
import re
import sqlite3
import urllib.request

from portfolio.funded.catalog.schema import connect
from portfolio.funded.deals import book

ECB = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"


def eurusd() -> float:
    """Today's ECB reference rate, so FTMO's euro prices rank against Hantec's dollars."""
    xml = urllib.request.urlopen(ECB, timeout=30).read().decode()
    return float(re.search(r"currency='USD' rate='([\d.]+)'", xml).group(1))


def floor(db: sqlite3.Connection, plan_key: str) -> tuple[float | None, bool]:
    """P(pass every phase) with no edge, and whether a trailing loss makes it an upper bound."""
    phases = db.execute("SELECT profit_target_pct, max_loss_pct, max_loss_mode FROM stages WHERE "
                        "plan_key = ? AND valid_to IS NULL AND stage != 'funded'", (plan_key,)).fetchall()
    if any(a is None or b is None for a, b, _ in phases):
        return None, False
    p = 1.0
    for a, b, _ in phases:
        p *= b / (a + b)
    return p, any(mode != "static" for _, _, mode in phases)


def refunded(db: sqlite3.Connection, firm: str, family: str) -> str:
    """'yes', 'no' or '?' from the rules compendium's fee_refund."""
    row = db.execute("SELECT value FROM rules WHERE firm = ? AND family IN (?, '*') AND "
                     "rule_key = 'fee_refund' AND valid_to IS NULL ORDER BY family = '*'",
                     (firm, family)).fetchone()
    return {"True": "yes", "False": "no"}.get(row[0] if row else None, "?")


def _per_k(price: float, prob: float | None, size: float, refund: str) -> float | None:
    """Expected fees per funded account, net of its own refunded fee, per $1,000 of account."""
    if not prob:
        return None
    return (price / prob - (price if refund == "yes" else 0)) * 1000 / size


def board(db: sqlite3.Connection, rate: float) -> list[dict]:
    """One row per universe plan: list and best current price in USD, the floor, cost per funded $1,000."""
    rows = []
    for key, p in book.universe(db).items():
        fx = rate if p["price_ccy"] == "EUR" else 1.0
        deal = db.execute("SELECT deal_price, deal_id FROM deals WHERE plan_key = ? AND status = 'valid' "
                          "AND deal_price IS NOT NULL ORDER BY deal_price LIMIT 1", (key,)).fetchone()
        now = deal[0] if deal else p["price"]
        prob, bound = floor(db, key)
        refund = refunded(db, p["firm"], p["family"])
        rows.append({"plan": key, "list": p["price"] * fx, "now": now * fx,
                     "deal_id": deal[1] if deal else None, "p": prob, "bound": bound, "refund": refund,
                     "per_pass_list": _per_k(p["price"] * fx, prob, p["size"], refund),
                     "per_pass_now": _per_k(now * fx, prob, p["size"], refund)})
    return rows


def _money(value: float | None) -> str:
    """A cost for the table, '?' when the floor is unknown."""
    return f"{value:,.1f}" if value else "?"


def _rank(rows: list[dict], field: str) -> dict[str, int]:
    """Position of each plan when sorted by a cost, cheapest first; plans without it go last."""
    order = sorted(rows, key=lambda r: (r[field] is None, r[field] or 0))
    return {r["plan"]: i + 1 for i, r in enumerate(order)}


def main() -> None:
    """Print the board, and for one deal how far it moves its plans."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("deal_id", nargs="?", type=int, help="the id the notification gives")
    args = parser.parse_args()
    db = connect()
    rows = board(db, eurusd())
    before, after = _rank(rows, "per_pass_list"), _rank(rows, "per_pass_now")
    print(f"{'plan':28} {'lista $':>8} {'hoy $':>8} {'P suelo':>8} {'$/k lista':>10} "
          f"{'$/k hoy':>8} {'puesto':>8}  reembolso")
    for r in sorted(rows, key=lambda r: after[r["plan"]]):
        prob = f"{'≤' if r['bound'] else ''}{r['p']:.0%}" if r["p"] else "?"
        print(f"{r['plan']:28} {r['list']:8.2f} {r['now']:8.2f} {prob:>8} {_money(r['per_pass_list']):>10} "
              f"{_money(r['per_pass_now']):>8} {before[r['plan']]:>3} → {after[r['plan']]:<3} {r['refund']}")
    if args.deal_id:
        firm, kind, code = db.execute("SELECT firm, kind, code FROM deals WHERE deal_id = ?",
                                      (args.deal_id,)).fetchone()
        touched = {k for (k,) in db.execute("SELECT plan_key FROM deals WHERE firm = ? AND kind = ? AND "
                                            "code = ? AND status = 'valid'", (firm, kind, code))}
        print(f"\nOferta {args.deal_id} ({firm} {code or kind}):")
        for r in rows:
            if r["plan"] in touched and r["per_pass_now"]:
                print(f"  {r['plan']}: ahorra {r['list'] - r['now']:.2f} $ por intento y "
                      f"{r['per_pass_list'] - r['per_pass_now']:,.1f} $ por cada 1.000 $ de cuenta aprobada sin edge; "
                      f"puesto {before[r['plan']]} → {after[r['plan']]} de {len(rows)}")
    print("\n$/k = cuotas esperadas por cada 1.000 $ de cuenta aprobada si la estrategia no tuviera edge, "
          "netas del reembolso de la cuota de la cuenta que aprueba (sólo si la empresa lo da y llega el "
          "primer cobro). Barreras sin límite diario ni costes; ≤ = trailing, peor aún. Un edge real lo "
          "baja. El veredicto con tus estrategias es el VE del encargo 33, aún por construir.")


if __name__ == "__main__":
    main()
