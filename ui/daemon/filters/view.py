"""What the strip and the funnel read of one databank's discards: counts, steps, conditions."""

import re

from ui.daemon.filters import discards, evaluate

PART = re.compile(r"^(.*?) (>|<|≥|≤|=|entre|dentro|fuera) ?(.*)$")
CODE = {shown: code for code, shown in evaluate.SHOWN.items()}


def worded(step: dict) -> str:
    """A step's expression for the funnel, each metric in the window's words (a step logged
    before the expression was worded still carries raw keys), and its «sin valor» and
    «sin identidad» counts."""
    parts = [PART.match(p) for p in step["expression"].split(" AND ")]
    text = step["expression"] if step["origin"] == "manual" else " AND ".join(
        f"{evaluate.named(m.group(1))} {m.group(2)} {m.group(3)}" for m in parts)
    return (text + (f" · {step['blank']} sin valor" if step["blank"] else "")
            + (f" · {step['anonymous']} sin identidad, no filtrables" if step["anonymous"]
               else ""))


def recovered(expression: str, metrics: list[dict]) -> list[dict]:
    """A filter of the old stacking log read back into rows from its expression, so the strip
    can show them again; [] when a part names no metric offered today.

    Args:
        expression: As `evaluate.expression` wrote it (or, older, with raw keys).
        metrics: What `evaluate.offered` gave.
    """
    by_words = {w: m["key"] for m in metrics for w in (m["key"], m["label"])}
    rows = []
    for part in expression.split(" AND "):
        m = PART.match(part)
        if m is None or m.group(1) not in by_words:
            return []
        op, value = CODE[m.group(2)], m.group(3)
        if op == "entre":
            value = value.split(" y ")
        elif op in ("dentro", "fuera"):
            value = value.removeprefix("del intervalo ").removesuffix(" %")
        rows.append({"metric": by_words[m.group(1)], "op": op, "value": value})
    return evaluate.normal(rows)


def state_of(project: str, databank: str, table: dict, metrics: list[dict]) -> dict:
    """One databank's discards now: hidden identities, each step's counts, the conditions in
    force (`conditions`), for a log from before re-filtering the old filter (`stale`), and
    the discard lines a truncated log left without a header (`orphans`, never hidden).

    Args:
        project: Project name.
        databank: Either spelling.
        table: What `/api/databank/table` answered, read once by the caller.
        metrics: What `evaluate.offered` gave, to read back a stale filter.
    """
    total = sum(r["identity"] is not None for r in table["rows"])
    steps = discards.steps(project, databank, total)
    hidden = discards.hidden(project, databank)
    old = discards.stale(project, databank)
    return {"databank": databank, "hidden": len(hidden), "hidden_ids": sorted(hidden),
            "entered": steps[0]["entered"] if steps else None,
            "remaining": steps[-1]["passed"] if steps else None,
            "anonymous": steps[-1]["anonymous"] if steps else None, "steps": steps,
            "manual": len(discards.manual_ids(project, databank)),
            "conditions": (recovered(old, metrics) if old
                           else discards.rows_now(project, databank)),
            "stale": old, "orphans": discards.orphans(project, databank)}


def funnel_rows(project: str, banks: list[str]) -> list[dict]:
    """The funnel's rows (screen, entered, passed, died, why), one per filter or deletion."""
    return [{"screen": f"Filtro · {bank}" if s["origin"] == "filter" else f"A mano · {bank}",
             "entered": s["entered"], "passed": s["passed"], "died": s["died"],
             "why": worded(s), "kind": "hard"}
            for bank in banks for s in discards.steps(project, bank)]
