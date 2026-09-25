"""The coverage matrix: what has been tried, where, and what came of it."""

from ui.daemon import library

# Named here rather than gathered from the data, because the question the matrix answers
# is "what have I got little of" — and an archetype nobody has authored yet has to show
# as an empty row. Gathering them from the rows would hide exactly the gaps.
ARCHETYPES = ("breakout", "meanReversion", "trendFollowing", "momentum", "volatility",
              "pattern", "session")
TIMEFRAMES = ("M5", "M15", "M30", "H1", "H4", "D1")
ROW_AXES = ("archetype", "symbol", "template")
RANK = {"promising": 3, "": 2, "weak": 1, "dead": 0}


def cell_verdict(runs: list[dict[str, str]]) -> str:
    """The one verdict that stands for a cell holding several runs.

    Args:
        runs: The runs that fell in this cell.

    Returns:
        The best verdict present, so a cell goes green the moment one run in it worked.
        A cell is an invitation to look, not a summary statistic: hiding a promising run
        behind two dead ones would make the matrix argue against opening it.
    """
    return max((r.get("verdict", "") for r in runs), key=lambda v: RANK.get(v, 2))


def matrix(row_axis: str = "archetype") -> dict[str, object]:
    """The grid of runs, one axis chosen by the reader and timeframes always across.

    Args:
        row_axis: `archetype`, `symbol` or `template` — which dimension runs down the side.

    Returns:
        `rows` in display order, `columns` the timeframes, and `cells` keyed
        "<row>|<timeframe>" holding the runs there, their verdict and the templates and
        symbols involved. Timeframes stay on the columns in all three views because they
        are the axis with a fixed, short and ordered vocabulary.
    """
    entries = library.catalogue()
    archetype_of = {t["name"]: t.get("archetype", "") for t in entries}

    cells: dict[str, list[dict[str, str]]] = {}
    seen_rows, seen_tfs = set(), set()
    for t in entries:
        for run in t["runs"]:
            key = {"archetype": archetype_of.get(t["name"], "") or "sin arquetipo",
                   "symbol": run["symbol"],
                   "template": t["name"]}[row_axis]
            tf = run["timeframe"]
            seen_rows.add(key)
            seen_tfs.add(tf)
            cells.setdefault(f"{key}|{tf}", []).append({**run, "template": t["name"],
                                                        "archetype": archetype_of.get(t["name"], "")})

    fixed = {"archetype": ARCHETYPES}.get(row_axis, ())
    rows = list(fixed) + sorted(seen_rows - set(fixed))
    columns = list(TIMEFRAMES) + sorted(seen_tfs - set(TIMEFRAMES))
    return {"row_axis": row_axis, "rows": rows, "columns": columns,
            "cells": {k: {"runs": v, "verdict": cell_verdict(v), "count": len(v),
                          "templates": sorted({r["template"] for r in v}),
                          "symbols": sorted({r["symbol"] for r in v})}
                      for k, v in cells.items()}}


def totals() -> dict[str, object]:
    """The headline counts the window shows above the matrix.

    Returns:
        How many templates, how many are build-confirmed, how many runs, how many markets
        and timeframes touched, and how many drafts are waiting to be authored.
    """
    entries = [t for t in library.catalogue() if not t["orphan"]]
    runs = [r for t in entries for r in t["runs"]]
    return {"templates": len(entries),
            "build_confirmed": sum(t.get("status") == "buildConfirmed" for t in entries),
            "runs": len(runs),
            "symbols": len({r["symbol"] for r in runs}),
            "timeframes": len({r["timeframe"] for r in runs}),
            "archetypes_used": len({t.get("archetype", "") for t in entries if t.get("archetype")}),
            "archetypes_total": len(ARCHETYPES),
            "drafts": len(library.drafts())}
