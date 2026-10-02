"""The questions the board asks of the memory: untouched cells, what survived, what was spent."""

from collections import Counter
from itertools import product

from studies.research.memory import sources
from studies.research.memory.sources import CONFIG

CONCLUSIVE = ("survivors", "died")   # outcome prefixes that answer; failed/incomplete/unknown do not


def cell(row: dict) -> tuple:
    """(symbol, timeframe, direction, family) of an attempt or an idea; '' where unknown."""
    return (row["symbol"], row["timeframe"], row["direction"], row.get("family", ""))


def grid() -> list[tuple]:
    """Every cell of the director's board: assets × timeframes × directions × families."""
    return list(product(CONFIG["asset_class"], CONFIG["timeframes"], CONFIG["directions"],
                        CONFIG["families"]))


def untouched_cells(attempts: list[dict]) -> list[tuple]:
    """Cells of the grid where no template of that family was ever run on that asset, timeframe
    and direction. A failed or empty run still counts as touched: the cell was tried."""
    touched = {cell(a) for a in attempts}
    return [c for c in grid() if c not in touched]


def conclusive(row: dict, include_dev: bool) -> bool:
    """A closed attempt: it died at a stage or reached the end. A dev draw (step 8 kept a random
    sample of 5) is a test of the chain, not evidence about the family, unless asked for."""
    return row["outcome"].startswith(CONCLUSIVE) and (include_dev or not row["dev_cut"])


def survivors_by_family(attempts: list[dict], include_dev: bool = False) -> list[dict]:
    """Per family and asset class: how many attempts, how many closed, how many gave survivors.

    Args:
        attempts: `attempts.table()`.
        include_dev: Count dev-draw runs as closed.

    Returns:
        Rows `family, asset_class, attempts, closed, with_survivors, survivors`. The board turns
        `with_survivors` out of `closed` into a rate and its uncertainty (few closed: wide); a
        family never tried has no row, which is «unknown», not zero.
    """
    seen: dict = {}
    for a in attempts:
        if not (a["family"] and a["asset_class"]):
            continue
        r = seen.setdefault((a["family"], a["asset_class"]), Counter())
        r["attempts"] += 1
        if conclusive(a, include_dev):
            r["closed"] += 1
            r["with_survivors"] += a["outcome"] == "survivors"
            r["survivors"] += a["survivors"]
    return [{"family": f, "asset_class": c, **{k: r[k] for k in
             ("attempts", "closed", "with_survivors", "survivors")}}
            for (f, c), r in sorted(seen.items())]


def ideas_spent(ideas: list[dict]) -> list[dict]:
    """Ideas already proposed per cell (asset × timeframe × direction × family).

    Args:
        ideas: `ideas.index()`.

    Returns:
        Rows `symbol, timeframe, direction, family, ideas, chosen, hypotheses`. An idea that never
        became a template has no known family: it counts in the row with family '' of its
        asset, timeframe and direction (the board adds that row to every family's). `hypotheses`
        is what the ideaExpert measured, each file counted once.
    """
    family = {n: CONFIG["archetype_family"].get(t["archetype"], "")
              for n, t in sources.templates().items()}
    cells: dict = {}
    for i in ideas:
        c = cell(i | {"family": family.get(i["idea"], "")})
        r = cells.setdefault(c, {"ideas": 0, "chosen": 0, "files": {}})
        r["ideas"] += 1
        r["chosen"] += i["chosen"] == "yes"
        r["files"][i["file"]] = i["hypotheses_measured"] or 0
    return [dict(zip(("symbol", "timeframe", "direction", "family"), c), ideas=r["ideas"],
                 chosen=r["chosen"], hypotheses=sum(r["files"].values()))
            for c, r in sorted(cells.items())]
