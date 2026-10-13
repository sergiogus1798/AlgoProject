"""One-off: fill `clock` and `commission` into the manifests archived before they were frozen there."""

import argparse
import json
import os
from collections import Counter
from pathlib import Path

from core import paths
from core.archive import manifest, read
from sqx.inspect import feeds

FEEDS_MOVED = "2026-10-01"   # SQX feeds renamed <ASSET>_M1 on EETUS: before it the live zone is not the trades' clock
# Owner 2026-10-13 (Q18): the one old feed whose clock is measured (rebuild vs SQX daily lows, 0.3-3 $
# against 430-2000 $ with EETUS). Not a fallback: any other old feed stays unfilled.
OLD_FEED_CLOCK = {"USDJPY_DukasM1_the5ers": "Asia/Jerusalem"}


def plan(version: Path) -> tuple[dict | None, str]:
    """What one version's manifest would get, or why nothing.

    Returns:
        (fields, ""), or (None, the reason). The commission is the card the member itself froze
        (`asset/card.json`, as of its archive day: exact, no git needed); the clock is the live
        zone of its feed, taken only when the project was created after the feeds moved —
        trades built earlier carry the old broker-suffixed feed's clock, which no file records.
    """
    doc = json.loads((version / "manifest.json").read_text(encoding="utf-8"))
    if "clock" in doc and "commission" in doc:
        return None, "ya congelado"
    use = json.loads((version / "asset" / "card.json").read_text(encoding="utf-8"))["costs"]["commission"]["use"]
    if not isinstance(use, dict):
        return None, f"comisión de la ficha sin tramos ({use!r}): formato anterior a 2026-09-29"
    feed = manifest.feed_of(version / "strategy.sqx")
    if doc["registry"]["created"][:10] < FEEDS_MOVED:
        if feed not in OLD_FEED_CLOCK:
            return None, f"proyecto creado {doc['registry']['created'][:10]}: reloj del feed antiguo {feed}, no registrado"
        return {"clock": OLD_FEED_CLOCK[feed], "commission": use}, ""
    return {"clock": feeds.timezone(feed), "commission": use}, ""


def write(version: Path, fields: dict) -> None:
    """Add the fields to a sealed manifest (folder 0555, file 0444) and seal it again."""
    path = version / "manifest.json"
    doc = {**json.loads(path.read_text(encoding="utf-8")), **fields}
    os.chmod(version, 0o755)
    os.chmod(path, 0o644)
    path.write_text(json.dumps(doc, indent=1, default=str), encoding="utf-8")
    os.chmod(path, 0o444)
    os.chmod(version, 0o555)


def main(argv: list[str] | None = None) -> None:
    """Print the table of what is fillable; write it with `--yes`."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yes", action="store_true", help="escribe; sin esto solo muestra la tabla")
    args = parser.parse_args(argv)
    count = Counter()
    for row in read.listing():
        version = paths.archive_dir() / row["identity"] / row["version"]
        fields, why = plan(version)
        symbol = json.loads((version / "manifest.json").read_text(encoding="utf-8"))["asset"]["symbol"]
        state = "ya" if why == "ya congelado" else "rellenable" if fields else "NO"
        count[(symbol, state)] += 1
        if state == "NO":
            print(f"NO  {row['identity'][:12]} {row['version']} {symbol}: {why}")
        elif fields and args.yes:
            write(version, fields)
    for (symbol, state), n in sorted(count.items()):
        print(f"{symbol:10} {state:11} {n}")


if __name__ == "__main__":
    main()
