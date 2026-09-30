"""The discard log of one databank: what the filter in force and the manual deletions set aside."""

import json
from datetime import datetime, timezone
from pathlib import Path

from core.paths import DATA


def root() -> Path:
    """`AlgoData/filters/`, the one root of every filter file. Derived here and not in
    `core/paths.py`, which cannot take another function under the 250-line limit."""
    return DATA / "filters"


def folder(project: str, databank: str) -> Path:
    """Where one databank's filters live: `<root>/<P>/<D>/`, the databank as its report
    folder spells it (underscores)."""
    return root() / project / databank.replace(" ", "_")


def log_file(project: str, databank: str) -> Path:
    """The databank's `discards.jsonl`, whether or not it exists yet."""
    return folder(project, databank) / "discards.jsonl"


def events(project: str, databank: str) -> list[dict]:
    """Every line of the log, oldest first; none when nothing was ever filtered."""
    path = log_file(project, databank)
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def since_clear(project: str, databank: str) -> list[dict]:
    """Every line after the last «quitar filtros» (or cut): applied headers and discards."""
    lines = events(project, databank)
    cut = max((i for i, e in enumerate(lines) if e.get("clear")), default=-1)
    return lines[cut + 1:]


def groups(project: str, databank: str) -> list[tuple[dict, list[dict]]]:
    """The live log as (applied header, its discard lines), oldest first. Discard lines with
    no header before them (a truncated log) belong to nothing and are skipped (`orphans`)."""
    out: list[tuple[dict, list[dict]]] = []
    for e in since_clear(project, databank):
        if e.get("applied"):
            out.append((e, []))
        elif "identity" in e and out:
            out[-1][1].append(e)
    return out


def orphans(project: str, databank: str) -> int:
    """Discard lines since the last clear that no `applied` header precedes: never hidden."""
    lines = since_clear(project, databank)
    first = next((i for i, e in enumerate(lines) if e.get("applied")), len(lines))
    return sum("identity" in e for e in lines[:first])


def current(project: str, databank: str) -> tuple[list[tuple[dict, list[dict]]],
                                                  list[tuple[dict, list[dict]]]]:
    """The filter in force and the manual deletions, apart.

    The latest filter decides: it was judged on the whole databank, so loosening it brings
    strategies back. A latest filter logged before 2026-09-28 (its header has no `rows`
    key) was judged on what earlier filters had left and cannot be replayed alone: no
    filter is in force until the next «Aplicar» (`stale` names it). Manual deletions always
    stack, whatever filter replaces whatever.

    Returns:
        ([the filter in force] or [], manual groups oldest first).
    """
    every = groups(project, databank)
    filters = [g for g in every if g[0]["origin"] == "filter"]
    return ([filters[-1]] if filters and "rows" in filters[-1][0] else [],
            [g for g in every if g[0]["origin"] == "manual"])


def stale(project: str, databank: str) -> str | None:
    """The expression of a latest filter from the old stacking log, or None."""
    filters = [h for h, _ in groups(project, databank) if h["origin"] == "filter"]
    return filters[-1]["expression"] if filters and "rows" not in filters[-1] else None


def live(project: str, databank: str) -> list[dict]:
    """What the view hides now, and so what «Continuar workflow» cuts: the lines of the
    filters in force, then the manual deletions they did not already hide.

    Returns:
        One dict per identity set aside: `identity`, `name`, `origin` (filter | manual),
        `expression`, `ts`, `n_in` (how many the filter or deletion was judged on).
    """
    filters, manual = current(project, databank)
    out: dict[str, dict] = {}
    for _, lines in filters + manual:
        for line in lines:
            out.setdefault(line["identity"], line)
    return list(out.values())


def hidden(project: str, databank: str) -> set[str]:
    """The identities set aside now."""
    return {e["identity"] for e in live(project, databank)}


def manual_ids(project: str, databank: str) -> set[str]:
    """The identities deleted by hand since the last clear: they survive every re-filter."""
    return {line["identity"] for _, lines in current(project, databank)[1] for line in lines}


def rows_now(project: str, databank: str) -> list[dict]:
    """The conditions of the filter in force, as the strip shows them; none without one."""
    filters = current(project, databank)[0]
    return (filters[0][0]["rows"] or []) if filters else []


def unchanged(project: str, databank: str, rows: list[dict], n_in: int,
              dropped: set[str]) -> bool:
    """Whether applying would change nothing: the same conditions in force AND the same
    judgement over the table now. A strategy SQX wrote or deleted since makes it differ, so
    a re-apply picks the change up (and drops identities the table no longer holds)."""
    filters = current(project, databank)[0]
    if not filters:
        return not rows and not stale(project, databank)
    head, lines = filters[0]
    return ((head["rows"] or []) == rows and head["n_in"] == n_in
            and {line["identity"] for line in lines} == dropped)


def stamp() -> str:
    """Now, in UTC, to the second."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def append(project: str, databank: str, lines: list[dict]) -> None:
    """Add lines to the log, in append mode: nothing here rewrites a line.

    Args:
        project: Project name.
        databank: Either spelling.
        lines: One dict per line.
    """
    path = log_file(project, databank)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for line in lines:
            handle.write(json.dumps(line, ensure_ascii=False) + "\n")


def record(project: str, databank: str, dropped: dict[str, str], origin: str,
           expression: str, n_in: int, blank: int = 0, anonymous: int = 0,
           rows: list[dict] | None = None, total: int | None = None) -> None:
    """Write one filter's or one manual deletion's discards, after one `applied` line that
    keeps its counts (a filter that set nobody aside is still a step of the funnel).

    Args:
        project: Project name.
        databank: Either spelling.
        dropped: identity → strategy name.
        origin: `filter` or `manual`.
        expression: What was applied, as the ledger's `criterion` says it.
        n_in: How many were visible before.
        blank: How many stayed for lacking a value (a filter's «sin valor»).
        anonymous: Rows of the table without identity, which no filter can hide.
        rows: A filter's conditions, when it was judged on the whole databank: the header
            then replaces every earlier filter (`current`); [] records «sin filtro», and
            None (a caller that has none to give) still replaces.
        total: The databank's identified rows (what a deletion counts from when no filter is
            in force); a filter's is its n_in.
    """
    ts = stamp()
    head = {"applied": True, "origin": origin, "expression": expression, "ts": ts,
            "n_in": n_in, "n_out": n_in - len(dropped), "blank": blank,
            "anonymous": anonymous, "rows": rows, "total": n_in if total is None else total}
    append(project, databank, [head] + [{"identity": i, "name": n, "origin": origin,
                                "expression": expression, "ts": ts, "n_in": n_in}
                               for i, n in sorted(dropped.items(), key=lambda kv: kv[1])])


def clear(project: str, databank: str) -> int:
    """«Quitar filtros»: a `clear` line; the lines before it stay as history.

    Returns:
        How many identities it brought back.
    """
    back = len(hidden(project, databank))
    append(project, databank, [{"clear": True, "ts": stamp()}])
    return back


def steps(project: str, databank: str, total: int | None = None) -> list[dict]:
    """The live log as the funnel counts it: the filter in force, then each manual
    deletion counted against what they left (a deletion of a strategy the filter now hides
    kills nothing). A filter with no conditions is no step.

    Args:
        project: Project name.
        databank: Either spelling.
        total: The databank's identified rows now, what the first deletion entered from when
            no filter is in force; None falls back on the count its header recorded.

    Returns:
        `expression`, `origin`, `ts`, `entered`, `died`, `passed`, `blank`, `anonymous`.
    """
    filters, manual = current(project, databank)
    out, gone = [], set()
    for head, lines in filters:
        gone |= {line["identity"] for line in lines}
        if head.get("rows") != []:
            out.append({"expression": head["expression"], "origin": "filter", "ts": head["ts"],
                        "entered": head["n_in"], "passed": head["n_out"],
                        "died": head["n_in"] - head["n_out"], "blank": head.get("blank", 0),
                        "anonymous": head.get("anonymous", 0)})
    for head, lines in manual:
        ids = {line["identity"] for line in lines} - gone
        gone |= ids
        entered = (out[-1]["passed"] if out else total if total is not None
                   else head.get("total", head["n_in"]))
        out.append({"expression": head["expression"], "origin": "manual", "ts": head["ts"],
                    "entered": entered, "passed": entered - len(ids), "died": len(ids),
                    "blank": 0, "anonymous": head.get("anonymous", 0)})
    return out


def databanks(project: str) -> list[str]:
    """The databank folders of a project that have a discard log."""
    top = root() / project
    return sorted(p.parent.name for p in top.glob("*/discards.jsonl")) if top.is_dir() else []
