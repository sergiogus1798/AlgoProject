"""Move every asset's oos2 to end on the last day of the previous month, once the data covers it."""

import argparse
import sys
from datetime import date, timedelta

from core.assetdata import policy
from core.assetwrite import set_segment_end


def month_end_before(today: date) -> date:
    """The last calendar day of the month before `today`'s."""
    return today.replace(day=1) - timedelta(days=1)


def last_weekday(day: date) -> date:
    """`day` itself, or the Friday before it when it falls on a weekend — the last bar a feed can have."""
    return day - timedelta(days=max(0, day.weekday() - 4))


def plan(segments: dict, end: date) -> tuple[list, list]:
    """Which assets move and which the data does not yet reach.

    Args:
        segments: `_policy.yaml`'s `segments:` block.
        end: The new last day of oos2.

    Returns:
        (to move, short of data), each a list of (asset, current end, data end). An asset whose
        oos2 is undecided (`to: null`) is neither: its window is the owner's to set. One already
        at or past `end` is left alone — the roll never moves a window backwards.
    """
    move, short = [], []
    for symbol, seg in segments.items():
        to = seg["oos2"]["to"]
        # A bare year means its whole year (`assets/RULES.md`), so it ends on 31 December.
        if to is None or (date(to, 12, 31) if isinstance(to, int) else to) >= end:
            continue
        data_to = seg["data"]["to"] if seg["data"] else None
        row = (symbol, to, data_to)
        (move if data_to and data_to >= last_weekday(end) else short).append(row)
    return move, short


def main() -> None:
    """Print the plan; with --apply, write it into `_policy.yaml`."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="write it; otherwise a dry run")
    a = ap.parse_args()

    end = month_end_before(date.today())
    move, short = plan(policy()["segments"], end)
    print(f"oos2 → hasta {end} (último día del mes anterior)")
    for symbol, to, data_to in move:
        print(f"  {symbol}: {to} → {end}   (datos hasta {data_to})")
        if a.apply:
            set_segment_end(symbol, "oos2", end)
    for symbol, to, data_to in short:
        print(f"  ⚠️ {symbol}: se queda en {to} — los datos llegan a {data_to}, "
              f"hace falta al menos {last_weekday(end)}")
    if not move and not short:
        print("  nada que mover: todos los oos2 decididos ya llegan ahí")
    if move and not a.apply:
        print("ENSAYO. Añade --apply para escribirlo.")
    sys.exit(1 if short else 0)


if __name__ == "__main__":
    main()
