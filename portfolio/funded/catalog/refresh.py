"""Re-read every firm's site and rules file into the funding database and print what changed."""

import argparse
import csv
import datetime as dt
import hashlib
import json
import sqlite3

from core.datapaths import funding_dir
from portfolio.funded.catalog import combos, firms, ftmo, fundednext, hantec, manual, overlay, store
from portfolio.funded.catalog.schema import connect

# A firm whose register entry says `catalogue: manual` has no adapter: `manual.py` reads its typed file.
ADAPTERS = {"hantec": hantec, "ftmo": ftmo, "fundednext": fundednext}
# The current picture as CSV for a spreadsheet; the database stays the source of truth.
EXPORTS = {
    "combos": "SELECT * FROM combos ORDER BY firm, family, size, price",
    "plans": "SELECT * FROM plans WHERE valid_to IS NULL ORDER BY firm, family, size",
    "rules": "SELECT * FROM rules WHERE valid_to IS NULL ORDER BY firm, family, rule_key",
    "changes": "SELECT * FROM changes ORDER BY detected_on DESC, tbl, key",
}


def _snapshot(db: sqlite3.Connection, firm: str, source: str, raw: dict, plans: int, today: str) -> str:
    """Keep the raw catalogue when it differs from the last one kept; always log the fetch."""
    text = json.dumps(raw, indent=1, ensure_ascii=False, sort_keys=True, default=str)  # typed files carry dates
    sha = hashlib.sha256(text.encode()).hexdigest()
    last = db.execute("SELECT sha256, raw_path FROM snapshots WHERE firm = ? "
                      "ORDER BY rowid DESC LIMIT 1", (firm,)).fetchone()
    path = last[1] if last and last[0] == sha else None
    if path is None:
        target = funding_dir() / "catalogs" / firm / f"{today}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        path = str(target.relative_to(funding_dir()))
    db.execute("INSERT INTO snapshots VALUES (?, ?, ?, ?, ?, ?)",
               (firm, today, source, path, sha, plans))
    return "new catalogue" if last is None or last[0] != sha else "catalogue unchanged"


def refresh(firm: str, today: str) -> dict:
    """Fetch, normalise, overlay the rules, store with history, rebuild the combinations."""
    if firm in ADAPTERS:
        raw, source = ADAPTERS[firm].fetch(), ADAPTERS[firm].SOURCE
        rows = ADAPTERS[firm].normalise(raw)
    else:
        raw = manual.fetch(firm)
        source, rows = raw["source"], manual.normalise(raw, firm)
    rules = overlay.load(firm)
    overlay.apply(rows, rules)
    db = connect()
    with db:
        note = _snapshot(db, firm, source, raw, len(rows["plans"]), today)
        log = [line for table in ("plans", "stages", "options")
               for line in store.write(db, table, firm, rows[table], today)]
        log += store.write(db, "rules", firm, overlay.compendium(firm, rules), today)
        every = combos.build(rows)
        store.write_combos(db, firm, every)
    return {"firm": firm, "note": note, "plans": len(rows["plans"]), "combos": len(every),
            "changes": log, "unmodelled": sorted(combos.unmodelled(rows)),
            "open": [r for r in rules if r["value"] is None or r["status"] != "confirmed"]}


def export_csv() -> None:
    """Rewrite `AlgoData/funding/csv/<table>.csv` from the database, one file per `EXPORTS` entry."""
    folder = funding_dir() / "csv"
    folder.mkdir(exist_ok=True)
    db = connect()
    for name, sql in EXPORTS.items():
        cur = db.execute(sql)
        with open(folder / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
            out = csv.writer(f)
            out.writerow(c[0] for c in cur.description)
            out.writerows(cur)


def main() -> None:
    """Refresh the firms named, or all, and print each one's changes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("firms", nargs="*", default=firms.named(*firms.FOLLOWED),
                        help="default: every active or candidate firm of the register")
    args = parser.parse_args()
    today = dt.date.today().isoformat()
    for firm in args.firms:
        r = refresh(firm, today)
        print(f"== {firm}: {r['plans']} plans, {r['combos']} combinations, {r['note']}, "
              f"{len(r['changes'])} changes")
        for day, table, key, field, old, new in r["changes"][:200]:
            print(f"  {table:7} {key:40} {field:18} {old} → {new}")
        if len(r["changes"]) > 200:
            print(f"  … {len(r['changes']) - 200} more in the `changes` table")
        for key in r["unmodelled"]:
            print(f"  UNMODELLED add-on {key}: priced, but its effect is not in combos.EFFECTS")
        print(f"  {len(r['open'])} rules unknown, unconfirmed or in conflict")
    export_csv()
    print(f"CSV rewritten in {funding_dir() / 'csv'}")


if __name__ == "__main__":
    main()
