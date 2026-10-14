#!/usr/bin/env python3
"""The oos2 roll moves asset by asset: a stale feed stays behind alone and never holds the others."""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.data import roll_oos2

END = date(2026, 9, 30)  # a Wednesday: the data must reach it
SEGMENTS = {
    "FRESH": {"data": {"to": date(2026, 10, 1)}, "oos2": {"to": date(2026, 8, 31)}},
    "EXACT": {"data": {"to": date(2026, 9, 30)}, "oos2": {"to": date(2026, 8, 30)}},
    # the feed named after FTMO's symbol, as it stood on 2026-10-03: bars to 24 September
    "STALE": {"data": {"to": date(2026, 9, 24)}, "oos2": {"to": date(2026, 8, 31)}},
    "NOFEED": {"data": None, "oos2": {"to": date(2026, 8, 31)}},
    "DONE": {"data": {"to": date(2026, 9, 24)}, "oos2": {"to": date(2026, 9, 30)}},
    "UNDECIDED": {"data": {"to": date(2026, 10, 1)}, "oos2": {"to": None}},
    "YEAR": {"data": {"to": date(2026, 10, 1)}, "oos2": {"to": 2026}},
    "OLDYEAR": {"data": {"to": date(2026, 10, 1)}, "oos2": {"to": 2025}},
}


def main() -> None:
    """Known answers for plan(), month_end_before() and last_weekday(), on fakes only."""
    failures = []
    move, short = roll_oos2.plan(SEGMENTS, END)
    if [row[0] for row in move] != ["FRESH", "EXACT", "OLDYEAR"]:
        failures.append(
            f"se mueven {[row[0] for row in move]}, no FRESH, EXACT y OLDYEAR"
        )
    if [row[0] for row in short] != ["STALE", "NOFEED"]:
        failures.append(f"se quedan {[row[0] for row in short]}, no STALE y NOFEED")

    # The catch-up of a later Saturday: the same end, and only what stayed behind is left.
    later = {
        "FRESH": {"data": {"to": date(2026, 10, 9)}, "oos2": {"to": END}},
        "STALE": {"data": {"to": date(2026, 10, 9)}, "oos2": {"to": date(2026, 8, 31)}},
    }
    move, short = roll_oos2.plan(later, roll_oos2.month_end_before(date(2026, 10, 10)))
    if [row[0] for row in move] != ["STALE"] or short:
        failures.append("el segundo sábado no recoge sólo al activo que se quedó atrás")

    for today, wanted in (
        (date(2026, 10, 3), END),
        (date(2026, 10, 31), END),
        (date(2026, 1, 3), date(2025, 12, 31)),
    ):
        if roll_oos2.month_end_before(today) != wanted:
            failures.append(f"month_end_before({today}) no es {wanted}")
    # 31 May 2026 is a Sunday: the last bar a feed can hold is Friday the 29th.
    for day, wanted in ((date(2026, 5, 31), date(2026, 5, 29)), (END, END)):
        if roll_oos2.last_weekday(day) != wanted:
            failures.append(f"last_weekday({day}) no es {wanted}")
    weekend = {
        "A": {"data": {"to": date(2026, 5, 29)}, "oos2": {"to": date(2026, 4, 30)}}
    }
    if not roll_oos2.plan(weekend, date(2026, 5, 31))[0]:
        failures.append(
            "un fin de mes en domingo exige una barra que ningún feed tiene"
        )

    print(
        "\n".join(failures)
        or "ok: el roll mueve activo a activo; el feed atrasado se queda "
        "solo y el sábado siguiente lo recoge"
    )
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
