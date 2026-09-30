"""A population result read for one strategy: only its rows, bars and grid line, said to be a view."""

import copy

# The columns a population table names its strategy in, as the studies write them.
KEYS = ("strategy", "mother", "name", "estrategia", "Strategy Name")


def mine(value: object, strategy: str) -> bool:
    """Whether one cell names this strategy, or a sibling scaled from it (crossTF)."""
    text = str(value or "")
    return text == strategy or text.startswith(f"{strategy}_Scaled")


def block(b: dict, strategy: str) -> dict | None:
    """One block kept to this strategy's share, or None when it holds none of it.

    Args:
        b: A contract block.
        strategy: The strategy's name.

    Returns:
        A table with only the rows whose strategy column names it; bars with only its items;
        a grid with only its row; a verdict or a note as it was. None for any other block,
        or one of these with nothing about this strategy.
    """
    kind = b.get("kind")
    if kind == "table":
        at = [i for i, c in enumerate(b.get("columns") or []) if c in KEYS]
        rows = [r for r in b.get("rows") or [] if any(mine(r[i], strategy) for i in at)]
        return {**b, "rows": rows} if rows else None
    if kind == "bars":
        items = [i for i in b.get("items") or [] if mine(str(i.get("label", "")).split(" · ")[0],
                                                          strategy)]
        return {**b, "items": items} if items else None
    if kind == "grid":
        keep = [i for i, r in enumerate(b.get("rows") or []) if mine(r, strategy)]
        if not keep:
            return None
        return {**b, "rows": [b["rows"][i] for i in keep],
                "values": [b["values"][i] for i in keep],
                **({"labels": [b["labels"][i] for i in keep]} if b.get("labels") else {})}
    return None


def slice_for(result: dict, strategy: str) -> dict | None:
    """A population result as this strategy's page shows it (feedback 2026-09-29 §4.5).

    Args:
        result: The study's population contract result.
        strategy: The strategy's name.

    Returns:
        A copy with every tab kept to the blocks that speak of this strategy and a note on
        each saying it is the population run, filtered; None when no block names it — a
        study that judged the population without a row per strategy.
    """
    out = copy.deepcopy(result)
    tabs = []
    for tab in out.get("tabs", []):
        kept = [k for k in (block(b, strategy) for b in tab.get("blocks", [])) if k]
        if kept:
            tabs.append({**tab, "blocks": kept, "note": "Corrida de toda la población, vista "
                         "solo para esta estrategia. " + (tab.get("note") or "")})
    if not tabs:
        return None
    return {**out, "tabs": tabs, "strategy": strategy, "sliced": True}


def verdict_row(result: dict, row: dict, strategy: str) -> dict:
    """A population result whose blocks never name the strategy, read off its verdict.csv row.

    Args:
        result: The study's population contract result.
        row: This strategy's verdict.csv row, every column as text.
        strategy: The strategy's name.

    Returns:
        One tab holding that row as a table, with the population's own verdict beside it —
        what the study said about this strategy, when its page drew only aggregates (decay).
    """
    keys = [k for k in row if k != "identity"]
    table = {"kind": "table", "title": "Lo que el estudio dijo de esta estrategia",
             "columns": keys, "rows": [[row[k] for k in keys]], "align": ["left"] * len(keys)}
    return {**copy.deepcopy(result), "strategy": strategy, "sliced": True,
            "tabs": [{"name": "row", "title": "Esta estrategia", "blocks": [table],
                      "note": "Su fila del verdict.csv de la corrida de toda la población."}]}


def whole(result: dict, strategy: str) -> dict:
    """A population result that says nothing per strategy (Filtros candidatos, exceso sobre el
    mono), shown as it is on a strategy's page — the same for every strategy, and said so."""
    out = copy.deepcopy(result)
    for tab in out.get("tabs", []):
        tab["note"] = ("Este estudio lee la población entera: su resultado es el mismo para "
                       "todas las estrategias del databank. " + (tab.get("note") or ""))
    return {**out, "strategy": strategy, "sliced": True}
